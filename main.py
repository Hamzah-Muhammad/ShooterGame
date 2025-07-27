from ursina import *
from config import MAP_SIZE
from map import create_map
from teams import team_manager
from scoreboard import Scoreboard

app = Ursina()

window.title = 'ShooterGame'
window.borderless = False
window.exit_button.visible = False
window.fps_counter.enabled = True
window.color = color.black
window.size = (1280, 720)

create_map()

team_manager.spawn_teams()
scoreboard = Scoreboard(team_manager)

def update():
    for player in team_manager.all_players:
        player.update()

app.run()
