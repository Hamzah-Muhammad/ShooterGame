from ursina import *
from config import (
    HEADSHOT_MULTIPLIER,
    BULLET_RECOIL_RECOVERY,
    AI_EXTRA_SPREAD,
    CROUCH_SPREAD_MULT,
    AK47_DAMAGE, AK47_FIRE_RATE, AK47_AMMO, AK47_RELOAD_TIME,
    AK47_RECOIL_PER_SHOT, AK47_RECOIL_MAX, AK47_BASE_SPREAD, AK47_MOVE_SPREAD,
    SNIPER_DAMAGE, SNIPER_FIRE_RATE, SNIPER_AMMO, SNIPER_RELOAD_TIME,
    SNIPER_BOLT_DELAY, SNIPER_BASE_SPREAD, SNIPER_MOVE_SPREAD, SNIPER_SCOPE_FOV,
)
import math
import random


def _ray_aabb(origin, direction, box_min, box_max):
    """Slab-method ray vs AABB. Returns distance to first intersection (>=0) or None."""
    t_min = 0.0
    t_max = float('inf')
    for i in range(3):
        d = direction[i]
        o = origin[i]
        lo = box_min[i]
        hi = box_max[i]
        if abs(d) < 1e-9:
            if o < lo or o > hi:
                return None
        else:
            t1 = (lo - o) / d
            t2 = (hi - o) / d
            if t1 > t2:
                t1, t2 = t2, t1
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
            if t_min > t_max:
                return None
    return t_min


# Populated by zombies_mode when in zombies mode; gun checks this when
# team_manager is None so S&D and Zombies share the same shoot() path.
zombie_targets = []

WEAPON_STATS = {
    'ak47': {
        'damage':          AK47_DAMAGE,
        'fire_rate':       AK47_FIRE_RATE,
        'ammo':            AK47_AMMO,
        'reload_time':     AK47_RELOAD_TIME,
        'recoil_per_shot': AK47_RECOIL_PER_SHOT,
        'recoil_max':      AK47_RECOIL_MAX,
        'base_spread':     AK47_BASE_SPREAD,
        'move_spread':     AK47_MOVE_SPREAD,
        'bolt_action':     False,
        'bolt_delay':      0.0,
        'gun_color':       color.rgb32(40, 30, 20),
        'gun_scale':       Vec3(0.2, 0.2, 1.0),
    },
    'sniper': {
        'damage':          SNIPER_DAMAGE,
        'fire_rate':       SNIPER_FIRE_RATE,
        'ammo':            SNIPER_AMMO,
        'reload_time':     SNIPER_RELOAD_TIME,
        'recoil_per_shot': 0.0,
        'recoil_max':      0.0,
        'base_spread':     SNIPER_BASE_SPREAD,
        'move_spread':     SNIPER_MOVE_SPREAD,
        'bolt_action':     True,
        'bolt_delay':      SNIPER_BOLT_DELAY,
        'gun_color':       color.rgb32(55, 50, 45),
        'gun_scale':       Vec3(0.12, 0.12, 1.8),
    },
}


