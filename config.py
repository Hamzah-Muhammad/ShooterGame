from ursina import color

# General game settings
PLAYER_SCALE = 1.5
MAP_SIZE = 50
SCORE_LIMIT = 10
GAME_RUNNING = True

# Player settings
PLAYER_SPEED = 5
SPRINT_SPEED = 8
CROUCH_HEIGHT = 0.5
RELOAD_TIME = 1.5
AMMO_CAPACITY = 10

# Bullet settings
BULLET_SPEED = 20
BULLET_LIFETIME = 3

# Colors
TEAM_COLORS = {
    'blue': color.azure,
    'red': color.red,
}

# Spawn points for blue and red teams (within the 50x50 map bounds)
# Use the positions originally defined in ``constants.py``
SPAWN_POINTS = {
    'blue': [(-15 + i * 10, 1, -15) for i in range(5)],
    'red':  [(-15 + i * 10, 1,  15) for i in range(5)]
}

# Additional game constants
MAX_SCORE = 20
