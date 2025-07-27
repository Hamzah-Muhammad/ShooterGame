from ursina import *
from ursina.prefabs.health_bar import HealthBar
from config import BULLET_SPEED, BULLET_LIFETIME

class Gun(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(
            model='cube',
            color=color.gray,
            scale=(0.2, 0.1, 0.6),
            position=(0.3, -0.2, 0.6),
            rotation=(0, 0, 0),
            **kwargs
        )
        self.player = player
        self.bullet = None
        self.bullet_lifetime = BULLET_LIFETIME
        self.last_shot_time = 0
        self.shoot_interval = 1  # AI shoots every 1 second

    def shoot(self):
        if self.bullet:
            return

        self.bullet = Entity(
            model='sphere',
            color=color.yellow,
            scale=0.1,
            position=self.world_position,
            direction=self.forward,
            speed=BULLET_SPEED,
            origin=self.world_position,
        )

    def update(self):
        self.update_bullet()

        # AI shooting logic
        if not self.player.is_local:
            if time.time() - self.last_shot_time >= self.shoot_interval:
                self.shoot()
                self.last_shot_time = time.time()

    def update_bullet(self):
        if not self.bullet:
            return

        try:
            self.bullet.position += self.bullet.direction * self.bullet.speed * time.dt
        except Exception:
            self.bullet = None
            return

        # Check collision with opponents
        try:
            for player in self.player.team_manager.get_opposing_players(self.player.team_color):
                if not player or not player.enabled:
                    continue
                if distance(self.bullet.position, player.position) < 1.5:
                    player.health -= 25
                    if player.health <= 0:
                        self.player.kills += 1
                        player.die()
                    destroy(self.bullet)
                    self.bullet = None
                    return
        except Exception:
            pass

        # Check if bullet exceeded range
        if distance(self.bullet.origin, self.bullet.position) > 50:
            destroy(self.bullet)
            self.bullet = None
