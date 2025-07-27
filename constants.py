from ursina import color

TEAM_COLORS = {
    'blue': color.azure,
    'red': color.red
}

SPAWN_POINTS = {
    'blue': [(-15 + i * 10, 1, -15) for i in range(5)],
    'red':  [(-15 + i * 10, 1,  15) for i in range(5)]
}



MAX_SCORE = 20
PLAYER_SPEED = 5
SPRINT_SPEED = 8
CROUCH_HEIGHT = 0.5
RELOAD_TIME = 1.5
AMMO_CAPACITY = 10
BULLET_SPEED = 30
BULLET_LIFETIME = 1.5
MAP_SIZE = 50

