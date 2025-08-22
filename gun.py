from ursina import *
from config import BULLET_SPEED, BULLET_LIFETIME, BULLET_DAMAGE

class Gun(Entity):
    def __init__(self, player, **kwargs):
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

    def shoot(self):
        if self.bullet:
            return  # Only one bullet at a time for now

        direction = self.forward
        if self.player.is_local:
            direction = camera.forward
        self.bullet = Entity(
            model='sphere',
            color=color.yellow,
            scale=0.1,
            position=self.world_position + direction * 1.5,
            direction=direction,
            speed=BULLET_SPEED,
            life=BULLET_LIFETIME,
            collider='sphere'
        )

    def update(self):
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
                    player.take_damage(BULLET_DAMAGE, attacker=self.player)
                    break
            destroy(self.bullet)
            self.bullet = None
