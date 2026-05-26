from ursina import *
from zombies_map import create_zombies_map

_map_data   = None
_local_player = None
_camera_pivot = None


def start_zombies(local_player):
    """
    Called from main.py when the player clicks ZOMBIES.
    Tears down nothing from the S&D session — Zombies runs on a fresh app state.
    Returns the map_data dict for future use by the zombie spawner.
    """
    global _map_data, _local_player, _camera_pivot
    _local_player = local_player
    _map_data     = create_zombies_map()

    spawn = _map_data['player_spawn']
    local_player.position = spawn
    local_player.enabled  = True

    return _map_data


def get_window_spawns():
    return _map_data['window_spawns'] if _map_data else []


def get_door_barriers():
    return _map_data['door_barriers'] if _map_data else []
