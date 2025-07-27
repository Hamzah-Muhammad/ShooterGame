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

# Pause menu setup

class PauseMenu(Entity):
    """Simple pause menu with Resume and Close Game buttons."""

    def __init__(self):
        super().__init__(parent=camera.ui, enabled=False)
        self.panel = Panel(scale=(0.4, 0.3), model='quad', color=color.gray, parent=self)
        self.resume_button = Button(text='Resume', scale=(0.3, 0.1), position=(0, 0.05), parent=self)
        self.resume_button.on_click = self.resume
        self.quit_button = Button(text='Close Game', color=color.red, scale=(0.3, 0.1), position=(0, -0.05), parent=self)
        self.quit_button.on_click = application.quit

    def resume(self):
        self.disable()
        mouse.locked = True

pause_menu = PauseMenu()

# Initialize Search & Destroy game mode
search_destroy.sd_game = SearchAndDestroyGame(team_manager)
search_destroy.sd_game.start_round()

def update():
    for player in team_manager.all_players:
        player.update()
    scoreboard.update()

def input(key):
    if key == 'escape':
        pause_menu.enabled = not pause_menu.enabled
        mouse.locked = not pause_menu.enabled

app.run()
