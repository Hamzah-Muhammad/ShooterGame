from ursina import *
from player import Player
from team import Team

app = Ursina()

# Ground and sky
Entity(model='plane', texture='white_cube', scale=(50, 1, 50), collider='box', texture_scale=(50, 50))
Sky()

# Local player (you)
my_player = Player(team_color=color.red, spawn_point=(-10, 0, 10), is_local=True)

# Teams
team_red = Team('Red', color.red, spawn_area=(-10, 0, 10))
team_blue = Team('Blue', color.blue, spawn_area=(10, 0, -10))

# Add teammates and enemies
for _ in range(4):
    team_red.add_player()
for _ in range(5):
    team_blue.add_player()

app.run()
