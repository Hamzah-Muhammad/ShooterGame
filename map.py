# map.py - Sets up the terrain and environment

"""Map creation utilities used by the shooter demo.

The original version of this module produced a very basic arena.  To make the
game feel closer to classic tactical shooters such as Counter‑Strike we add a
few visual flourishes and clean up some of the repetitive code.  Textures for
buildings and obstacles, a basic asphalt road and a warm sunset skybox all
help the world feel less like a prototype.
"""

from ursina import *
from config import MAP_SIZE, BOMB_SITES
import math
import itertools

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

    # Utility functions to add town features
    house_colors = [
        color.rgb(160, 82, 45),   # warm brown
        color.rgb(210, 180, 140), # tan
        color.rgb(200, 100, 100), # red
        color.rgb(100, 100, 200), # blue
        color.rgb(220, 220, 220)  # light gray
    ]
    color_cycle = itertools.cycle(house_colors)

    def create_house(position, scale=(6, 4, 6)):
        return Entity(
            model='cube',
            scale=scale,
            position=position,
            texture='brick',
            color=next(color_cycle),
            collider='box'
        )

    def create_lamppost(position):
        Entity(model='cube', scale=(0.3, 4, 0.3), position=(position.x, 2, position.z), color=color.rgb(80, 80, 80))
        PointLight(position=(position.x, 4, position.z), color=color.rgb(255, 240, 200), shadows=True)

    def create_tree(position):
        Entity(model='cube', scale=(1, 4, 1), position=(position[0], 2, position[2]), color=color.rgb(101, 67, 33))
        Entity(model='sphere', scale=3, position=(position[0], 5, position[2]), color=color.rgb(34, 139, 34))

    # Create houses for each bomb site to form key town buildings
    for site in BOMB_SITES:
        create_house(site)

    # Deterministic obstacles to add cover
    obstacle_configs = [
        ((5, 3, 5), (-80, 1, 80)),
        ((7, 2, 4), (80, 1, 80)),
        ((4, 3, 6), (-80, 1, -80)),
        ((6, 2, 5), (80, 1, -80)),
        ((8, 3, 8), (0, 1, 0)),
    ]
    for scale, position in obstacle_configs:
        Entity(
            model='cube',
            scale=scale,
            position=position,
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
        # Populate the street with houses and lamps
        direction = (end - start).normalized()
        side_offset = Vec3(-direction.z, 0, direction.x) * 10
        steps = int(length // 20)
        for i in range(1, steps):
            pos = start + direction * (i * 20)
            create_house(pos + side_offset)
            create_house(pos - side_offset)
            create_lamppost(pos)

    for i in range(len(BOMB_SITES)):
        create_road(BOMB_SITES[i], BOMB_SITES[(i + 1) % len(BOMB_SITES)])

    # Scatter trees evenly around the town for a bit of greenery
    tree_spacing = 40
    perimeter = int(MAP_SIZE // tree_spacing)
    for i in range(perimeter):
        offset = -half_size + 20 + i * tree_spacing
        create_tree((offset, 0, half_size - 20))
        create_tree((offset, 0, -half_size + 20))
        create_tree((half_size - 20, 0, offset))
        create_tree((-half_size + 20, 0, offset))

    # A subtle ambient light and sunset skybox make the level feel warmer and
    # closer to a real outdoor environment.
    DirectionalLight(y=3, z=3, shadows=True)
    AmbientLight(color=color.rgb(100, 100, 100))
    Sky(texture='sky_sunset')
