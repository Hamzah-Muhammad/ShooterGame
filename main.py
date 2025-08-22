from ursina import *
from map import create_map
from teams import team_manager
from scoreboard import Scoreboard
from search_destroy import SearchAndDestroyGame
import search_destroy

app = Ursina()

window.title = 'Streets of Karachi'
window.borderless = True
window.fullscreen = True
window.exit_button.visible = False
window.fps_counter.enabled = True
window.color = color.black
window.size = (1920, 1080)

scoreboard = None


def start_game(mode: str):
    """Initialize the selected game mode and hide the start menu."""
    global scoreboard
    start_menu.enabled = False
    create_map()
    team_manager.spawn_teams(mode=mode)
    scoreboard = Scoreboard(team_manager)
    if mode == '5v5':
        search_destroy.sd_game = SearchAndDestroyGame(team_manager)
        search_destroy.sd_game.start_round()
    else:
        search_destroy.sd_game = None
    mouse.locked = True


# --- Start Menu ---
start_menu = Entity(parent=camera.ui, ignore_paused=True)
Panel(
    parent=start_menu,
    scale=(0.6, 0.4),
    color=color.rgba(0, 0, 0, 150),
    ignore_paused=True,
)
Button(
    text='5v5 Search & Destroy',
    parent=start_menu,
    position=(0, 0.05),
    on_click=lambda: start_game('5v5'),
    ignore_paused=True,
)
Button(
    text='1v1 Duel',
    parent=start_menu,
    position=(0, -0.05),
    on_click=lambda: start_game('1v1'),
    ignore_paused=True,
)

# --- Pause Menu ---
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

def quit_game():
    application.quit()


Button(
    text='Close Game',
    parent=pause_menu,
    position=(0, -0.05),
    on_click=quit_game,
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
    if key == 'escape' and not start_menu.enabled:
        toggle_menu()


def update():
    if start_menu.enabled or pause_menu.enabled or not scoreboard:
        return
    for player in team_manager.all_players:
        player.update()
    scoreboard.update()
    if search_destroy.sd_game:
        search_destroy.sd_game.update()


app.run()
