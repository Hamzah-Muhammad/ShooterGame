from ursina import *
from config import (
    BULLET_DAMAGE, HEADSHOT_MULTIPLIER, FIRE_RATE, AMMO_CAPACITY, RELOAD_TIME,
    BULLET_BASE_SPREAD, BULLET_MOVE_SPREAD,
    BULLET_RECOIL_PER_SHOT, BULLET_RECOIL_MAX, BULLET_RECOIL_RECOVERY,
    AI_EXTRA_SPREAD, CROUCH_SPREAD_MULT,
)
import math
import random


class Gun(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(
            parent=player,
            position=Vec3(0.3, 1.2, 0.5),
            model='cube',
            scale=(0.2, 0.2, 1),
            color=color.gray,
            origin_z=-0.5,
            **kwargs
        )
        self.player = player
        self.fire_cooldown = 0
        self.ammo = AMMO_CAPACITY
        self.reloading = False
        self.reload_timer = 0
        self.recoil = 0.0

    def _get_spread_deg(self):
        spread = BULLET_BASE_SPREAD
        if getattr(self.player, 'is_moving', False):
            spread += BULLET_MOVE_SPREAD
        if getattr(self.player, 'is_crouching', False):
            spread *= CROUCH_SPREAD_MULT
        spread += self.recoil
        if not self.player.is_local:
            spread += AI_EXTRA_SPREAD
        return spread

    def _spread_direction(self, base_dir, angle_deg):
        if angle_deg < 0.001:
            return base_dir
        angle_rad = math.radians(angle_deg)
        theta = random.uniform(0, angle_rad)
        phi = random.uniform(0, 2 * math.pi)

        # Build a perpendicular frame around base_dir
        if abs(base_dir.x) < 0.9:
            right = base_dir.cross(Vec3(1, 0, 0)).normalized()
        else:
            right = base_dir.cross(Vec3(0, 1, 0)).normalized()
        up = right.cross(base_dir).normalized()

        # Spherical-cap sample: rotate base_dir by theta around a random axis in the perp plane
        perp = right * math.cos(phi) + up * math.sin(phi)
        return (base_dir * math.cos(theta) + perp * math.sin(theta)).normalized()

    def shoot(self):
        if self.fire_cooldown > 0 or self.ammo <= 0 or self.reloading:
            return

        if self.player.is_local:
            base_dir = camera.forward
            origin = camera.world_position
        else:
            base_dir = self.forward
            origin = self.world_position

        spread = self._get_spread_deg()
        direction = self._spread_direction(base_dir, spread)

        # Hitscan raycast — ignore own entity and both hitboxes
        ray = raycast(
            origin,
            direction,
            distance=500,
            ignore=[self.player, self.player.body_hitbox, self.player.head_hitbox, self],
        )

        if ray.hit and ray.entity:
            target = getattr(ray.entity, 'owner', None)
            is_head = getattr(ray.entity, 'is_head', False)
            if target and not getattr(target, 'dead', True):
                opposing = self.player.team_manager.get_opposing_players(self.player.team_color)
                if target in opposing:
                    dmg = BULLET_DAMAGE * (HEADSHOT_MULTIPLIER if is_head else 1.0)
                    target.take_damage(dmg, attacker=self.player, headshot=is_head)

        # Visual tracer
        tracer_end = origin + direction * (ray.distance if ray.hit else 200)
        mid = (origin + tracer_end) * 0.5
        length = (tracer_end - origin).length()
        tracer = Entity(
            model='cube',
            color=color.rgba(255, 240, 120, 180),
            scale=(0.03, 0.03, length),
            position=mid,
        )
        tracer.look_at(tracer_end)
        destroy(tracer, delay=0.04)

        # Muzzle flash
        flash = Entity(
            parent=self,
            model='sphere',
            color=color.rgba(255, 210, 60, 220),
            scale=0.35,
            position=Vec3(0, 0, -1.1),
        )
        destroy(flash, delay=0.05)

        self.fire_cooldown = FIRE_RATE
        self.ammo -= 1
        self.recoil = min(self.recoil + BULLET_RECOIL_PER_SHOT, BULLET_RECOIL_MAX)

        if self.ammo == 0:
            self._start_reload()

    def reload(self):
        if not self.reloading and self.ammo < AMMO_CAPACITY:
            self._start_reload()

    def _start_reload(self):
        self.reloading = True
        self.reload_timer = RELOAD_TIME

    def reset(self):
        self.ammo = AMMO_CAPACITY
        self.reloading = False
        self.reload_timer = 0
        self.fire_cooldown = 0
        self.recoil = 0.0

    def update(self):
        if self.reloading:
            self.reload_timer -= time.dt
            if self.reload_timer <= 0:
                self.ammo = AMMO_CAPACITY
                self.reloading = False

        self.fire_cooldown = max(0, self.fire_cooldown - time.dt)
        self.recoil = max(0.0, self.recoil - BULLET_RECOIL_RECOVERY * time.dt)
