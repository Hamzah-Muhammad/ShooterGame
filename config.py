from ursina import Vec3, color

# General game settings
PLAYER_SCALE = 1.5
MAP_SIZE = 50
SCORE_LIMIT = 10
GAME_RUNNING = True

# Bullet settings
BULLET_SPEED = 20
BULLET_LIFETIME = 3

# Colors
TEAM_COLORS = {
    'blue': color.azure,
    'red': color.red,
}

# Spawn points for blue and red teams (within the 50x50 map bounds)
SPAWN_POINTS = {
    'blue': [
        Vec3(-15, 0, -15),
        Vec3(-10, 0, -20),
        Vec3(-5, 0, -10),
        Vec3(-20, 0, -5),
        Vec3(-10, 0, -15),
    ],
    'red': [
        Vec3(15, 0, 15),
        Vec3(10, 0, 20),
        Vec3(5, 0, 10),
        Vec3(20, 0, 5),
        Vec3(10, 0, 15),
    ]
}
