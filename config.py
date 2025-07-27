from ursina import color

# General game settings
PLAYER_SCALE = 1.5
# Size of the square map.  This is used for ground generation
# and to position spawn points near the edges.
MAP_SIZE = 100
SCORE_LIMIT = 10
GAME_RUNNING = True
JUMP_HEIGHT = 5
MAX_HEALTH = 100

# Player settings
PLAYER_SPEED = 5
SPRINT_SPEED = 8
CROUCH_HEIGHT = 0.5
RELOAD_TIME = 1.5
AMMO_CAPACITY = 10
PLAYER_JUMP_HEIGHT = 2.5    # Adjust as needed for your game

# Bullet settings
BULLET_SPEED = 20
BULLET_LIFETIME = 3
BULLET_DAMAGE = 25

# Colors
TEAM_COLORS = {
    'blue': color.azure,
    'red': color.red,
}

# Spawn points for blue and red teams. They are spread along the
# X axis near the opposite edges of the map.
SPAWN_SPACING = MAP_SIZE // 5
SPAWN_OFFSET = -MAP_SIZE // 2 + SPAWN_SPACING // 2
SPAWN_Z_OFFSET = MAP_SIZE // 2 - SPAWN_SPACING // 2

SPAWN_POINTS = {
    'blue': [(SPAWN_OFFSET + i * SPAWN_SPACING, 1, -SPAWN_Z_OFFSET) for i in range(5)],
    'red':  [(SPAWN_OFFSET + i * SPAWN_SPACING, 1,  SPAWN_Z_OFFSET) for i in range(5)]
}

# Additional game constants
MAX_SCORE = 20

BLUE_NAMES = ['Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo']
RED_NAMES = ['Viper', 'Cobra', 'Falcon', 'Ghost', 'Reaper']
