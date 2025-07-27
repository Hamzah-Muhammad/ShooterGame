# map.py - Sets up the terrain and environment

from ursina import *
import random
from config import MAP_SIZE, BOMB_SITES
import math

def create_map():
    # Create the ground based on the configured map size
    ground = Entity(
        model='plane',
        scale=(MAP_SIZE, 1, MAP_SIZE),
        texture='grass',
        texture_scale=(MAP_SIZE, MAP_SIZE),
        color=color.green,
        collider='box'
    )

    # Create invisible boundary walls to keep players inside the map
    wall_thickness = 1
    wall_height = 5
    half_size = MAP_SIZE / 2
    # North and south walls
    Entity(
        model='cube',
        scale=(MAP_SIZE, wall_height, wall_thickness),
        position=(0, wall_height / 2, half_size - wall_thickness / 2),
        collider='box',
        visible=False
    )
    Entity(
        model='cube',
        scale=(MAP_SIZE, wall_height, wall_thickness),
        position=(0, wall_height / 2, -half_size + wall_thickness / 2),
        collider='box',
        visible=False
    )
    # East and west walls
    Entity(
        model='cube',
        scale=(wall_thickness, wall_height, MAP_SIZE),
        position=(half_size - wall_thickness / 2, wall_height / 2, 0),
        collider='box',
        visible=False
    )
    Entity(
        model='cube',
        scale=(wall_thickness, wall_height, MAP_SIZE),
        position=(-half_size + wall_thickness / 2, wall_height / 2, 0),
        collider='box',
        visible=False
    )

    # Create houses for each bomb site
    for site in BOMB_SITES:
        Entity(
            model='cube',
            scale=(6, 4, 6),
            position=site,
            color=color.rgb(139, 69, 19),
            collider='box'
        )

    # Random obstacles to add cover
    num_obstacles = MAP_SIZE // 8
    for _ in range(num_obstacles):
        size_x = random.uniform(2, 6)
        size_z = random.uniform(2, 6)
        pos_x = random.uniform(-MAP_SIZE / 2 + size_x, MAP_SIZE / 2 - size_x)
        pos_z = random.uniform(-MAP_SIZE / 2 + size_z, MAP_SIZE / 2 - size_z)
        Entity(
            model='cube',
            scale=(size_x, random.uniform(2, 4), size_z),
            position=(pos_x, 1, pos_z),
            color=color.rgb(139, 69, 19),
            collider='box'
        )

    # Roads between sites
    def create_road(start, end):
        start = Vec3(start)
        end = Vec3(end)
        mid = (start + end) / 2
        length = math.sqrt((end.x - start.x) ** 2 + (end.z - start.z) ** 2)
        angle = math.degrees(math.atan2(end.x - start.x, end.z - start.z))
        Entity(
            model='cube',
            scale=(4, 0.1, length),
            position=(mid.x, 0.05, mid.z),
            rotation=(0, angle, 0),
            color=color.gray
        )

    for i in range(len(BOMB_SITES)):
        create_road(BOMB_SITES[i], BOMB_SITES[(i + 1) % len(BOMB_SITES)])

    DirectionalLight(y=3, z=3, shadows=True)
    Sky()
