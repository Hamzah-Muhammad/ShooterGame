# map.py - Sets up the terrain and environment

from ursina import *
import random
from config import MAP_SIZE

def create_map():
    # Create the ground based on the configured map size
    ground = Entity(
        model='plane',
        scale=(MAP_SIZE, 1, MAP_SIZE),
        texture='white_cube',
        texture_scale=(MAP_SIZE, MAP_SIZE),
        color=color.light_gray,
        collider='box'
    )

    # Randomly place obstacles (simple houses/walls)
    num_obstacles = MAP_SIZE // 5  # scale the amount with map size
    for _ in range(num_obstacles):
        size_x = random.uniform(2, 6)
        size_z = random.uniform(2, 6)
        pos_x = random.uniform(-MAP_SIZE / 2 + size_x, MAP_SIZE / 2 - size_x)
        pos_z = random.uniform(-MAP_SIZE / 2 + size_z, MAP_SIZE / 2 - size_z)
        Entity(
            model='cube',
            scale=(size_x, random.uniform(2, 4), size_z),
            position=(pos_x, 1, pos_z),
            color=color.dark_gray,
            collider='box'
        )

    DirectionalLight(y=3, z=3, shadows=True)
    Sky()
