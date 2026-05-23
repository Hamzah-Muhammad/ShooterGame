from ursina import *
from config import BULLET_SPEED, BULLET_LIFETIME, BULLET_DAMAGE, FIRE_RATE, AMMO_CAPACITY, RELOAD_TIME

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
        self.ammo = AMMO_CAPACITY
        self.reloading = False
        self.reload_timer = 0

    def shoot(self):
        if self.fire_cooldown > 0 or self.ammo <= 0 or self.reloading:
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
        self.ammo -= 1

        if self.ammo == 0:
            self._start_reload()

        # Muzzle flash
        flash = Entity(
            parent=self,
            model='sphere',
            color=color.rgba(255, 210, 60, 220),
            scale=0.35,
            position=Vec3(0, 0, -1.1),
        )
        destroy(flash, delay=0.05)

    def reload(self):
        if not self.reloading and self.ammo < AMMO_CAPACITY:
            self._start_reload()

    def _start_reload(self):
        self.reloading = True
        self.reload_timer = RELOAD_TIME

    def reset(self):
        """Full ammo restore — called on respawn."""
        for bullet in self.bullets:
            destroy(bullet)
        self.bullets = []
        self.ammo = AMMO_CAPACITY
        self.reloading = False
        self.reload_timer = 0
        self.fire_cooldown = 0

    def update(self):
        if self.reloading:
            self.reload_timer -= time.dt
            if self.reload_timer <= 0:
                self.ammo = AMMO_CAPACITY
                self.reloading = False
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

            for player in self.player.team_manager.get_opposing_players(self.player.team_color):
                if player.dead:
                    continue
                if bullet.intersects(player.hitbox).hit:
                    player.take_damage(BULLET_DAMAGE, attacker=self.player)
                    destroy(bullet)
                    self.bullets.remove(bullet)
                    break
