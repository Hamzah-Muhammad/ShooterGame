from ursina import *
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
local_player = next(p for p in team_manager.all_players if p.is_local)
scoreboard = Scoreboard(team_manager)

# ── Pause menu ────────────────────────────────────────────────────────────────
pause_menu = Entity(parent=camera.ui, enabled=False, ignore_paused=True)
Panel(
    parent=pause_menu,
    scale=(0.4, 0.38),
    color=color.rgba32(0, 0, 0, 150),
    ignore_paused=True,
)
Button(
    text='Resume',
    parent=pause_menu,
    position=(0, 0.10),
    on_click=lambda: toggle_menu(False),
    ignore_paused=True,
)
Button(
    text='Loadout',
    parent=pause_menu,
    position=(0, 0.0),
    on_click=lambda: toggle_loadout(True),
    ignore_paused=True,
)
Button(
    text='Close Game',
    parent=pause_menu,
    position=(0, -0.10),
    on_click=application.quit,
    ignore_paused=True,
)

# ── Loadout menu ──────────────────────────────────────────────────────────────
loadout_menu = Entity(parent=camera.ui, enabled=False, ignore_paused=True)
Panel(
    parent=loadout_menu,
    scale=(0.58, 0.52),
    color=color.rgba32(0, 0, 0, 185),
    ignore_paused=True,
)
Text(
    text='LOADOUT',
    parent=loadout_menu,
    position=(0, 0.20),
    origin=(0, 0),
    scale=2.4,
    color=color.white,
    ignore_paused=True,
)
Text(
    text='Choice applies at the start of the next round',
    parent=loadout_menu,
    position=(0, 0.12),
    origin=(0, 0),
    scale=1.1,
    color=color.light_gray,
    ignore_paused=True,
)

ak47_btn = Button(
    text='AK-47',
    parent=loadout_menu,
    position=(-0.13, 0.02),
    scale=(0.22, 0.09),
    color=color.azure,      # default selected
    ignore_paused=True,
    on_click=lambda: select_weapon('ak47'),
)
sniper_btn = Button(
    text='L96A1',
    parent=loadout_menu,
    position=(0.13, 0.02),
    scale=(0.22, 0.09),
    color=color.gray,
    ignore_paused=True,
    on_click=lambda: select_weapon('sniper'),
)

Text(
    text='Full-auto  •  30 rounds',
    parent=loadout_menu,
    position=(-0.13, -0.06),
    origin=(0, 0),
    scale=1.0,
    color=color.light_gray,
    ignore_paused=True,
)
Text(
    text='Bolt-action  •  5 rounds  •  1-shot kill',
    parent=loadout_menu,
    position=(0.13, -0.06),
    origin=(0, 0),
    scale=1.0,
    color=color.light_gray,
    ignore_paused=True,
)
Text(
    text='Hold RMB to scope in',
    parent=loadout_menu,
    position=(0.13, -0.11),
    origin=(0, 0),
    scale=0.9,
    color=color.rgb32(160, 200, 160),
    ignore_paused=True,
)

Button(
    text='Back',
    parent=loadout_menu,
    position=(0, -0.19),
    scale=(0.18, 0.06),
    on_click=lambda: toggle_loadout(False),
    ignore_paused=True,
)


_round_loadout_active = False


def toggle_menu(show=None):
    if show is None:
        pause_menu.enabled = not pause_menu.enabled
    else:
        pause_menu.enabled = show
    if pause_menu.enabled:
        loadout_menu.enabled = False
    mouse.locked = not pause_menu.enabled
    application.paused = pause_menu.enabled


def _open_round_loadout():
    global _round_loadout_active
    _round_loadout_active = True
    search_destroy.sd_game.loadout_open = True
    w = local_player.selected_weapon
    ak47_btn.color   = color.azure if w == 'ak47'   else color.gray
    sniper_btn.color = color.azure if w == 'sniper' else color.gray
    loadout_menu.enabled = True


def toggle_loadout(show):
    global _round_loadout_active
    if show:
        w = local_player.selected_weapon
        ak47_btn.color   = color.azure if w == 'ak47'   else color.gray
        sniper_btn.color = color.azure if w == 'sniper' else color.gray
    loadout_menu.enabled = show
    if _round_loadout_active:
        if not show:
            _round_loadout_active = False
            search_destroy.sd_game.loadout_open = False
            local_player.gun.set_weapon(local_player.selected_weapon)
    else:
        pause_menu.enabled = not show


def select_weapon(weapon_type):
    local_player.selected_weapon = weapon_type
    ak47_btn.color   = color.azure if weapon_type == 'ak47'   else color.gray
    sniper_btn.color = color.azure if weapon_type == 'sniper' else color.gray
    if _round_loadout_active:
        toggle_loadout(False)


def input(key):
    if key == 'escape':
        if loadout_menu.enabled:
            toggle_loadout(False)
        else:
            toggle_menu()


# ── Search & Destroy ──────────────────────────────────────────────────────────
search_destroy.sd_game = SearchAndDestroyGame(team_manager)
search_destroy.sd_game.on_round_start = _open_round_loadout
search_destroy.sd_game.start_round()


def update():
    if application.paused:
        return
    for player in team_manager.all_players:
        player.update()
    scoreboard.update()
    search_destroy.sd_game.update()


app.run()
