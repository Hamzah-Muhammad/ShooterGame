from ursina import *
from config import MAP_SIZE
from map import create_map
from teams import team_manager
from scoreboard import Scoreboard
from search_destroy import SearchAndDestroyGame
import search_destroy

app = Ursina()

window.title = 'ShooterGame'
window.borderless = True
window.fullscreen = True
window.exit_button.visible = False
window.fps_counter.enabled = True
window.color = color.black
window.size = (1920, 1080)

create_map()

team_manager.spawn_teams()
scoreboard = Scoreboard(team_manager)

# Pause menu — ignore_paused=True so it stays visible when application.paused
pause_menu = Entity(parent=camera.ui, enabled=False, ignore_paused=True)
Panel(
    parent=pause_menu,
    scale=(0.4, 0.3),
    color=color.rgba(0, 0, 0, 150),
    ignore_paused=True,
)
Button(
    text='Resume',
    parent=pause_menu,
    position=(0, 0.05),
    on_click=lambda: toggle_menu(False),
    ignore_paused=True,
)
Button(
    text='Close Game',
    parent=pause_menu,
    position=(0, -0.05),
    on_click=application.quit,
    ignore_paused=True,
)

def toggle_menu(show=None):
    if show is None:
        pause_menu.enabled = not pause_menu.enabled
    else:
        pause_menu.enabled = show
    mouse.locked = not pause_menu.enabled
    application.paused = pause_menu.enabled

def input(key):
    if key == 'escape':
        toggle_menu()

# Initialize Search & Destroy game mode
search_destroy.sd_game = SearchAndDestroyGame(team_manager)
search_destroy.sd_game.start_round()

def update():
    if pause_menu.enabled:
        return
    for player in team_manager.all_players:
        player.update()
    scoreboard.update()
    search_destroy.sd_game.update()

app.run()
