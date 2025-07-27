from ursina import *
from teams import team_manager
from scoreboard import Scoreboard
from config import MAP_SIZE

app = Ursina()

window.color = color.rgb(100, 149, 237)
window.borderless = False
window.fullscreen = False
window.size = (1280, 720)
window.position = Vec2(192, 108)

# Load map
ground = Entity(
    model='plane',
    texture='white_cube',
    texture_scale=(MAP_SIZE, MAP_SIZE),
    scale=(MAP_SIZE, 1, MAP_SIZE),
    color=color.gray,
    collider='box'
)

team_manager.spawn_teams()
scoreboard = Scoreboard(team_manager)

def update():
    for player in team_manager.blue_team.players + team_manager.red_team.players:
        player.update()
        if hasattr(player, 'gun'):
            player.gun.update()

    scoreboard.update_score()


app.run()
