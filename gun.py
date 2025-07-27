from ursina import *
from config import BULLET_SPEED, BULLET_LIFETIME, BULLET_DAMAGE

class Gun(Entity):
    def __init__(self, player, **kwargs):
        parent_entity = camera if player.is_local else player
        gun_position = Vec3(0.3, -0.2, 1) if player.is_local else Vec3(0.3, 1.2, 0.5)

        super().__init__(
            parent=parent_entity,
            position=gun_position,
            model='cube',
            scale=(0.2, 0.2, 1),
            color=color.gray,
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

        # Check hit against each opposing player's hitbox
        for player in self.player.team_manager.get_opposing_players(self.player.team_color):
            if player.dead:
                continue
            if self.bullet.intersects(player.hitbox).hit:
                player.take_damage(BULLET_DAMAGE, attacker=self.player)
                destroy(self.bullet)
                self.bullet = None
                break
