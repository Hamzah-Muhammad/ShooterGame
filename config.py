from ursina import color

# General game settings
PLAYER_SCALE = 1.5
MAP_SIZE = 400

# Search & Destroy settings
ROUND_LIMIT = 5
ROUND_TIME = 115         # seconds (1:55 per round; defenders win if expires with no plant)
PLANT_TIME = 3.0         # seconds to hold '4' to plant bomb
DEFUSE_TIME = 10.0       # seconds to hold '4' to defuse bomb

# Player settings
PLAYER_SPEED = 5
SPRINT_SPEED = 8
CROUCH_SPEED = 2.5
RELOAD_TIME = 1.5
AMMO_CAPACITY = 30
PLAYER_JUMP_HEIGHT = 8
GRAVITY = -20
FIRE_RATE = 0.1          # seconds between shots (10 rps — CS-like auto rate)

# Bullet / hitscan settings
BULLET_DAMAGE = 25
HEADSHOT_MULTIPLIER = 4.0     # damage multiplier on head hits
BULLET_BASE_SPREAD = 0.5      # degrees — standing still, not shooting
BULLET_MOVE_SPREAD = 5.0      # degrees added when moving
BULLET_RECOIL_PER_SHOT = 1.0  # degrees of recoil added per shot fired
BULLET_RECOIL_MAX = 6.0       # degrees — maximum accumulated recoil
BULLET_RECOIL_RECOVERY = 4.0  # degrees recovered per second
AI_EXTRA_SPREAD = 3.0         # extra degrees for AI to balance difficulty
CROUCH_SPREAD_MULT = 0.35     # crouch reduces spread to 35% of base

# Bomb settings
BOMB_SITE_A = (-120, 1, 120)
BOMB_SITE_B = (120, 1, 120)
BOMB_SITE_C = (0, 1, -120)
BOMB_SITES = [BOMB_SITE_A, BOMB_SITE_B, BOMB_SITE_C]
BOMB_TIMER = 40
BOMB_PICKUP_RADIUS = 1.5
BOMB_PLANT_RADIUS = 2
BOMB_DEFUSE_RADIUS = 2
BOMB_BLAST_RADIUS = 18        # explosion damage radius (units)
BOMB_BLAST_DAMAGE = 250       # max damage at center; linear falloff to 0 at radius
ROUND_OVER_DURATION = 3.0     # seconds banner shown between rounds

# Colors
TEAM_COLORS = {
    'blue': color.azure,
    'red': color.red,
}

SPAWN_SPACING = MAP_SIZE // 5
SPAWN_OFFSET = -MAP_SIZE // 2 + SPAWN_SPACING // 2
SPAWN_Z_OFFSET = MAP_SIZE // 2 - SPAWN_SPACING // 2

SPAWN_POINTS = {
    'blue': [(SPAWN_OFFSET + i * SPAWN_SPACING, 1, -SPAWN_Z_OFFSET) for i in range(5)],
    'red':  [(SPAWN_OFFSET + i * SPAWN_SPACING, 1,  SPAWN_Z_OFFSET) for i in range(5)]
}

BLUE_NAMES = ['Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo']
RED_NAMES = ['Viper', 'Cobra', 'Falcon', 'Ghost', 'Reaper']
