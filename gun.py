from ursina import *
from constants import BULLET_SPEED, BULLET_LIFETIME

class Gun(Entity):
    def __init__(self, player, **kwargs):
        # Set default values without causing duplicate keyword conflicts
        kwargs.setdefault('parent', player.camera_pivot)
        kwargs.setdefault('model', 'cube')
        kwargs.setdefault('scale', (0.1, 0.1, 1))
        kwargs.setdefault('color', color.black)
        kwargs.setdefault('position', (0.3, -0.3, 1))

        super().__init__(**kwargs)

        self.player = player
        self.last_fired = 0
        self.cooldown = 0.1  # seconds

    def fire(self, from_pos, direction):
        current_time = time.time()
        if current_time - self.last_fired < self.cooldown:
            return

        self.last_fired = current_time

        ray = raycast(from_pos, direction, distance=100, ignore=[self.player])
        if ray.hit and hasattr(ray.entity, 'hit'):
            ray.entity.hit(self.player)

        bullet = Entity(
            model='sphere',
            color=color.yellow,
            scale=0.1,
            position=from_pos + direction.normalized() * 1.5,
            collider=None
        )
        bullet.animate_position(
            bullet.position + direction.normalized() * BULLET_SPEED,
            duration=BULLET_LIFETIME,
            curve=curve.linear
        )
        destroy(bullet, delay=BULLET_LIFETIME)
