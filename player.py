from ursina import *
from gun import Gun
from config import PLAYER_SCALE, PLAYER_SPEED, PLAYER_JUMP_HEIGHT
import search_destroy
import math

class Player(Entity):
    def __init__(self, team_color=color.white, spawn_point=(0, 1, 0), is_local=False, name="Player", team_manager=None, **kwargs):
        super().__init__(
            model='soldier.obj',
            double_sided=True,
            scale=PLAYER_SCALE if PLAYER_SCALE != Vec3(0,0,0) else Vec3(1,1,1),
            color=team_color,
            position=spawn_point,
            **kwargs
        )

        self.enabled = True
        self.visible = True

        self.spawn_point = Vec3(spawn_point[0], 1, spawn_point[2])  # ensure above ground
        self.team_color = team_color
        self.name_text = Text(
            text=name,
            position=(0, 2.5, 0),
            scale=2,
            color=color.white,
            parent=self,
            origin=(0, 0),
            world=True
        )

        self.health = 100
        self.health_bar = Entity(
            model='quad',
            color=color.green,
            scale=(1, 0.1),
            position=(0, 2.2, 0),
            parent=self,
            always_on_top=True
        )
        self.collider = BoxCollider(self, center=Vec3(0, 1, 0), size=Vec3(1, 2, 1))
        # Separate hitbox entity for more reliable bullet collisions
        self.hitbox = Entity(
            parent=self,
            model='cube',
            scale=Vec3(1, 2, 1),
            position=Vec3(0, 1, 0),
            collider='box',
            visible=False
        )

        self.speed = PLAYER_SPEED
        self.jump_height = PLAYER_JUMP_HEIGHT  # unused now, no gravity
        self.kills = 0
        self.dead = False
        self.team_manager = team_manager
        self.is_local = is_local
        self.has_bomb = False

        self.gun = Gun(player=self)

        if self.is_local:
            camera.parent = self
            camera.position = (0, 2, 1)  # zoomed out a bit more
            camera.rotation = (10, 0, 0)
            self.camera_pitch = camera.rotation_x
            mouse.locked = True
            # add small yellow dot crosshair at the center of the screen
            self.crosshair = Entity(
                parent=camera.ui,
                model='quad',
                texture='circle',
                color=color.yellow,
                scale=0.02,
                position=Vec2(0, 0),
                enabled=True
            )

    def update(self):
        if self.dead:
            return

        if self.is_local:
            self._handle_input()
        else:
            self._update_ai()

    def _handle_input(self):
        move = Vec3(
            held_keys['d'] - held_keys['a'],
            0,
            held_keys['w'] - held_keys['s']
        ).normalized()

        self.rotation_y += mouse.velocity[0] * 100
        self.camera_pitch -= mouse.velocity[1] * 100
        self.camera_pitch = max(min(self.camera_pitch, 60), -60)
        camera.rotation_x = self.camera_pitch

        move = self.forward * move.z + self.right * move.x
        self.position += move * self.speed * time.dt

        if held_keys['space']:
            self.jump()

        self.gun.aim_target = mouse.world_point if mouse.world_point else self.forward
        if mouse.left:
            self.gun.shoot()
        self.gun.update()

        if held_keys['4'] and search_destroy.sd_game:
            search_destroy.sd_game.handle_action(self)

    def jump(self):
        pass  # Gravity is disabled

    def _update_ai(self):
        enemies = [p for p in self.team_manager.get_opposing_players(self.team_color) if not p.dead]
        if not enemies:
            self.gun.update()
            return

        nearest = min(enemies, key=lambda p: distance(p.position, self.position))

        # Vector toward the nearest enemy on the XZ plane
        direction = nearest.position - self.position
        direction.y = 0
        dist = direction.length()

        if dist > 0:
            self.rotation_y = math.degrees(math.atan2(direction.x, direction.z))

        # Move toward the enemy if far enough away
        if dist > 3:
            self.position += direction.normalized() * self.speed * time.dt

        # Shoot when within range
        if dist < 20:
            self.gun.aim_target = nearest.position
            if not self.gun.bullet:
                self.gun.shoot()

        self.gun.update()

    def take_damage(self, amount, attacker=None):
        if self.dead:
            return

        self.health -= amount
        self.health_bar.scale_x = self.health / 100

        if self.health <= 0:
            if attacker:
                attacker.kills += 1
            self.die()

    def die(self):
        if self.dead:
            return
        self.dead = True
        self.health_bar.enabled = False
        self.visible = False
        self.collider = None
        self.hitbox.enabled = False
        if self.has_bomb and search_destroy.sd_game:
            search_destroy.sd_game.drop_bomb(self.position)
            self.has_bomb = False
        if search_destroy.sd_game:
            search_destroy.sd_game.on_player_death(self)
        else:
            invoke(self.respawn, delay=3)

    def respawn(self):
        self.position = Vec3(self.spawn_point[0], 1, self.spawn_point[2])
        self.health = 100
        self.dead = False
        self.visible = True
        self.health_bar.enabled = True
        self.collider = BoxCollider(self, center=Vec3(0, 1, 0), size=Vec3(1, 2, 1))
        self.hitbox.enabled = True
        self.health_bar.scale_x = 1
        self.has_bomb = False
