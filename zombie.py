from ursina import *
import math
import random
import zombies_points as zp

MELEE_RANGE    = 2.0    # units — attack if within this distance
MELEE_DAMAGE   = 25     # 4 hits to kill player (100 HP)
MELEE_COOLDOWN = 1.0    # seconds between hits per zombie
_GRAVITY       = -20


class Zombie(Entity):
    def __init__(self, position, target_player, max_health=150, speed=2.0,
                 on_death=None, **kwargs):
        super().__init__(
            model='soldier.obj',
            double_sided=True,
            scale=1.5,
            color=color.rgb32(70, 130, 70),
            position=Vec3(position.x, 1, position.z),
            **kwargs
        )
        self.is_zombie     = True
        self.target_player = target_player
        self.max_health    = max_health
        self.health        = float(max_health)
        self.speed         = speed
        self.dead          = False
        self._melee_cd     = random.uniform(0, 0.5)   # stagger so group doesn't hit simultaneously
        self._vel_y        = 0.0
        self._on_ground    = True
        self._on_death     = on_death
        self._avoid_dir    = Vec3(1, 0, 0)
        self._avoid_timer  = 0.0

        # Collider for wall probing and to physically block player movement
        self.collider = BoxCollider(self, center=Vec3(0, 1.2, 0),
                                    size=Vec3(1.5, 2.4, 1.5))

    # ── Per-frame update ──────────────────────────────────────────────────────
    def update(self):
        if self.dead:
            return
        self._apply_gravity()
        self._move_toward_player()
        self._tick_melee()

    def _apply_gravity(self):
        if not self._on_ground:
            self._vel_y += _GRAVITY * time.dt
        self.y += self._vel_y * time.dt
        if self.y <= 1.0:
            self.y       = 1.0
            self._vel_y  = 0.0
            self._on_ground = True
        else:
            self._on_ground = False

    def _move_toward_player(self):
        player = self.target_player
        if player is None or getattr(player, 'dead', True):
            return

        to_player = player.position - self.position
        to_player.y = 0
        dist = to_player.length()

        if dist < MELEE_RANGE or dist < 0.01:
            return

        direction = to_player.normalized()
        self.rotation_y = math.degrees(math.atan2(direction.x, direction.z))

        # Build ignore list: self + player hitboxes (so zombie walks up to player)
        ignore = [self]
        if player:
            ignore += [player,
                       getattr(player, 'body_hitbox', None),
                       getattr(player, 'head_hitbox', None)]
        ignore = [e for e in ignore if e is not None]

        probe = raycast(
            self.world_position + Vec3(0, 1.2, 0),
            direction,
            distance=0.9,
            ignore=ignore,
        )

        blocked = probe.hit and not getattr(probe.entity, 'is_zombie', False)

        if not blocked:
            self._avoid_timer = 0.0
            self.position += direction * self.speed * time.dt
        else:
            # Stuck on a wall — strafe perpendicular until clear
            self._avoid_timer += time.dt
            if self._avoid_timer < 0.05:
                # Pick a new avoidance direction on first block
                self._avoid_dir = Vec3(-direction.z, 0, direction.x).normalized()
                if random.random() > 0.5:
                    self._avoid_dir = -self._avoid_dir
            self.position += self._avoid_dir * self.speed * time.dt

    def _tick_melee(self):
        self._melee_cd = max(0.0, self._melee_cd - time.dt)
        player = self.target_player
        if player is None or getattr(player, 'dead', True):
            return
        if self._melee_cd > 0:
            return
        dist = (player.position - self.position).length()
        if dist < MELEE_RANGE:
            player.take_damage(MELEE_DAMAGE)
            self._melee_cd = MELEE_COOLDOWN

    # ── AABB bounds — same interface as Player, consumed by gun.shoot() ───────
    def get_body_bounds(self):
        x, y, z = self.x, self.y, self.z
        cy, hw = y + 1.2, 1.2
        return (Vec3(x - 0.75, cy - hw, z - 0.75),
                Vec3(x + 0.75, cy + hw, z + 0.75))

    def get_head_bounds(self):
        x, y, z = self.x, self.y, self.z
        cy, hw = y + 2.7, 0.3
        return (Vec3(x - 0.4125, cy - hw, z - 0.4125),
                Vec3(x + 0.4125, cy + hw, z + 0.4125))

    # ── Damage / death ────────────────────────────────────────────────────────
    def take_damage(self, amount, attacker=None, headshot=False):
        if self.dead:
            return

        zp.on_hit()

        if attacker and getattr(attacker, 'is_local', False):
            attacker._show_hit_marker(headshot=headshot)

        self.health -= amount   # gun.py already applied headshot multiplier
        if self.health <= 0:
            self._die(headshot=headshot)

    def _die(self, headshot=False):
        if self.dead:
            return
        self.dead     = True
        self.collider = None
        self.visible  = False

        zp.on_kill(headshot=headshot)

        if self._on_death:
            self._on_death(self)

        destroy(self, delay=0.5)
