from ursina import *
from player import Player

app = Ursina()

window.color = color.rgb(180, 220, 255)
window.title = "5v5 Third-Person Shooter"

camera.fov = 90
camera.clip_plane_near = 0.1

# Create a large flat map
ground = Entity(
    model='plane',
    scale=(100, 1, 100),
    texture='white_cube',
    texture_scale=(100, 100),
    color=color.green,
    collider='box'
)

# Field border walls
walls = [
    Entity(model='cube', scale=(1, 10, 100), position=(-50, 5, 0), color=color.gray, collider='box'),
    Entity(model='cube', scale=(1, 10, 100), position=(50, 5, 0), color=color.gray, collider='box'),
    Entity(model='cube', scale=(100, 10, 1), position=(0, 5, -50), color=color.gray, collider='box'),
    Entity(model='cube', scale=(100, 10, 1), position=(0, 5, 50), color=color.gray, collider='box')
]

# Spawn 5 local team players (you can control the first one)
local_player = Player(team_color=color.azure, spawn_point=(-20, 0, -30), is_local=True)

# Spawn additional allies (AI/placeholder)
team_players = [local_player]
for i in range(1, 5):
    team_players.append(
        Player(team_color=color.azure, spawn_point=(-20 + i * 10, 0, -30))
    )

# Spawn 5 enemies
enemies = []
for i in range(5):
    enemies.append(
        Player(team_color=color.red, spawn_point=(-20 + i * 10, 0, 30))
    )

app.run()
