from ursina import *
from config import PLAYER_SCALE
from gun import Gun

class Player(Entity):
    def __init__(self, team_color, spawn_point, is_local=False, name="Player", team_manager=None, **kwargs):
        super().__init__(
            model='assets/soldier.obj',
            scale=PLAYER_SCALE,
            color=team_color,
            position=spawn_point,
            collider='box',
            **kwargs
        )

        self.name = name
        self.team_color = team_color
        self.is_local = is_local
        self.team_manager = team_manager
        self.kills = 0
        self.health = 100
        self.speed = 5
        self.ai_target = None
        self.double_sided = True
        self.grounded = True

        # Display name
        self.name_tag = Text(
            text=name,
            parent=self,
            y=2.2,
            world=True,
            scale=1,
            origin=(0, 0),
            color=color.white,
            billboard=True
        )

        # Camera setup
        if self.is_local:
            self.camera_pivot = Entity(parent=self, y=2)
            camera.parent = self.camera_pivot
            camera.position = (0, 0, -6)
            camera.rotation = (10, 0, 0)
            mouse.locked = False
        else:
            self.camera_pivot = self  # fallback for gun parenting

        # Gun setup
        self.gun = Gun(player=self)

    def update(self):
        if self.health <= 0:
            return

        if self.is_local:
            self._handle_input()
        else:
            self._update_ai()

    def _handle_input(self):
        move_dir = Vec3(
            held_keys['d'] - held_keys['a'],
            0,
            held_keys['w'] - held_keys['s']
        ).normalized()

        self.rotation_y += mouse.velocity[0] * 40
        self.position += self.forward * move_dir.z * self.speed * time.dt
        self.position += self.right * move_dir.x * self.speed * time.dt

        if held_keys['space']:
            self.jump()

        if held_keys['left mouse']:
            self.gun.shoot()

    def _update_ai(self):
        if not self.team_manager:
            return

        if not self.ai_target or self.ai_target.health <= 0:
            enemies = self.team_manager.get_opposing_team(self.team_color).players
            if enemies:
                self.ai_target = random.choice(enemies)

        if self.ai_target:
            dir_to_target = (self.ai_target.position - self.position).normalized()
            self.look_at(self.ai_target.position + Vec3(0, 1.5, 0))
            self.position += dir_to_target * self.speed * time.dt * 0.5

            if distance_xz(self, self.ai_target) < 20:
                self.gun.shoot()

    def jump(self):
        if not hasattr(self, 'velocity_y'):
            self.velocity_y = 0

        if self.grounded:
            self.velocity_y = 8
            self.grounded = False

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.on_death()

    def on_death(self):
        destroy(self)
        print(f"{self.name} has died.")
