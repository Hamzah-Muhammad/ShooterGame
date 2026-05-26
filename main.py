from ursina import *

app = Ursina()

window.title      = 'ShooterGame'
window.borderless = True
window.fullscreen = True
window.exit_button.visible = False
window.fps_counter.enabled = True
window.color = color.black
window.size  = (1920, 1080)

_mode        = None   # '1v1' or 'zombies'
_game_started = False

# S&D objects — created only when 1v1 mode is chosen
_sd_team_manager = None
_sd_local_player = None
_sd_scoreboard   = None
_sd_game         = None
_pause_menu      = None
_loadout_menu    = None
_ak47_btn        = None
_sniper_btn      = None
_round_loadout_active = False


# ── Main menu ─────────────────────────────────────────────────────────────────
_main_menu = Entity(parent=camera.ui, enabled=True, ignore_paused=True)

Entity(
    model='quad', parent=_main_menu, scale=(2, 2),
    color=color.rgba32(0, 0, 0, 240), ignore_paused=True,
)
Text(
    text='SHOOTER', parent=_main_menu, position=(0, 0.28), origin=(0, 0),
    scale=7, color=color.white, ignore_paused=True,
)
Text(
    text='SELECT GAME MODE', parent=_main_menu, position=(0, 0.12), origin=(0, 0),
    scale=1.8, color=color.light_gray, ignore_paused=True,
)
Button(
    text='1v1  —  Search & Destroy', parent=_main_menu, position=(0, -0.02),
    scale=(0.42, 0.09), color=color.azure,
    on_click=lambda: _launch_1v1(), ignore_paused=True,
)
Button(
    text='ZOMBIES', parent=_main_menu, position=(0, -0.15),
    scale=(0.42, 0.09), color=color.rgb32(80, 160, 80),
    on_click=lambda: _launch_zombies(), ignore_paused=True,
)
Button(
    text='QUIT', parent=_main_menu, position=(0, -0.28),
    scale=(0.42, 0.09), color=color.rgb32(60, 60, 60),
    on_click=application.quit, ignore_paused=True,
)
Text(
    text='WASD: move   Mouse: aim   LMB: shoot   RMB: scope\n'
         'Space: jump   Ctrl: crouch   Shift: sprint\n'
         'R: reload   4: plant/defuse   Esc: pause',
    parent=_main_menu, position=(0, -0.42), origin=(0, 0),
    scale=1.1, color=color.rgb32(110, 110, 110), ignore_paused=True,
)

application.paused = True
mouse.locked = False


# ── 1v1 Search & Destroy setup ────────────────────────────────────────────────
def _launch_1v1():
    global _mode, _game_started
    global _sd_team_manager, _sd_local_player, _sd_scoreboard, _sd_game
    global _pause_menu, _loadout_menu, _ak47_btn, _sniper_btn

    _mode = '1v1'
    _hide_main_menu()

    from map import create_map
    from teams import team_manager
    from scoreboard import Scoreboard
    from search_destroy import SearchAndDestroyGame
    import search_destroy as _sd_mod

    create_map()
    team_manager.spawn_teams()
    _sd_team_manager = team_manager
    _sd_local_player = next(p for p in team_manager.all_players if p.is_local)
    _sd_scoreboard   = Scoreboard(team_manager)

    # Pause menu
    _pause_menu = Entity(parent=camera.ui, enabled=False, ignore_paused=True)
    Panel(parent=_pause_menu, scale=(0.4, 0.38),
          color=color.rgba32(0, 0, 0, 150), ignore_paused=True)
    Button(text='Resume',     parent=_pause_menu, position=(0,  0.10),
           on_click=lambda: _toggle_pause(False), ignore_paused=True)
    Button(text='Loadout',    parent=_pause_menu, position=(0,  0.00),
           on_click=lambda: _toggle_loadout(True), ignore_paused=True)
    Button(text='Close Game', parent=_pause_menu, position=(0, -0.10),
           on_click=application.quit, ignore_paused=True)

    # Loadout menu
    _loadout_menu = Entity(parent=camera.ui, enabled=False, ignore_paused=True)
    Panel(parent=_loadout_menu, scale=(0.58, 0.52),
          color=color.rgba32(0, 0, 0, 185), ignore_paused=True)
    Text(text='LOADOUT', parent=_loadout_menu, position=(0, 0.20), origin=(0, 0),
         scale=2.4, color=color.white, ignore_paused=True)
    Text(text='Choice applies at the start of the next round',
         parent=_loadout_menu, position=(0, 0.12), origin=(0, 0),
         scale=1.1, color=color.light_gray, ignore_paused=True)

    _ak47_btn = Button(
        text='AK-47', parent=_loadout_menu, position=(-0.13, 0.02),
        scale=(0.22, 0.09), color=color.azure, ignore_paused=True,
        on_click=lambda: _select_weapon('ak47'))
    _sniper_btn = Button(
        text='L96A1', parent=_loadout_menu, position=(0.13, 0.02),
        scale=(0.22, 0.09), color=color.gray, ignore_paused=True,
        on_click=lambda: _select_weapon('sniper'))

    Text(text='Full-auto  •  30 rounds', parent=_loadout_menu,
         position=(-0.13, -0.06), origin=(0, 0), scale=1.0,
         color=color.light_gray, ignore_paused=True)
    Text(text='Bolt-action  •  5 rounds  •  1-shot kill', parent=_loadout_menu,
         position=(0.13, -0.06), origin=(0, 0), scale=1.0,
         color=color.light_gray, ignore_paused=True)
    Text(text='Hold RMB to scope in', parent=_loadout_menu,
         position=(0.13, -0.11), origin=(0, 0), scale=0.9,
         color=color.rgb32(160, 200, 160), ignore_paused=True)
    Button(text='Back', parent=_loadout_menu, position=(0, -0.19),
           scale=(0.18, 0.06), on_click=lambda: _toggle_loadout(False),
           ignore_paused=True)

    # S&D game instance
    _sd_game = SearchAndDestroyGame(team_manager)
    _sd_mod.sd_game = _sd_game
    _sd_game.on_round_start = _open_round_loadout

    application.paused = False
    _game_started = True
    _sd_game.start_round()


