from ursina import *
from config import MAP_SIZE
from map import create_map
from teams import team_manager
from scoreboard import Scoreboard
from search_destroy import SearchAndDestroyGame
import search_destroy

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

# Initialize Search & Destroy game mode
search_destroy.sd_game = SearchAndDestroyGame(team_manager)
search_destroy.sd_game.start_round()

def update():
    for player in team_manager.all_players:
        player.update()
    scoreboard.update()

app.run()
