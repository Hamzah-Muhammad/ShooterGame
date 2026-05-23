from ursina import *
from config import BULLET_SPEED, BULLET_LIFETIME, BULLET_DAMAGE, FIRE_RATE

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
        self.bullets = []
        self.fire_cooldown = 0

    def shoot(self):
        if self.fire_cooldown > 0:
            return

        direction = self.forward
        if self.player.is_local:
            direction = camera.forward

        bullet = Entity(
            model='sphere',
            color=color.yellow,
            scale=0.1,
            position=self.world_position + direction * 1.5,
            direction=direction,
            speed=BULLET_SPEED,
            life=BULLET_LIFETIME,
            collider='sphere'
        )
        self.bullets.append(bullet)
        self.fire_cooldown = FIRE_RATE

        # Muzzle flash
        flash = Entity(
            parent=self,
            model='sphere',
            color=color.rgba(255, 210, 60, 220),
            scale=0.35,
            position=Vec3(0, 0, -1.1),
        )
        destroy(flash, delay=0.05)

    def update(self):
        self.fire_cooldown = max(0, self.fire_cooldown - time.dt)
        self._update_bullets()

    def _update_bullets(self):
        for bullet in self.bullets[:]:
            bullet.position += bullet.direction * bullet.speed * time.dt
            bullet.life -= time.dt

            if bullet.life <= 0:
                destroy(bullet)
                self.bullets.remove(bullet)
                continue

            hit = False
            for player in self.player.team_manager.get_opposing_players(self.player.team_color):
                if player.dead:
                    continue
                if bullet.intersects(player.hitbox).hit:
                    player.take_damage(BULLET_DAMAGE, attacker=self.player)
                    destroy(bullet)
                    self.bullets.remove(bullet)
                    hit = True
                    break
