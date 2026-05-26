from ursina import *
import random
import zombies_points as zp
import gun as gun_mod

# ── Public state (read by gun.py and zombie.py) ───────────────────────────────
live_zombies  = []   # Zombie instances currently alive in the world

# ── Private state ─────────────────────────────────────────────────────────────
_local_player = None
_map_data     = None
_buy_prompt   = None
_nearby_door  = None

# Round / wave system
_round_number       = 0
_round_state        = 'idle'   # 'spawning' | 'intermission'
_spawn_queue        = 0        # zombies yet to enter this round
_spawn_timer        = 0.0
_intermission_timer = 0.0
_INTERMISSION_DUR   = 6.0     # seconds between rounds

# HUD elements created in start()
_hud_round  = None    # persistent round counter (top-right)
_hud_count  = None    # persistent zombie counter (below round)
_BUY_RADIUS = 4.0


# ── Lifecycle ─────────────────────────────────────────────────────────────────
def start():
    global _local_player, _map_data, _buy_prompt, _nearby_door
    global live_zombies, _round_number, _round_state
    global _hud_round, _hud_count

    live_zombies.clear()
    gun_mod.zombie_targets = live_zombies   # share list reference with gun

    _round_number = 0
    _round_state  = 'idle'

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

    # Points HUD (bottom-left via zombies_points)
    zp.init_hud()

    # Round counter — top-right
    _hud_round = Text(
        text     = '',
        position = (0.72, 0.44),
        origin   = (0.5, 0),
        scale    = 1.8,
        color    = color.white,
        parent   = camera.ui,
    )
    # Zombie count — below round counter
    _hud_count = Text(
        text     = '',
        position = (0.72, 0.38),
        origin   = (0.5, 0),
        scale    = 1.4,
        color    = color.light_gray,
        parent   = camera.ui,
    )
    # Door buy prompt — bottom-centre
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
    _start_round()


def update():
    if _local_player is None:
        return

    _local_player.update()
    zp.update(time.dt)
    _check_door_proximity()
    _update_round_logic()
    _update_hud()

    for z in list(live_zombies):
        z.update()


def handle_input(key):
    if key == 'f':
        _try_open_door()
    elif key == 'escape':
        application.quit()


# ── Round / wave system ───────────────────────────────────────────────────────
def _start_round():
    global _round_number, _spawn_queue, _spawn_timer, _round_state

    _round_number += 1
    count         = 6 + (_round_number - 1) * 2   # R1=6, R2=8, R3=10 …
    _spawn_queue  = count
    _spawn_timer  = 0.0
    _round_state  = 'spawning'

    _show_round_banner(_round_number)


def _show_round_banner(n):
    banner = Text(
        text     = f'ROUND  {n}',
        position = (0, 0.12),
        origin   = (0, 0),
        scale    = 5,
        color    = color.white,
        parent   = camera.ui,
    )
    banner.animate('color', color.rgba(1, 1, 1, 0), duration=3.0)
    destroy(banner, delay=3.5)


def _update_round_logic():
    global _spawn_queue, _spawn_timer, _round_state, _intermission_timer

    if _round_state == 'spawning':
        # Tick spawn timer
        if _spawn_queue > 0:
            _spawn_timer -= time.dt
            if _spawn_timer <= 0:
                _spawn_zombie()
                _spawn_queue -= 1
                _spawn_timer  = _spawn_interval()

        # Check if round is over
        if _spawn_queue == 0 and len(live_zombies) == 0:
            _round_state        = 'intermission'
            _intermission_timer = _INTERMISSION_DUR

    elif _round_state == 'intermission':
        _intermission_timer -= time.dt
        if _intermission_timer <= 0:
            _start_round()


def _spawn_interval():
    """Seconds between spawns — shrinks as rounds increase, min 0.5 s."""
    return max(0.5, 2.0 - (_round_number - 1) * 0.1)


def _spawn_zombie():
    from zombie import Zombie

    spawns = _map_data.get('window_spawns', [])
    # Use only ground-floor windows (y ≈ 1) for now
    ground = [s for s in spawns if -1 < s.y < 3]
    if not ground:
        ground = spawns
    if not ground:
        return

    pos = random.choice(ground)

    # Scale difficulty with round
    hp    = int(150 * (1.1 ** (_round_number - 1)))
    speed = min(2.0 + (_round_number - 1) * 0.15, 4.5)

    z = Zombie(
        position      = pos,
        target_player = _local_player,
        max_health    = hp,
        speed         = speed,
        on_death      = _on_zombie_death,
    )
    live_zombies.append(z)


def _on_zombie_death(zombie):
    if zombie in live_zombies:
        live_zombies.remove(zombie)


# ── HUD refresh ───────────────────────────────────────────────────────────────
def _update_hud():
    if _hud_round:
        _hud_round.text = f'ROUND  {_round_number}'

    if _hud_count:
        total = _spawn_queue + len(live_zombies)
        if _round_state == 'intermission':
            t = max(0, int(_intermission_timer) + 1)
            _hud_count.text  = f'Next round in {t}s'
            _hud_count.color = color.yellow
        else:
            _hud_count.text  = f'Zombies: {total}'
            _hud_count.color = color.light_gray


# ── Door interaction ──────────────────────────────────────────────────────────
def _check_door_proximity():
    global _nearby_door

    if _local_player is None or _map_data is None:
        return

    ppos    = _local_player.position
    closest = None
    min_d   = _BUY_RADIUS

    for barrier in _map_data['door_barriers']:
        if barrier['open']:
            continue
        dist = (ppos - barrier['entity'].position).length()
        if dist < min_d:
            min_d   = dist
            closest = barrier

    _nearby_door = closest

    if closest is None:
        _buy_prompt.enabled = False
        return

    can_afford = zp.points >= closest['cost']
    _buy_prompt.enabled = True
    _buy_prompt.text    = f"[F]  Open door  —  {closest['cost']:,} pts"
    _buy_prompt.color   = color.yellow if can_afford else color.rgb32(220, 70, 70)


def _try_open_door():
    if _nearby_door is None:
        return
    cost = _nearby_door['cost']
    if not zp.spend_points(cost):
        if _buy_prompt:
            _buy_prompt.color = color.red
        return

    destroy(_nearby_door['entity'])
    _nearby_door['entity'] = None
    _nearby_door['open']   = True

    if _buy_prompt:
        _buy_prompt.text    = f'Door opened!  (-{cost:,} pts)'
        _buy_prompt.color   = color.lime
        invoke(lambda: setattr(_buy_prompt, 'enabled', False), delay=1.5)
