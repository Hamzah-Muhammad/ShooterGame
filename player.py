from ursina import *
from gun import Gun
from config import (
    PLAYER_SCALE, PLAYER_SPEED, SPRINT_SPEED, CROUCH_SPEED,
    PLAYER_JUMP_HEIGHT, GRAVITY,
    BOMB_PLANT_RADIUS, BOMB_DEFUSE_RADIUS, AMMO_CAPACITY,
)
import search_destroy
from killfeed import kill_feed
import math
import random


class Player(Entity):
    def __init__(self, team_color=color.white, spawn_point=(0, 1, 0), is_local=False, name="Player", team_manager=None, **kwargs):
        super().__init__(
            model='soldier.obj',
            double_sided=True,
            scale=PLAYER_SCALE if PLAYER_SCALE != Vec3(0, 0, 0) else Vec3(1, 1, 1),
            color=team_color,
            position=spawn_point,
            **kwargs
        )

        self.enabled = True
        self.visible = True

        self.spawn_point = Vec3(spawn_point[0], 1, spawn_point[2])
        self.player_name = name
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
        # Body hitbox — torso + legs
        self.body_hitbox = Entity(
            parent=self,
            model='cube',
            scale=Vec3(1, 1.6, 1),
            position=Vec3(0, 0.8, 0),
            collider='box',
            visible=False,
        )
        self.body_hitbox.owner = self
        self.body_hitbox.is_head = False
        # Head hitbox — smaller, on top
        self.head_hitbox = Entity(
            parent=self,
            model='cube',
            scale=Vec3(0.55, 0.4, 0.55),
            position=Vec3(0, 1.8, 0),
            collider='box',
            visible=False,
        )
        self.head_hitbox.owner = self
        self.head_hitbox.is_head = True
        # Back-compat alias for any external refs
        self.hitbox = self.body_hitbox

        self.speed = PLAYER_SPEED
        self.jump_height = PLAYER_JUMP_HEIGHT
        self.kills = 0
        self.dead = False
        self.team_manager = team_manager
        self.is_local = is_local
        self.has_bomb = False
        self.is_moving = False
        self.is_crouching = False

        # Gravity state
        self.velocity_y = 0
        self.on_ground = True

        # AI state
        self._avoid_dir = Vec3(1, 0, 0)
        self._strafe_timer = 0
        self._evasion_timer = 0.0
        self._evasion_dir = Vec3(1, 0, 0)
        self._last_health = 100

        self.gun = Gun(player=self)

        if self.is_local:
            camera.parent = self
            camera.position = (0, 2, 1)
            camera.rotation = (10, 0, 0)
            self.camera_pitch = camera.rotation_x
            mouse.locked = True
            self.crosshair = Entity(
                parent=camera.ui,
                model='quad',
                texture='circle',
                color=color.yellow,
                scale=0.02,
                position=Vec2(0, 0),
                enabled=True
            )
            self.bomb_indicator = Text(
                text='',
                parent=camera.ui,
                position=window.bottom_left + Vec2(0.05, 0.1),
                origin=(0, 0),
                scale=1.5,
                color=color.white
            )
            self.ammo_text = Text(
                text=f'{AMMO_CAPACITY} / {AMMO_CAPACITY}',
                parent=camera.ui,
                position=window.bottom_right + Vec2(-0.05, 0.1),
                origin=(1, 0),
                scale=1.5,
                color=color.white,
            )
            self.health_text = Text(
                text='100',
                parent=camera.ui,
                position=window.bottom_left + Vec2(0.05, 0.17),
                origin=(0, 0),
                scale=2,
                color=color.white,
            )
        else:
            self.bomb_indicator = None
            self.ammo_text = None
            self.health_text = None

    def update(self):
        if self.dead:
            return

        self._apply_gravity()
        self._update_hitbox_pose()

        if search_destroy.sd_game and (
            search_destroy.sd_game.countdown_active or search_destroy.sd_game.round_over_active
        ):
            return

        if self.is_local:
            self._handle_input()
            if self.bomb_indicator:
                self.bomb_indicator.text = 'You have the bomb  [4] to plant' if self.has_bomb else ''
            if self.ammo_text:
                if self.gun.reloading:
                    self.ammo_text.text = 'RELOADING...'
                    self.ammo_text.color = color.orange
                else:
                    self.ammo_text.text = f'{self.gun.ammo} / {AMMO_CAPACITY}'
                    self.ammo_text.color = color.white if self.gun.ammo > 3 else color.red
            if self.health_text:
                hp = max(0, int(self.health))
                self.health_text.text = str(hp)
                if hp > 50:
                    self.health_text.color = color.white
                elif hp > 25:
                    self.health_text.color = color.orange
                else:
                    self.health_text.color = color.red
        else:
            self._update_ai()

    def _update_hitbox_pose(self):
        """Shrink hitboxes when crouching so crouch is mechanically real, not just visual."""
        if self.is_crouching:
            self.body_hitbox.scale = Vec3(1, 1.0, 1)
            self.body_hitbox.position = Vec3(0, 0.5, 0)
            self.head_hitbox.scale = Vec3(0.55, 0.35, 0.55)
            self.head_hitbox.position = Vec3(0, 1.2, 0)
        else:
            self.body_hitbox.scale = Vec3(1, 1.6, 1)
            self.body_hitbox.position = Vec3(0, 0.8, 0)
            self.head_hitbox.scale = Vec3(0.55, 0.4, 0.55)
            self.head_hitbox.position = Vec3(0, 1.8, 0)

    def _apply_gravity(self):
        if not self.on_ground:
            self.velocity_y += GRAVITY * time.dt
        self.y += self.velocity_y * time.dt
        if self.y <= 1:
            self.y = 1
            self.velocity_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

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

        # Crouch (ctrl)
        if held_keys['control']:
            self.is_crouching = True
            camera.y = 1.0
        else:
            self.is_crouching = False
            camera.y = 2.0

        if self.is_crouching:
            move_speed = CROUCH_SPEED
        elif held_keys['shift'] and move.length() > 0:
            move_speed = SPRINT_SPEED
        else:
            move_speed = PLAYER_SPEED

        self.is_moving = move.length() > 0.01

        move = self.forward * move.z + self.right * move.x
        self.position += move * move_speed * time.dt

        if held_keys['space']:
            self.jump()

        if held_keys['r']:
            self.gun.reload()

        if mouse.left:
            self.gun.shoot()
        self.gun.update()

        if held_keys['4'] and search_destroy.sd_game:
            search_destroy.sd_game.handle_action(self)

    def jump(self):
        if self.on_ground:
            self.velocity_y = self.jump_height
            self.on_ground = False

    def _update_ai(self):
        # Detect being hit — start evasion
        if self.health < self._last_health and self.health > 0:
            self._evasion_timer = random.uniform(0.4, 1.0)
            self._evasion_dir = self.right if random.random() > 0.5 else -self.right
        self._last_health = self.health

        if self._evasion_timer > 0 and self._strafe_timer <= 0:
            self._evasion_timer -= time.dt
            self.position += self._evasion_dir * self.speed * time.dt
            self.is_moving = True

        if search_destroy.sd_game:
            sd = search_destroy.sd_game
            is_attacker = self.team_color == sd.attacking_team.color

            if self.has_bomb and sd.plant_sites:
                nearest_site = min(sd.plant_sites, key=lambda s: distance(self.position, s.position))
                self._ai_move_toward(nearest_site.position)
                if distance(self.position, nearest_site.position) < BOMB_PLANT_RADIUS:
                    sd.handle_action(self)
                self._ai_engage_nearby(range_limit=14)
                self.gun.update()
                return

            if not is_attacker and sd.bomb_planted and sd.planted_bomb:
                self._ai_move_toward(sd.planted_bomb.position)
                if distance(self.position, sd.planted_bomb.position) < BOMB_DEFUSE_RADIUS:
                    sd.handle_action(self)
                self._ai_engage_nearby(range_limit=20)
                self.gun.update()
                return

        enemies = [p for p in self.team_manager.get_opposing_players(self.team_color) if not p.dead]
        if not enemies:
            self.is_moving = False
            self.gun.update()
            return

        nearest = min(enemies, key=lambda p: distance(p.position, self.position))
        direction = nearest.position - self.position
        direction.y = 0
        dist = direction.length()

        if dist > 0:
            self.rotation_y = math.degrees(math.atan2(direction.x, direction.z))

        if dist > 3:
            self.is_moving = True
            self._ai_move_toward(nearest.position)
        else:
            self.is_moving = False

        if dist < 20:
            self.gun.shoot()

        self.gun.update()

    def _ai_engage_nearby(self, range_limit=14):
        enemies = [p for p in self.team_manager.get_opposing_players(self.team_color) if not p.dead]
        if not enemies:
            return
        nearest = min(enemies, key=lambda p: distance(p.position, self.position))
        if distance(nearest.position, self.position) < range_limit:
            dx = nearest.position.x - self.position.x
            dz = nearest.position.z - self.position.z
            self.rotation_y = math.degrees(math.atan2(dx, dz))
            self.gun.shoot()

    def _ai_move_toward(self, target):
        direction = target - self.position
        direction.y = 0
        dist = direction.length()
        if dist < 0.5:
            self.is_moving = False
            return

        direction = direction.normalized()
        self.rotation_y = math.degrees(math.atan2(direction.x, direction.z))

        ray = raycast(
            self.world_position + Vec3(0, 1, 0),
            direction,
            distance=3,
            ignore=[self, self.body_hitbox, self.head_hitbox]
        )
        if ray.hit:
            if self._strafe_timer <= 0:
                perp = Vec3(-direction.z, 0, direction.x).normalized()
                self._avoid_dir = perp if random.random() > 0.5 else -perp
                self._strafe_timer = random.uniform(0.5, 1.5)
            self._strafe_timer -= time.dt
            self.position += self._avoid_dir * self.speed * time.dt
        else:
            self._strafe_timer = 0
            self.position += direction * self.speed * time.dt
        self.is_moving = True

    def _show_hit_marker(self, headshot=False):
        # Red for body, bright yellow for headshot
        c = color.rgba32(255, 230, 60, 240) if headshot else color.rgba32(255, 50, 50, 230)
        size, gap = (0.034, 0.014) if headshot else (0.025, 0.014)
        offsets = [
            (Vec2(gap + size / 2, 0), (size, 0.003)),
            (Vec2(-(gap + size / 2), 0), (size, 0.003)),
            (Vec2(0, gap + size / 2), (0.003, size)),
            (Vec2(0, -(gap + size / 2)), (0.003, size)),
        ]
        for pos, scl in offsets:
            line = Entity(parent=camera.ui, model='quad', color=c, scale=scl, position=pos)
            destroy(line, delay=0.15)

    def take_damage(self, amount, attacker=None, headshot=False):
        if self.dead:
            return

        self.health -= amount
        self.health_bar.scale_x = max(0, self.health / 100)

        if attacker and attacker.is_local:
            attacker._show_hit_marker(headshot=headshot)

        if self.health <= 0:
            if attacker:
                attacker.kills += 1
                kill_feed.add(attacker.player_name, self.player_name, headshot=headshot)
            self.die()

    def die(self):
        if self.dead:
            return
        self.dead = True
        self.health_bar.enabled = False
        self.visible = False
        self.collider = None
        self.body_hitbox.enabled = False
        self.head_hitbox.enabled = False
        if self.is_local and hasattr(self, 'crosshair'):
            self.crosshair.enabled = False
        if self.has_bomb and search_destroy.sd_game:
            search_destroy.sd_game.drop_bomb(self.position)
            self.has_bomb = False
        if self.bomb_indicator:
            self.bomb_indicator.text = ''
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
        self.body_hitbox.enabled = True
        self.head_hitbox.enabled = True
        self.health_bar.scale_x = 1
        if self.is_local and hasattr(self, 'crosshair'):
            self.crosshair.enabled = True
        self.has_bomb = False
        self.is_moving = False
        self.is_crouching = False
        self.velocity_y = 0
        self.on_ground = True
        self._last_health = 100
        self._evasion_timer = 0.0
        self.gun.reset()
        if self.bomb_indicator:
            self.bomb_indicator.text = ''
        if self.ammo_text:
            self.ammo_text.text = f'{AMMO_CAPACITY} / {AMMO_CAPACITY}'
            self.ammo_text.color = color.white
        if self.health_text:
            self.health_text.text = '100'
            self.health_text.color = color.white
