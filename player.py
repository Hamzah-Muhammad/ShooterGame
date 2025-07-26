from ursina import *
import random
import time
from math import atan2, pi
from gun import Gun
from constants import BULLET_SPEED, BULLET_LIFETIME, AMMO_CAPACITY, RELOAD_TIME

class Player(Entity):
    def __init__(self, team_color=color.white, spawn_point=(0, 0, 0), is_local=False, **kwargs):
        super().__init__(
            model='assets/soldier.obj',
            color=team_color,
            scale=1,
            position=spawn_point,
            collider='box',
            **kwargs
        )

        self.speed = 5
        self.is_local = is_local
        self.team_color = team_color
        self.spawn_point = spawn_point
        self.health = 100
        self.alive = True

        self.gun = None
        self.health_bar = None
        self.scoreboard = None

        if self.is_local:
            # Camera setup
            self.camera_offset = Vec3(0, 7, -20)
            self.camera_pivot = Entity(parent=self, y=2)

            # Crosshair
            self.crosshair = Entity(
                parent=camera.ui,
                model='quad',
                color=color.white,
                scale=0.01,
                position=(0, 0)
            )

            # Gun (✅ Fixed: pass player=self)
            self.gun = Gun(
                player=self,
                parent=self.camera_pivot,
                position=(0.4, -0.3, 1),
                rotation=(0, 0, 0)
            )

            # Health bar UI
            self.health_bar = Entity(
                parent=camera.ui,
                model='quad',
                color=color.red,
                scale=(0.3, 0.03),
                position=(-0.35, 0.45),
                origin=(-.5, 0)
            )

    def update(self):
        if not self.alive:
            return

        self.move()

        if self.is_local:
            camera.position = self.camera_pivot.world_position + self.camera_offset
            camera.look_at(self.camera_pivot.world_position)

            if mouse.left:
                self.gun.fire(from_pos=self.position + Vec3(0, 1.5, 0), direction=camera.forward)

            if self.health_bar:
                self.health_bar.scale_x = max(0.001, self.health / 100)

    def move(self):
        direction = Vec3(
            held_keys['d'] - held_keys['a'],
            0,
            held_keys['w'] - held_keys['s']
        ).normalized()

        self.position += (self.forward * direction.z + self.right * direction.x) * time.dt * self.speed

        if direction.length() > 0:
            angle = atan2(direction.x, direction.z) * (180 / pi)
            self.rotation_y = lerp(self.rotation_y, angle, 10 * time.dt)

    def hit(self, attacker):
        self.health -= 25
        if self.health <= 0:
            self.die()

    def die(self):
        self.alive = False
        self.visible = False
        if self.health_bar:
            self.health_bar.visible = False
        invoke(self.respawn, delay=3)

    def respawn(self):
        self.position = Vec3(
            self.spawn_point[0] + random.uniform(-3, 3),
            self.spawn_point[1],
            self.spawn_point[2] + random.uniform(-3, 3)
        )
        self.health = 100
        self.visible = True
        self.alive = True
        if self.health_bar:
            self.health_bar.visible = True