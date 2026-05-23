from ursina import *
import random
from config import MAP_SIZE, BOMB_SITES
import math

WALL_COLOR  = color.rgb(110, 75, 45)
ROOF_COLOR  = color.rgb(60, 40, 25)
DOOR_COLOR  = color.rgb(15, 10, 8)

def _create_building(site):
    x, y, z = site
    # Walls
    Entity(model='cube', scale=(8, 5, 8), position=(x, y + 1.5, z),
           color=WALL_COLOR, collider='box')
    # Roof slab
    Entity(model='cube', scale=(9.4, 0.5, 9.4), position=(x, y + 4.25, z),
           color=ROOF_COLOR, collider='box')
    # Door opening (dark inset on south face)
    Entity(model='cube', scale=(1.8, 3.2, 0.4), position=(x, y + 0.1, z - 4.2),
           color=DOOR_COLOR)

def create_map():
    # Ground
    Entity(
        model='plane',
        scale=(MAP_SIZE, 1, MAP_SIZE),
        texture='grass',
        texture_scale=(MAP_SIZE // 8, MAP_SIZE // 8),
        color=color.rgb(55, 115, 50),
        collider='box'
    )

    # Invisible boundary walls
    wall_thickness = 1
    wall_height = 10
    half = MAP_SIZE / 2
    for pos, scl in [
        ((0,          wall_height/2,  half),           (MAP_SIZE, wall_height, wall_thickness)),
        ((0,          wall_height/2, -half),            (MAP_SIZE, wall_height, wall_thickness)),
        (( half,      wall_height/2,  0),               (wall_thickness, wall_height, MAP_SIZE)),
        ((-half,      wall_height/2,  0),               (wall_thickness, wall_height, MAP_SIZE)),
    ]:
        Entity(model='cube', scale=scl, position=pos, collider='box', visible=False)

    # Detailed bomb-site buildings
    for site in BOMB_SITES:
        _create_building(site)

    # Random cover obstacles
    num_obstacles = MAP_SIZE // 8
    for _ in range(num_obstacles):
        sx = random.uniform(2, 6)
        sz = random.uniform(2, 6)
        px = random.uniform(-MAP_SIZE / 2 + sx, MAP_SIZE / 2 - sx)
        pz = random.uniform(-MAP_SIZE / 2 + sz, MAP_SIZE / 2 - sz)
        Entity(
            model='cube',
            scale=(sx, random.uniform(2, 4), sz),
            position=(px, 1, pz),
            color=color.rgb(100, 65, 35),
            collider='box'
        )

    # Roads between sites
    def create_road(start, end):
        s, e = Vec3(start), Vec3(end)
        mid = (s + e) / 2
        length = math.sqrt((e.x - s.x) ** 2 + (e.z - s.z) ** 2)
        angle = math.degrees(math.atan2(e.x - s.x, e.z - s.z))
        Entity(model='cube', scale=(4, 0.1, length),
               position=(mid.x, 0.05, mid.z), rotation=(0, angle, 0),
               color=color.rgb(60, 60, 60))

    for i in range(len(BOMB_SITES)):
        create_road(BOMB_SITES[i], BOMB_SITES[(i + 1) % len(BOMB_SITES)])

    # Lighting
    sun = DirectionalLight()
    sun.look_at(Vec3(1, -3, 1))
    sun.color = color.rgb(255, 235, 190)

    AmbientLight(color=color.rgba(90, 100, 130, 255))

    sky = Sky()
    sky.color = color.rgb(100, 155, 220)