def _toggle_pause(show=None):
    if _pause_menu is None:
        return
    if show is None:
        _pause_menu.enabled = not _pause_menu.enabled
    else:
        _pause_menu.enabled = show
    if _pause_menu.enabled:
        _loadout_menu.enabled = False
    mouse.locked = not _pause_menu.enabled
    application.paused = _pause_menu.enabled


def _open_round_loadout():
    global _round_loadout_active
    _round_loadout_active = True
    _sd_game.loadout_open = True
    w = _sd_local_player.selected_weapon
    _ak47_btn.color   = color.azure if w == 'ak47'   else color.gray
    _sniper_btn.color = color.azure if w == 'sniper' else color.gray
    _loadout_menu.enabled = True
    mouse.locked = False


def _toggle_loadout(show):
    global _round_loadout_active
    if show:
        w = _sd_local_player.selected_weapon
        _ak47_btn.color   = color.azure if w == 'ak47'   else color.gray
        _sniper_btn.color = color.azure if w == 'sniper' else color.gray
    _loadout_menu.enabled = show
    if _round_loadout_active:
        if not show:
            _round_loadout_active = False
            _sd_game.loadout_open = False
            _sd_local_player.gun.set_weapon(_sd_local_player.selected_weapon)
            mouse.locked = True
    else:
        _pause_menu.enabled = not show


def _select_weapon(weapon_type):
    _sd_local_player.selected_weapon = weapon_type
    _ak47_btn.color   = color.azure if weapon_type == 'ak47'   else color.gray
    _sniper_btn.color = color.azure if weapon_type == 'sniper' else color.gray
    if _round_loadout_active:
        _toggle_loadout(False)


# ── Zombies setup ─────────────────────────────────────────────────────────────
def _launch_zombies():
    global _mode, _game_started

    _mode = 'zombies'
    _hide_main_menu()

    import zombies_mode
    zombies_mode.start()

    application.paused = False
    mouse.locked = True
    _game_started = True


# ── Shared helpers ────────────────────────────────────────────────────────────
def _hide_main_menu():
    global _main_menu
    if _main_menu:
        destroy(_main_menu)
        _main_menu = None


# ── Input / Update ────────────────────────────────────────────────────────────
def input(key):
    if not _game_started:
        return
    if _mode == '1v1':
        if key == 'escape':
            if _loadout_menu and _loadout_menu.enabled:
                _toggle_loadout(False)
            else:
                _toggle_pause()
    elif _mode == 'zombies':
        import zombies_mode
        zombies_mode.handle_input(key)


def update():
    if application.paused:
        return
    if _mode == '1v1':
        for player in _sd_team_manager.all_players:
            player.update()
        _sd_scoreboard.update()
        _sd_game.update()
    elif _mode == 'zombies':
        import zombies_mode
        zombies_mode.update()


app.run()
