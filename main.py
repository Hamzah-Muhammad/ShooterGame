from ursina import *
from teams import team_manager
from scoreboard import Scoreboard
from config import MAP_SIZE


match_started = False

def _begin_match():
    global match_started
    match_started = True
    countdown_text.enabled = False


def _countdown(n=3):
    countdown_text.text = str(n)
    if n > 1:
        invoke(_countdown, n-1, delay=1)
    else:
        invoke(_begin_match, delay=1)

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
countdown_text = Text(text='', scale=3, origin=(0,0))
_countdown(3)

def update():
    if not match_started:
        return

    for player in team_manager.blue_team.players + team_manager.red_team.players:
        player.update()
        if hasattr(player, 'gun'):
            player.gun.update()

    scoreboard.update_score()


app.run()
