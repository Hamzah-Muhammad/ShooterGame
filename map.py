# map.py - Sets up the terrain and environment

"""Map creation utilities used by the shooter demo.

The original version of this module produced a very basic arena.  To make the
game feel closer to classic tactical shooters such as Counter‑Strike we add a
few visual flourishes and clean up some of the repetitive code.  Textures for
buildings and obstacles, a basic asphalt road and a warm sunset skybox all
help the world feel less like a prototype.
"""

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

    # Create invisible boundary walls to keep players inside the map.  The
    # previous implementation duplicated very similar ``Entity`` definitions
    # four times; iterating over the configurations keeps the file compact and
    # easier to modify.
    wall_thickness = 1
    wall_height = 5
    half_size = MAP_SIZE / 2
    wall_configs = [
        # North and south walls
        ((MAP_SIZE, wall_height, wall_thickness), (0, wall_height / 2, half_size - wall_thickness / 2)),
        ((MAP_SIZE, wall_height, wall_thickness), (0, wall_height / 2, -half_size + wall_thickness / 2)),
        # East and west walls
        ((wall_thickness, wall_height, MAP_SIZE), (half_size - wall_thickness / 2, wall_height / 2, 0)),
        ((wall_thickness, wall_height, MAP_SIZE), (-half_size + wall_thickness / 2, wall_height / 2, 0)),
    ]
    for scale, position in wall_configs:
        Entity(model='cube', scale=scale, position=position, collider='box', visible=False)

    # Create houses for each bomb site.  Using a simple ``brick`` texture helps
    # them stand out against the terrain.
    for site in BOMB_SITES:
        Entity(
            model='cube',
            scale=(6, 4, 6),
            position=site,
            texture='brick',
            color=color.rgb(160, 82, 45),
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
            texture='brick',
            color=color.rgb(120, 70, 40),
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
            texture='white_cube',
            color=color.rgb(50, 50, 50)
        )

    for i in range(len(BOMB_SITES)):
        create_road(BOMB_SITES[i], BOMB_SITES[(i + 1) % len(BOMB_SITES)])

    # A subtle ambient light and sunset skybox make the level feel warmer and
    # closer to a real outdoor environment.
    DirectionalLight(y=3, z=3, shadows=True)
    AmbientLight(color=color.rgb(100, 100, 100))
    Sky(texture='sky_sunset')
