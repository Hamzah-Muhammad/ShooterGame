from ursina import *
import random
from config import MAP_SIZE, BOMB_SITES
import math

# ── Palette ────────────────────────────────────────────────────────────────────
BOMB_WALL_COLOR = color.rgb(110, 75,  45)
BOMB_ROOF_COLOR = color.rgb( 60, 40,  25)
BOMB_DOOR_COLOR = color.rgb( 15, 10,   8)

HOUSE_WALL_COLORS = [
    color.rgb(215, 190, 160),
    color.rgb(185, 160, 130),
    color.rgb(200, 175, 145),
    color.rgb(170, 148, 122),
]
HOUSE_ROOF_COLORS = [
    color.rgb(140, 55, 35),
    color.rgb( 85, 72, 60),
    color.rgb(158, 88, 38),
]

STONE_COLOR  = color.rgb(128, 112,  98)
FENCE_COLOR  = color.rgb(118,  78,  42)
FENCE_POST   = color.rgb( 95,  60,  28)
TRUNK_COLOR  = color.rgb( 75,  48,  22)

ROOF_ANGLE = 32   # degrees for gable roof slope


# ── Bomb-site buildings ────────────────────────────────────────────────────────
def _create_bomb_building(site):
    x, y, z = site
    Entity(model='cube', scale=(8, 5, 8),   position=(x, y+1.5, z),
           color=BOMB_WALL_COLOR, collider='box')
    Entity(model='cube', scale=(9.4, 0.5, 9.4), position=(x, y+4.25, z),
           color=BOMB_ROOF_COLOR, collider='box')
    Entity(model='cube', scale=(1.8, 3.2, 0.4),  position=(x, y+0.1, z-4.2),
           color=BOMB_DOOR_COLOR)


# ── Residential house ──────────────────────────────────────────────────────────
def _create_house(x, z, width=10, depth=9, wall_h=4, rotation_y=0):
    wc = random.choice(HOUSE_WALL_COLORS)
    rc = random.choice(HOUSE_ROOF_COLORS)

    pivot = Entity(position=(x, 0, z), rotation_y=rotation_y)

    # Walls
    Entity(parent=pivot, model='cube', scale=(width, wall_h, depth),
           position=(0, wall_h/2, 0), color=wc, collider='box')

    # Gable roof — two tilted panels meeting at a ridge
    roof_y    = wall_h + (depth/4) * math.tan(math.radians(ROOF_ANGLE))
    panel_len = (depth/2) / math.cos(math.radians(ROOF_ANGLE)) + 0.3
    for z_off, rx in [(-depth/4, -ROOF_ANGLE), (depth/4, ROOF_ANGLE)]:
        Entity(parent=pivot, model='cube',
               scale=(width+0.6, 0.25, panel_len),
               position=(0, roof_y, z_off), rotation_x=rx, color=rc)
    # Ridge cap
    Entity(parent=pivot, model='cube', scale=(width+0.6, 0.28, 0.35),
           position=(0, roof_y+0.12, 0), color=color.rgb(70, 40, 20))

    # Windows (front face, local -z)
    for wx in [-width/4, width/4]:
        Entity(parent=pivot, model='cube', scale=(1.4, 1.2, 0.15),
               position=(wx, wall_h*0.62, -depth/2-0.09),
               color=color.rgb(100, 145, 190))

    # Door
    Entity(parent=pivot, model='cube', scale=(1.4, 2.3, 0.15),
           position=(0, 1.15, -depth/2-0.09), color=color.rgb(85, 52, 28))

    # Random chimney
    if random.random() > 0.45:
        cx = random.uniform(-width/3, width/3)
        Entity(parent=pivot, model='cube', scale=(0.7, 1.8, 0.7),
               position=(cx, roof_y+0.9, 0), color=color.rgb(90, 80, 75))


# ── Tree ───────────────────────────────────────────────────────────────────────
def _create_tree(x, z):
    trunk_h = random.uniform(2.5, 5.0)
    trunk_w = random.uniform(0.28, 0.48)
    Entity(model='cube', scale=(trunk_w, trunk_h, trunk_w),
           position=(x, trunk_h/2, z), color=TRUNK_COLOR)

    g = random.randint(95, 145)
    fc = color.rgb(random.randint(20, 45), g, random.randint(20, 45))

    if random.random() > 0.35:
        # Round deciduous
        r = random.uniform(1.8, 3.0)
        Entity(model='sphere', scale=Vec3(r*2, r*1.8, r*2),
               position=(x, trunk_h + r*0.55, z), color=fc)
    else:
        # Layered pine
        for ry, rs in [(0.0, 2.2), (1.3, 1.7), (2.4, 1.1)]:
            Entity(model='sphere', scale=Vec3(rs*2, rs*1.3, rs*2),
                   position=(x, trunk_h*0.7 + ry, z), color=fc)


