from ursina import *
import zombies_points as zp

_local_player = None
_map_data     = None
_buy_prompt   = None   # HUD text shown near purchasable doors
_nearby_door  = None   # barrier dict currently in range

_BUY_RADIUS = 4.0      # units — how close to stand to interact


def start():
    global _local_player, _map_data, _buy_prompt, _nearby_door

    from zombies_map import create_zombies_map
    from player import Player

    _map_data = create_zombies_map()
    spawn     = _map_data['player_spawn']

    _local_player = Player(
        team_color  = color.azure,
        spawn_point = (spawn.x, spawn.y, spawn.z),
        is_local    = True,
        name        = 'Player',
    )

    # Points HUD
    zp.init_hud()

    # Buy prompt — bottom-centre, hidden until near a door
    _buy_prompt = Text(
        text     = '',
        position = (0, -0.40),
        origin   = (0, 0),
        scale    = 1.6,
        color    = color.yellow,
        parent   = camera.ui,
        enabled  = False,
    )

    _nearby_door = None


def update():
    if _local_player is None:
        return
    _local_player.update()
    zp.update(time.dt)
    _check_door_proximity()


def handle_input(key):
    if key == 'f':
        _try_open_door()
    elif key == 'escape':
        application.quit()


# ── Door interaction ──────────────────────────────────────────────────────────
def _check_door_proximity():
    global _nearby_door

    if _local_player is None or _map_data is None:
        return

    ppos    = _local_player.position
    closest = None
    closest_dist = _BUY_RADIUS

    for barrier in _map_data['door_barriers']:
        if barrier['open']:
            continue
        e    = barrier['entity']
        dist = (ppos - e.position).length()
        if dist < closest_dist:
            closest_dist = dist
            closest      = barrier

    _nearby_door = closest

    if closest is None:
        _buy_prompt.enabled = False
        return

    cost        = closest['cost']
    can_afford  = zp.points >= cost
    _buy_prompt.enabled = True
    _buy_prompt.text    = f'[F]  Open door  —  {cost:,} pts'
    _buy_prompt.color   = color.yellow if can_afford else color.rgb32(220, 70, 70)


def _try_open_door():
    if _nearby_door is None:
        return

    cost = _nearby_door['cost']
    if not zp.spend_points(cost):
        # Flash the prompt red to signal insufficient funds
        if _buy_prompt:
            _buy_prompt.color = color.red
        return

    # Remove the physical barrier
    destroy(_nearby_door['entity'])
    _nearby_door['entity'] = None
    _nearby_door['open']   = True

    # Brief "door opened" confirmation
    if _buy_prompt:
        _buy_prompt.text    = f'Door opened!  (-{cost:,} pts)'
        _buy_prompt.color   = color.lime
        invoke(lambda: setattr(_buy_prompt, 'enabled', False), delay=1.5)
