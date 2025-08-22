from ursina import *
from config import BULLET_SPEED, BULLET_LIFETIME, BULLET_DAMAGE
from typing import Optional

class Gun(Entity):
    """Basic firearm entity used by players.

    The original implementation only supported a single generic weapon.  This
    class now exposes a few tunable attributes (damage, rate of fire, bullet
    speed/lifetime) so that specific weapon types such as the AK‑47 or M4A1 can
    simply subclass ``Gun`` with their own stats.
    """

    cost = 0

    def __init__(
        self,
        player,
        bullet_speed=BULLET_SPEED,
        bullet_lifetime=BULLET_LIFETIME,
        damage=BULLET_DAMAGE,
        fire_rate: float = 0.1,
        cost: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(
            parent=player,
            position=Vec3(0.3, 1.2, 0.5),
            model='cube',
            texture='white_cube',
            scale=(0.2, 0.2, 1),
            color=color.rgb(80, 80, 80),
            origin_z=-0.5,
            **kwargs
        )
        self.player = player
        self.bullet = None
        self.bullet_timer = 0
        self.bullet_speed = bullet_speed
        self.bullet_lifetime = bullet_lifetime
        self.damage = damage
        self.fire_rate = fire_rate
        self.cost = cost if cost is not None else self.__class__.cost
        self._cooldown = 0

    def shoot(self):
        if self.bullet or self._cooldown > 0:
            return  # rate-limited firing

        direction = self.forward
        if self.player.is_local:
            direction = camera.forward
        self.bullet = Entity(
            model='sphere',
            color=color.yellow,
            scale=0.1,
            position=self.world_position + direction * 1.5,
            direction=direction,
            speed=self.bullet_speed,
            life=self.bullet_lifetime,
            collider='sphere'
        )
        self._cooldown = self.fire_rate

    def update(self):
        # handle fire-rate cooldown
        if self._cooldown > 0:
            self._cooldown = max(0, self._cooldown - time.dt)
        self.update_bullet()

    def update_bullet(self):
        if not self.bullet:
            return

        self.bullet.position += self.bullet.direction * self.bullet.speed * time.dt
        self.bullet.life -= time.dt

        if self.bullet.life <= 0:
            destroy(self.bullet)
            self.bullet = None
            return

        # Check for a collision against any entity in the world.  This avoids
        # manually testing the bullet against each player every frame and also
        # lets bullets disappear when they hit walls or other scenery.
        hit_info = self.bullet.intersects(ignore=[self.player])
        if hit_info.hit:
            for player in self.player.team_manager.get_opposing_players(self.player.team_color):
                if hit_info.entity == player.hitbox:
                    player.take_damage(self.damage, attacker=self.player)
                    break
            destroy(self.bullet)
            self.bullet = None


# --- Specific weapons -----------------------------------------------------


class AK47(Gun):
    cost = 2700

    def __init__(self, player, **kwargs):
        super().__init__(player, damage=35, fire_rate=0.1, **kwargs)


class L96A1(Gun):
    cost = 4750

    def __init__(self, player, **kwargs):
        super().__init__(player, damage=90, fire_rate=1.2, **kwargs)


class M4A1(Gun):
    cost = 3100

    def __init__(self, player, **kwargs):
        super().__init__(player, damage=30, fire_rate=0.1, **kwargs)


class DSR1(Gun):
    cost = 5000

    def __init__(self, player, **kwargs):
        super().__init__(player, damage=95, fire_rate=1.3, **kwargs)