# ── Fence line ─────────────────────────────────────────────────────────────────
def _fence(x1, z1, x2, z2, post_spacing=3.5):
    dx, dz = x2-x1, z2-z1
    length  = math.sqrt(dx*dx + dz*dz)
    if length < 0.1:
        return
    angle = math.degrees(math.atan2(dx, dz))
    mx, mz = (x1+x2)/2, (z1+z2)/2

    # Rails
    for ry in [1.25, 0.55]:
        Entity(model='cube', scale=(0.1, 0.09, length),
               position=(mx, ry, mz), rotation_y=angle, color=FENCE_COLOR)

    # Posts
    n = max(2, int(length / post_spacing) + 1)
    for i in range(n):
        t  = i / (n-1) if n > 1 else 0.5
        px = x1 + dx*t
        pz = z1 + dz*t
        Entity(model='cube', scale=(0.13, 1.6, 0.13),
               position=(px, 0.8, pz), color=FENCE_POST)


# ── Stone cover wall ───────────────────────────────────────────────────────────
def _wall(x, z, length, ry=0, height=2.5):
    Entity(model='cube', scale=(length, height, 0.65),
           position=(x, height/2, z), rotation_y=ry,
           color=STONE_COLOR, collider='box')


# ── Main map builder ───────────────────────────────────────────────────────────
def create_map():
    random.seed(42)   # deterministic layout

    # Ground
    Entity(model='plane', scale=(MAP_SIZE, 1, MAP_SIZE),
           texture='grass', texture_scale=(MAP_SIZE//8, MAP_SIZE//8),
           color=color.rgb(55, 115, 50), collider='box')

    # Invisible boundary walls
    half = MAP_SIZE / 2
    wh   = 10
    for pos, scl in [
        ((0,  wh/2,  half), (MAP_SIZE, wh, 1)),
        ((0,  wh/2, -half), (MAP_SIZE, wh, 1)),
        (( half, wh/2, 0),  (1, wh, MAP_SIZE)),
        ((-half, wh/2, 0),  (1, wh, MAP_SIZE)),
    ]:
        Entity(model='cube', scale=scl, position=pos, collider='box', visible=False)

    # Bomb-site buildings
    for site in BOMB_SITES:
        _create_bomb_building(site)

    # Random cover boxes
    for _ in range(MAP_SIZE // 8):
        sx = random.uniform(2, 6)
        sz = random.uniform(2, 6)
        px = random.uniform(-half+sx, half-sx)
        pz = random.uniform(-half+sz, half-sz)
        Entity(model='cube', scale=(sx, random.uniform(2, 4), sz),
               position=(px, 1, pz), color=color.rgb(100, 65, 35), collider='box')

    # Roads between sites
    def _road(a, b):
        s, e = Vec3(a), Vec3(b)
        mid  = (s+e)/2
        lng  = math.sqrt((e.x-s.x)**2 + (e.z-s.z)**2)
        ang  = math.degrees(math.atan2(e.x-s.x, e.z-s.z))
        Entity(model='cube', scale=(4, 0.1, lng),
               position=(mid.x, 0.05, mid.z), rotation=(0, ang, 0),
               color=color.rgb(60, 60, 60))

    for i in range(len(BOMB_SITES)):
        _road(BOMB_SITES[i], BOMB_SITES[(i+1) % len(BOMB_SITES)])

    # ── Houses ────────────────────────────────────────────────────────────────
    # North-west cluster
    _create_house(-155, -72,  width=11, depth=9,  wall_h=4.0, rotation_y=0)
    _create_house(-128, -94,  width=9,  depth=8,  wall_h=3.5, rotation_y=40)
    _create_house(-158, -112, width=10, depth=9,  wall_h=4.0, rotation_y=90)
    # North-east cluster
    _create_house( 130, -72,  width=11, depth=9,  wall_h=4.0, rotation_y=180)
    _create_house( 155, -94,  width=9,  depth=8,  wall_h=3.5, rotation_y=140)
    _create_house( 130, -112, width=10, depth=9,  wall_h=4.0, rotation_y=90)
    # Mid-west cluster
    _create_house(-165,  35,  width=10, depth=8,  wall_h=4.0, rotation_y=0)
    _create_house(-140,  58,  width=9,  depth=8,  wall_h=3.5, rotation_y=270)
    # Mid-east cluster
    _create_house( 140,  35,  width=10, depth=8,  wall_h=4.0, rotation_y=180)
    _create_house( 165,  58,  width=9,  depth=8,  wall_h=3.5, rotation_y=90)
    # South pair (near blue spawn corridor, add visual interest)
    _create_house( -55, -150, width=9,  depth=8,  wall_h=3.5, rotation_y=45)
    _create_house(  55, -150, width=9,  depth=8,  wall_h=3.5, rotation_y=315)
    # North pair (near red spawn corridor)
    _create_house( -60,  155, width=9,  depth=8,  wall_h=3.5, rotation_y=225)
    _create_house(  60,  155, width=9,  depth=8,  wall_h=3.5, rotation_y=135)

    # ── Fences ────────────────────────────────────────────────────────────────
    # NW cluster — two horizontal runs
    _fence(-182, -62, -108, -62)
    _fence(-182, -122, -108, -122)
    # NE cluster
    _fence( 108, -62,  182, -62)
    _fence( 108, -122,  182, -122)
    # Mid-west cluster
    _fence(-188,  22, -112,  22)
    _fence(-188,  70, -112,  70)
    # Mid-east cluster
    _fence( 112,  22,  188,  22)
    _fence( 112,  70,  188,  70)
    # Decorative side fences around south/north houses
    _fence( -80, -142, -80, -162)
    _fence(  80, -142,  80, -162)
    _fence( -80,  142, -80,  162)
    _fence(  80,  142,  80,  162)

    # ── Stone cover walls (mid-map tactical) ──────────────────────────────────
    _wall(   0,  30, 12, ry=0)
    _wall( -42,  10,  8, ry=90)
    _wall(  42,  10,  8, ry=90)
    _wall( -62, -22, 10, ry=45)
    _wall(  62, -22, 10, ry=135)
    _wall(   0, -52, 14, ry=0)
    _wall( -82,  62, 10, ry=0)
    _wall(  82,  62, 10, ry=0)
    _wall( -32,  82,  8, ry=90)
    _wall(  32,  82,  8, ry=90)
    _wall(   0, 112, 16, ry=0)
    _wall( -52, 138, 10, ry=60)
    _wall(  52, 138, 10, ry=120)
    # Corner walls near spawn entries
    _wall(-170, -170,  8, ry=45)
    _wall( 170, -170,  8, ry=135)
    _wall(-170,  170,  8, ry=315)
    _wall( 170,  170,  8, ry=225)

    # ── Trees ─────────────────────────────────────────────────────────────────
    # Dense around NW / NE house clusters
    for _ in range(14):
        _create_tree(random.uniform(-188, -105), random.uniform(-128, -58))
    for _ in range(14):
        _create_tree(random.uniform( 105,  188), random.uniform(-128, -58))
    # Dense around mid-west / mid-east clusters
    for _ in range(8):
        _create_tree(random.uniform(-192, -110), random.uniform(18, 72))
    for _ in range(8):
        _create_tree(random.uniform( 110,  192), random.uniform(18, 72))
    # Near south/north lone houses
    for _ in range(6):
        _create_tree(random.uniform(-90, -20), random.uniform(-165, -135))
        _create_tree(random.uniform( 20,  90), random.uniform(-165, -135))
        _create_tree(random.uniform(-90, -20), random.uniform( 135,  165))
        _create_tree(random.uniform( 20,  90), random.uniform( 135,  165))
    # General scatter — avoid the core combat zone
    for _ in range(40):
        px = random.uniform(-half+5, half-5)
        pz = random.uniform(-half+5, half-5)
        # skip centre combat area and spawn lanes
        if abs(px) < 90 and abs(pz) < 90:
            continue
        _create_tree(px, pz)

    random.seed()   # restore randomness

    # ── Lighting ──────────────────────────────────────────────────────────────
    sun = DirectionalLight()
    sun.look_at(Vec3(1, -3, 1))
    sun.color = color.rgb(255, 235, 190)
    AmbientLight(color=color.rgba(90, 100, 130, 255))

    sky = Sky()
    sky.color = color.rgb(100, 155, 220)
