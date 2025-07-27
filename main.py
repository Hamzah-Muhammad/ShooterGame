from ursina import *
from map import create_map
from teams import team_manager
from scoreboard import Scoreboard
from search_and_destroy import SearchAndDestroyGameMode

app = Ursina()

window.title = 'ShooterGame'
window.borderless = False
window.exit_button.visible = False
window.fps_counter.enabled = True
window.color = color.black
window.size = (1280, 720)

create_map()

team_manager.spawn_teams()
game_mode = SearchAndDestroyGameMode(team_manager)
scoreboard = Scoreboard(team_manager)

def update():
    for player in team_manager.all_players:
        player.update()
    game_mode.update()
    scoreboard.update()

app.run()
