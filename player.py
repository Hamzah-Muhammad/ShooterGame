from ursina import *
import random
import time
from math import atan2, pi

bullet_speed = 30
bullet_lifetime = 1.5
respawn_delay = 3

class Player(Entity):
    def __init__(self, team_color=color.white, spawn_point=(0, 0, 0), is_local=False, **kwargs):
        super().__init__(
            model='cube',
            color=team_color,
            scale=(1, 2, 1),
            position=spawn_point,
            collider='box'
        )
        self.speed = 5
        self.is_local = is_local
        self.team_color = team_color
        self.spawn_point = spawn_point
        self.health = 100
        self.alive = True

        self.gun = None
        self.health_bar = None

        if self.is_local:
            # Camera setup
            self.camera_offset = Vec3(0, 5, -10)
            self.camera_pivot = Entity(parent=self, y=1.5)

            # Crosshair
            self.crosshair = Entity(
                parent=camera.ui,
                model='quad',
                color=color.white,
                scale=0.01,
                position=(0, 0)
            )

            # Placeholder AK-47-style gun
            self.gun = Entity(
                model='cube',
                scale=(0.1, 0.1, 1),
                color=color.black,
                parent=self.camera_pivot,
                position=(0.3, -0.3, 1),
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
                self.shoot()

            if self.health_bar:
                self.health_bar.scale_x = max(0.001, self.health / 100)

    def move(self):
        move_dir = Vec3(
            held_keys['d'] - held_keys['a'],
            0,
            held_keys['w'] - held_keys['s']
        ).normalized() * time.dt * self.speed

        self.position += self.forward * move_dir.z + self.right * move_dir.x

        if move_dir.length() > 0:
            angle = atan2(move_dir.x, move_dir.z) * (180 / pi)
            self.rotation_y = lerp(self.rotation_y, angle, 6 * time.dt)

    def shoot(self):
        if not hasattr(self, '_shoot_cooldown') or time.time() - self._shoot_cooldown > 0.1:
            self._shoot_cooldown = time.time()

            ray = raycast(camera.world_position, camera.forward, distance=100, ignore=[self])
            if ray.hit and hasattr(ray.entity, 'hit'):
                ray.entity.hit(self)

            bullet = Entity(
                model='sphere',
                color=color.yellow,
                scale=0.1,
                position=self.position + self.forward * 1.5,
                collider=None
            )
            bullet.animate_position(
                bullet.position + camera.forward * bullet_speed,
                duration=bullet_lifetime,
                curve=curve.linear
            )
            destroy(bullet, delay=bullet_lifetime)

    def hit(self, attacker):
        self.health -= 25
        if self.health <= 0:
            self.die()

    def die(self):
        self.alive = False
        self.visible = False
        if self.health_bar:
            self.health_bar.visible = False
        invoke(self.respawn, delay=respawn_delay)

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