class Gun(Entity):
    def __init__(self, player, weapon_type='ak47', **kwargs):
        stats = WEAPON_STATS[weapon_type]
        super().__init__(
            parent=player,
            position=Vec3(0.3, 1.2, 0.5),
            model='cube',
            scale=stats['gun_scale'],
            color=stats['gun_color'],
            origin_z=-0.5,
            **kwargs
        )
        self.player = player
        self.weapon_type = weapon_type
        self._stats = stats

        self.fire_cooldown = 0.0
        self.ammo = stats['ammo']
        self.reloading = False
        self.reload_timer = 0.0
        self.recoil = 0.0

        self.bolt_cycling = False
        self.bolt_timer = 0.0

        self.scoped = False
        self.scope_overlay = None
        if weapon_type == 'sniper' and player.is_local:
            self._build_scope_overlay()

    # ── Scope overlay ──────────────────────────────────────────────────────────
    def _build_scope_overlay(self):
        self.scope_overlay = Entity(parent=camera.ui, enabled=False)
        B = color.black
        # Four black panels leave a rectangular center gap (the scope viewport)
        Entity(parent=self.scope_overlay, model='quad', color=B,
               scale=(2.0, 0.80), position=(0,  0.60))
        Entity(parent=self.scope_overlay, model='quad', color=B,
               scale=(2.0, 0.80), position=(0, -0.60))
        Entity(parent=self.scope_overlay, model='quad', color=B,
               scale=(0.70, 0.40), position=(-0.85, 0))
        Entity(parent=self.scope_overlay, model='quad', color=B,
               scale=(0.70, 0.40), position=( 0.85, 0))
        # Subtle scope glass tint
        Entity(parent=self.scope_overlay, model='quad',
               color=color.rgba32(0, 25, 8, 55), scale=(0.60, 0.40))
        # Crosshair lines
        Entity(parent=self.scope_overlay, model='quad',
               color=color.white, scale=(0.50, 0.0018))
        Entity(parent=self.scope_overlay, model='quad',
               color=color.white, scale=(0.0018, 0.38))
        # Center dot
        Entity(parent=self.scope_overlay, model='quad',
               color=color.red, scale=(0.006, 0.006))

    def _destroy_scope_overlay(self):
        if self.scope_overlay:
            destroy(self.scope_overlay)
            self.scope_overlay = None

    def scope_in(self):
        if (self.weapon_type != 'sniper' or self.scoped
                or self.bolt_cycling or not self.player.is_local):
            return
        self.scoped = True
        camera.fov = SNIPER_SCOPE_FOV
        if self.scope_overlay:
            self.scope_overlay.enabled = True
        if hasattr(self.player, 'crosshair'):
            self.player.crosshair.enabled = False

    def scope_out(self):
        if not self.scoped or not self.player.is_local:
            return
        self.scoped = False
        camera.fov = 90
        if self.scope_overlay:
            self.scope_overlay.enabled = False
        if hasattr(self.player, 'crosshair'):
            self.player.crosshair.enabled = True

    # ── Weapon switching ────────────────────────────────────────────────────────
    def set_weapon(self, weapon_type):
        if self.scoped:
            self.scope_out()
        self._destroy_scope_overlay()

        stats = WEAPON_STATS[weapon_type]
        self.weapon_type = weapon_type
        self._stats = stats
        self.scale = stats['gun_scale']
        self.color = stats['gun_color']
        self.ammo = stats['ammo']
        self.reloading = False
        self.reload_timer = 0.0
        self.fire_cooldown = 0.0
        self.recoil = 0.0
        self.bolt_cycling = False
        self.bolt_timer = 0.0
        self.scoped = False

        if self.player.is_local:
            self.player.camera_recoil = 0.0

        if weapon_type == 'sniper' and self.player.is_local:
            self._build_scope_overlay()

    # ── Spread calculation ──────────────────────────────────────────────────────
    def _get_spread_deg(self):
        s = self._stats
        spread = s['base_spread']
        if getattr(self.player, 'is_moving', False):
            spread += s['move_spread']
        if getattr(self.player, 'is_crouching', False):
            spread *= CROUCH_SPREAD_MULT
        spread += self.recoil
        if not self.player.is_local:
            spread += AI_EXTRA_SPREAD
        if self.scoped and not getattr(self.player, 'is_moving', False):
            spread = 0.0
        return spread

    def _spread_direction(self, base_dir, angle_deg):
        if angle_deg < 0.001:
            return base_dir
        angle_rad = math.radians(angle_deg)
        theta = random.uniform(0, angle_rad)
        phi = random.uniform(0, 2 * math.pi)
        if abs(base_dir.x) < 0.9:
            right = base_dir.cross(Vec3(1, 0, 0)).normalized()
        else:
            right = base_dir.cross(Vec3(0, 1, 0)).normalized()
        up = right.cross(base_dir).normalized()
        perp = right * math.cos(phi) + up * math.sin(phi)
        return (base_dir * math.cos(theta) + perp * math.sin(theta)).normalized()

    # ── Shoot ───────────────────────────────────────────────────────────────────
    def shoot(self):
        if self.fire_cooldown > 0 or self.ammo <= 0 or self.reloading:
            return
        if self._stats['bolt_action'] and self.bolt_cycling:
            return

        if self.player.is_local:
            base_dir = camera.forward
            origin = camera.world_position + base_dir
        else:
            base_dir = self.forward
            origin = self.world_position

        spread = self._get_spread_deg()
        direction = self._spread_direction(base_dir, spread)

        # ── Step 1: AABB check against each enemy — bypasses Ursina's entity
        #   lookup so hit registration doesn't depend on Panda3D collision quirks.
        best_target  = None
        best_is_head = False
        best_dist    = 499.0

        tm = self.player.team_manager
        if tm is not None:
            candidates = tm.get_opposing_players(self.player.team_color)
        else:
            candidates = [z for z in zombie_targets if not getattr(z, 'dead', True)]

        for candidate in candidates:
            if getattr(candidate, 'dead', True):
                continue
            for is_head, bounds in [(False, candidate.get_body_bounds()),
                                     (True,  candidate.get_head_bounds())]:
                d = _ray_aabb(origin, direction, bounds[0], bounds[1])
                if d is not None and 0 <= d < best_dist:
                    best_dist    = d
                    best_target  = candidate
                    best_is_head = is_head

        # ── Step 2: wall obstruction — raycast against map geometry only.
        #   We only need ray.hit / ray.distance here, not ray.entity.
        if tm is not None:
            all_player_nodes = []
            for p in tm.all_players:
                all_player_nodes += [p, p.body_hitbox, p.head_hitbox]
            all_player_nodes.append(self)
        else:
            # Zombies mode: ignore all zombie entities so wall check doesn't
            # mistake a zombie body for a wall (AABB already handled hits above).
            all_player_nodes = list(zombie_targets) + [self]

        wall = raycast(origin, direction,
                       distance=best_dist if best_target else 499,
                       ignore=all_player_nodes)

        if wall.hit:
            best_target = None
            tracer_dist = wall.distance
        elif best_target:
            tracer_dist = best_dist
        else:
            tracer_dist = 200

        # ── Step 3: apply damage ──────────────────────────────────────────────
        if best_target:
            dmg = self._stats['damage'] * (HEADSHOT_MULTIPLIER if best_is_head else 1.0)
            best_target.take_damage(dmg, attacker=self.player, headshot=best_is_head)

        # Visual tracer — clamp to avoid zero-length entity at extreme close range
        tracer_end = origin + direction * max(0.05, tracer_dist)
        mid = (origin + tracer_end) * 0.5
        length = (tracer_end - origin).length()
        tracer = Entity(
            model='cube',
            color=color.rgba32(255, 240, 120, 180),
            scale=(0.03, 0.03, length),
            position=mid,
        )
        tracer.look_at(tracer_end)
        destroy(tracer, delay=0.04)

        # Muzzle flash
        flash = Entity(
            parent=self,
            model='sphere',
            color=color.rgba32(255, 210, 60, 220),
            scale=0.35,
            position=Vec3(0, 0, -1.1),
        )
        destroy(flash, delay=0.05)

        self.fire_cooldown = self._stats['fire_rate']
        self.ammo -= 1

        if self._stats['bolt_action']:
            if self.player.is_local:
                self.scope_out()
            self.bolt_cycling = True
            self.bolt_timer = self._stats['bolt_delay']
        else:
            self.recoil = min(
                self.recoil + self._stats['recoil_per_shot'],
                self._stats['recoil_max'],
            )
            if self.player.is_local:
                self.player.camera_recoil = max(
                    -self._stats['recoil_max'] * 2.5,
                    self.player.camera_recoil - self._stats['recoil_per_shot'] * 2.5,
                )

        if self.ammo == 0:
            self._start_reload()

    def reload(self):
        if not self.reloading and self.ammo < self._stats['ammo']:
            self._start_reload()

    def _start_reload(self):
        if self.scoped:
            self.scope_out()
        self.reloading = True
        self.reload_timer = self._stats['reload_time']

    def reset(self):
        if self.scoped:
            self.scope_out()
        self.ammo = self._stats['ammo']
        self.reloading = False
        self.reload_timer = 0.0
        self.fire_cooldown = 0.0
        self.recoil = 0.0
        self.bolt_cycling = False
        self.bolt_timer = 0.0
        if self.player.is_local:
            self.player.camera_recoil = 0.0

    def update(self):
        if self.reloading:
            self.reload_timer -= time.dt
            if self.reload_timer <= 0:
                self.ammo = self._stats['ammo']
                self.reloading = False

        self.fire_cooldown = max(0.0, self.fire_cooldown - time.dt)

        if self._stats['bolt_action']:
            if self.bolt_cycling:
                self.bolt_timer -= time.dt
                if self.bolt_timer <= 0:
                    self.bolt_cycling = False
                    self.bolt_timer = 0.0
        else:
            self.recoil = max(0.0, self.recoil - BULLET_RECOIL_RECOVERY * time.dt)
            if self.player.is_local and self.player.camera_recoil < 0:
                self.player.camera_recoil = min(
                    0.0,
                    self.player.camera_recoil + BULLET_RECOIL_RECOVERY * 2.5 * time.dt,
                )
