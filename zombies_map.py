from ursina import *

# ── Material palette ──────────────────────────────────────────────────────────
_BRICK   = color.rgb32(130,  75,  55)
_PLASTER = color.rgb32(220, 210, 190)
_WOOD    = color.rgb32(101,  67,  33)
_STONE   = color.rgb32( 88,  82,  76)
_STONE_F = color.rgb32( 65,  60,  55)
_ROOF    = color.rgb32( 42,  42,  52)
_PARAPET = color.rgb32(110,  70,  50)
_WIN_FRM = color.rgb32( 55,  38,  18)
_WIN_GLS = color.rgba32(80, 130, 180, 80)
_BARRIER = color.rgb32( 90,  58,  28)
_STAIR   = color.rgb32( 95,  72,  48)
_DIRT    = color.rgb32( 60,  48,  35)
_CEIL    = color.rgb32(200, 192, 175)

FH = 5.0    # floor height per level
WT = 0.5    # wall thickness

# Mansion x/z extents
X1, X2 = -30.0, 30.0
Z1, Z2 = -25.0, 25.0

# Public data filled by create_zombies_map()
window_spawns = []   # Vec3 just outside each window at ground-entry height
door_barriers = []   # list of {'entity': Entity, 'cost': int, 'open': bool}
player_spawn  = Vec3(0, 1.2, -20)


# ── Geometry helpers ──────────────────────────────────────────────────────────
def _b(pos, sc, col, coll=True):
    return Entity(model='cube', position=pos, scale=sc, color=col,
                  collider='box' if coll else None)


def _slab(cx, y, cz, w, d, col, thick=0.3):
    _b((cx, y, cz), (w, thick, d), col)


def _solid(cx, y_fl, cz, w, h, d, col):
    _b((cx, y_fl + h / 2, cz), (w, h, d), col)


def _ramp(cx, y_mid, cz, w, h, d, rx, col=_STAIR):
    """Rotated slab used as a staircase ramp."""
    _b((cx, y_mid, cz), (w, h, d), col).rotation_x = rx


# Build a wall panel along X (fixed z) with optional window openings.
# wins = list of (win_center_x, win_w, win_y_off, win_h) — win_y_off from y_fl.
def _xwall(x1, x2, z, y_fl, wins=(), col=_BRICK, thick=WT):
    h    = FH
    segs = _slice1d(x1, x2, [(w[0]-w[1]/2, w[0]+w[1]/2) for w in wins])
    for sx1, sx2 in segs:
        cx = (sx1 + sx2) / 2
        _solid(cx, y_fl, z, sx2 - sx1, h, thick, col)

    for wx, ww, wy, wh in wins:
        # Below window
        if wy > 0:
            _solid(wx, y_fl, z, ww, wy, thick, col)
        # Above window
        above = h - wy - wh
        if above > 0:
            _solid(wx, y_fl + wy + wh, z, ww, above, thick, col)
        # Frame
        _b((wx, y_fl + wy + wh/2, z), (ww + 0.22, wh + 0.22, thick + 0.18), _WIN_FRM, coll=False)
        # Glass
        _b((wx, y_fl + wy + wh/2, z), (ww - 0.1, wh - 0.1, 0.06), _WIN_GLS, coll=False)
        # Spawn just outside
        out_z = z - 2.5 if z <= (Z1 + Z2) / 2 else z + 2.5
        window_spawns.append(Vec3(wx, y_fl + 1, out_z))


# Build a wall panel along Z (fixed x) with optional window openings.
def _zwall(z1, z2, x, y_fl, wins=(), col=_BRICK, thick=WT):
    h    = FH
    segs = _slice1d(z1, z2, [(w[0]-w[1]/2, w[0]+w[1]/2) for w in wins])
    for sz1, sz2 in segs:
        cz = (sz1 + sz2) / 2
        _solid(x, y_fl, cz, thick, h, sz2 - sz1, col)

    for wz, ww, wy, wh in wins:
        if wy > 0:
            _solid(x, y_fl, wz, thick, wy, ww, col)
        above = h - wy - wh
        if above > 0:
            _solid(x, y_fl + wy + wh, wz, thick, above, ww, col)
        _b((x, y_fl + wy + wh/2, wz), (thick + 0.18, wh + 0.22, ww + 0.22), _WIN_FRM, coll=False)
        _b((x, y_fl + wy + wh/2, wz), (0.06, wh - 0.1, ww - 0.1), _WIN_GLS, coll=False)
        out_x = x - 2.5 if x <= (X1 + X2) / 2 else x + 2.5
        window_spawns.append(Vec3(out_x, y_fl + 1, wz))


# Build an interior X-axis wall with a doorway gap.
def _xwall_door(x1, x2, z, y_fl, door_cx, door_w=2.6, col=_PLASTER, thick=WT):
    h = FH
    dh = 3.6
    segs = _slice1d(x1, x2, [(door_cx - door_w/2, door_cx + door_w/2)])
    for sx1, sx2 in segs:
        _solid((sx1+sx2)/2, y_fl, z, sx2-sx1, h, thick, col)
    above = h - dh
    if above > 0:
        _solid(door_cx, y_fl + dh, z, door_w, above, thick, col)


# Build an interior Z-axis wall with a doorway gap.
def _zwall_door(z1, z2, x, y_fl, door_cz, door_w=2.6, col=_PLASTER, thick=WT):
    h = FH
    dh = 3.6
    segs = _slice1d(z1, z2, [(door_cz - door_w/2, door_cz + door_w/2)])
    for sz1, sz2 in segs:
        _solid(x, y_fl, (sz1+sz2)/2, thick, h, sz2-sz1, col)
    above = h - dh
    if above > 0:
        _solid(x, y_fl + dh, door_cz, thick, above, door_w, col)


# Slice a 1D interval [lo, hi] with a list of cut-out ranges [(a,b),...].
def _slice1d(lo, hi, cuts):
    edges = sorted(set([lo, hi] + [v for a, b in cuts for v in (max(lo,a), min(hi,b))]))
    segs  = []
    for i in range(len(edges) - 1):
        mid = (edges[i] + edges[i+1]) / 2
        if not any(a <= mid <= b for a, b in cuts):
            segs.append((edges[i], edges[i+1]))
    return segs


# Locked door barrier
def _barrier(cx, y_fl, cz, w, h, d, cost):
    e   = _b((cx, y_fl + h/2, cz), (w, h, d), _BARRIER)
    rec = {'entity': e, 'cost': cost, 'open': False}
    door_barriers.append(rec)
    return rec


# ── Ground floor (y = 0..5) ───────────────────────────────────────────────────
def _build_ground(y):
    # === Floors ===
    # Entry Hall  x:-8..8  z:-25..-10
    _slab(0,      y, -17.5, 16, 15, _WOOD)
    # Living Room x:-30..-8  z:-25..-8
    _slab(-19,    y, -16.5, 22, 17, _WOOD)
    # Dining Room x:8..30  z:-25..-8
    _slab(19,     y, -16.5, 22, 17, _WOOD)
    # Staircase Hall x:-6..6  z:-10..8
    _slab(0,      y,  -1,   12, 18, _STONE_F)
    # Library x:-30..-6  z:-8..14
    _slab(-18,    y,   3,   24, 22, _WOOD)
    # Kitchen x:6..30  z:-8..14
    _slab(18,     y,   3,   24, 22, _WOOD)
    # Rear Hall x:-6..6  z:8..20
    _slab(0,      y,  14,   12, 12, _WOOD)
    # Rear Study x:-30..-6  z:14..25
    _slab(-18,    y,  19.5, 24, 11, _WOOD)
    # Pantry x:6..30  z:14..25
    _slab(18,     y,  19.5, 24, 11, _WOOD)

    # === Ceiling (underside of floor above) ===
    cy = y + FH
    _slab(0, cy, -17.5, 16, 15, _CEIL)
    _slab(-19, cy, -16.5, 22, 17, _CEIL)
    _slab(19, cy, -16.5, 22, 17, _CEIL)
    _slab(0, cy, -1, 12, 18, _CEIL)
    _slab(-18, cy, 3, 24, 22, _CEIL)
    _slab(18, cy, 3, 24, 22, _CEIL)
    _slab(0, cy, 14, 12, 12, _CEIL)
    _slab(-18, cy, 19.5, 24, 11, _CEIL)
    _slab(18, cy, 19.5, 24, 11, _CEIL)

    # === Exterior walls ===
    # Front face z=Z1=-25 — Entry Hall + Living + Dining
    _xwall(X1, -8, Z1, y, wins=[(-22, 2.2, 1.0, 2.2), (-15, 2.2, 1.0, 2.2)], col=_BRICK)
    _xwall(-8,  8, Z1, y, wins=[(0, 2.2, 1.0, 2.2)])                           # entry centre win
    _xwall( 8, X2, Z1, y, wins=[(15, 2.2, 1.0, 2.2), (22, 2.2, 1.0, 2.2)], col=_BRICK)
    # Left face x=X1=-30 — Living, Library, Rear Study
    _zwall(Z1, -8, X1, y, wins=[(-18, 2.2, 1.0, 2.2)], col=_BRICK)
    _zwall(-8, 14, X1, y, wins=[(2,   2.2, 1.0, 2.2)], col=_BRICK)
    _zwall(14, Z2, X1, y, wins=[(20,  2.2, 1.0, 2.2)], col=_BRICK)
    # Right face x=X2=30 — Dining, Kitchen, Pantry
    _zwall(Z1, -8, X2, y, wins=[(-18, 2.2, 1.0, 2.2)], col=_BRICK)
    _zwall(-8, 14, X2, y, wins=[(2,   2.2, 1.0, 2.2)], col=_BRICK)
    _zwall(14, Z2, X2, y, wins=[(20,  2.2, 1.0, 2.2)], col=_BRICK)
    # Back face z=Z2=25
    _xwall(X1, -6, Z2, y, wins=[(-18, 2.2, 1.0, 2.2)], col=_BRICK)
    _xwall(-6,  6, Z2, y)
    _xwall( 6, X2, Z2, y, wins=[(18,  2.2, 1.0, 2.2)], col=_BRICK)

    # === Interior partition walls (with open doorways) ===
    # Entry Hall south wall — separates Entry from Staircase Hall (open arch)
    _xwall_door(-8, 8, -10, y, door_cx=0, door_w=4.0, col=_PLASTER)
    # Entry ↔ Living Room
    _zwall_door(Z1, -8, -8, y, door_cz=-16)
    # Entry ↔ Dining Room
    _zwall_door(Z1, -8, 8, y, door_cz=-16)
    # Library north wall
    _xwall_door(X1, -6, 14, y, door_cx=-18, col=_PLASTER)
    # Library ↔ Staircase
    _zwall_door(-10, 8, -6, y, door_cz=0)
    # Kitchen north wall
    _xwall_door(6, X2, 14, y, door_cx=18, col=_PLASTER)
    # Kitchen ↔ Staircase
    _zwall_door(-10, 8, 6, y, door_cz=0)
    # Rear Hall ↔ Rear Study
    _zwall_door(14, Z2, -6, y, door_cz=19)
    # Rear Hall ↔ Pantry
    _zwall_door(14, Z2, 6, y, door_cz=19)
    # Rear Hall top wall
    _xwall(X1, X2, Z2, y)   # already exterior

    # === Locked barriers ===
    # Living Room → Library (500 pts)
    _barrier(-8, y, -11, WT+0.1, 3.6, 2.6, 500)
    # Dining Room → Kitchen (500 pts)
    _barrier(8, y, -11, WT+0.1, 3.6, 2.6, 500)
    # Staircase Hall → Rear Hall (750 pts)
    _barrier(0, y, 8, 4.0, 3.6, WT+0.1, 750)


# ── Floor 1 (y = 5..10) ──────────────────────────────────────────────────────
def _build_floor1(y):
    _slab(-19, y, -16.5, 22, 17, _WOOD)   # Master Bedroom
    _slab(19,  y, -16.5, 22, 17, _WOOD)   # Study
    _slab(0,   y,  -1,   12, 18, _STONE_F) # Upper Landing
    _slab(-18, y,   3,   24, 22, _WOOD)   # Trophy Room
    _slab(18,  y,   3,   24, 22, _WOOD)   # Bedroom 2
    _slab(0,   y,  14,   12, 12, _WOOD)   # Corridor
    _slab(-18, y,  19.5, 24, 11, _WOOD)   # Guest Suite
    _slab(18,  y,  19.5, 24, 11, _WOOD)   # Servants Quarters

    cy = y + FH
    _slab(-19, cy, -16.5, 22, 17, _CEIL)
    _slab(19,  cy, -16.5, 22, 17, _CEIL)
    _slab(0,   cy,  -1,   12, 18, _CEIL)
    _slab(-18, cy,   3,   24, 22, _CEIL)
    _slab(18,  cy,   3,   24, 22, _CEIL)
    _slab(0,   cy,  14,   12, 12, _CEIL)
    _slab(-18, cy,  19.5, 24, 11, _CEIL)
    _slab(18,  cy,  19.5, 24, 11, _CEIL)

    # Exterior walls
    _xwall(X1, -8, Z1, y, wins=[(-20, 2.2, 1.0, 2.2)], col=_BRICK)
    _xwall(-8, 8,  Z1, y, wins=[(0,   2.2, 1.0, 2.2)], col=_BRICK)
    _xwall(8, X2,  Z1, y, wins=[(20,  2.2, 1.0, 2.2)], col=_BRICK)
    _zwall(Z1, -8, X1, y, wins=[(-18, 2.2, 1.0, 2.2)], col=_BRICK)
    _zwall(-8, 14, X1, y, wins=[(2,   2.2, 1.0, 2.2)], col=_BRICK)
    _zwall(14, Z2, X1, y, wins=[(20,  2.2, 1.0, 2.2)], col=_BRICK)
    _zwall(Z1, -8, X2, y, wins=[(-18, 2.2, 1.0, 2.2)], col=_BRICK)
    _zwall(-8, 14, X2, y, wins=[(2,   2.2, 1.0, 2.2)], col=_BRICK)
    _zwall(14, Z2, X2, y, wins=[(20,  2.2, 1.0, 2.2)], col=_BRICK)
    _xwall(X1, -6, Z2, y, col=_BRICK)
    _xwall(-6,  6, Z2, y, col=_BRICK)
    _xwall( 6, X2, Z2, y, col=_BRICK)

    # Interior partitions
    _xwall_door(X1,  -8, -10, y, door_cx=-19)
    _xwall_door( 8, X2,  -10, y, door_cx=19)
    _zwall_door(Z1, -8, -8, y, door_cz=-16)
    _zwall_door(Z1, -8,  8, y, door_cz=-16)
    _zwall_door(-10, 8, -6, y, door_cz=0)
    _zwall_door(-10, 8,  6, y, door_cz=0)
    _xwall_door(X1, -6, 14, y, door_cx=-18, col=_PLASTER)
    _xwall_door( 6, X2, 14, y, door_cx=18,  col=_PLASTER)
    _zwall_door(14, Z2, -6, y, door_cz=19)
    _zwall_door(14, Z2,  6, y, door_cz=19)

    # Locked barriers
    _barrier(-8, y, -11, WT+0.1, 3.6, 2.6, 1000)
    _barrier(8,  y, -11, WT+0.1, 3.6, 2.6, 1000)
    _barrier(0,  y,  8,  4.0,    3.6, WT+0.1, 1250)


# ── Floor 2 (y = 10..15) ─────────────────────────────────────────────────────
def _build_floor2(y):
    _slab(-19, y, -12.5, 22, 25, _WOOD)   # Bedroom 3
    _slab(19,  y, -12.5, 22, 25, _WOOD)   # Bedroom 4
    _slab(0,   y,   0,   12, 16, _STONE_F) # Central Hall
    _slab(0,   y,  16,   40, 18, _WOOD)   # Sitting Room

    cy = y + FH
    _slab(-19, cy, -12.5, 22, 25, _CEIL)
    _slab(19,  cy, -12.5, 22, 25, _CEIL)
    _slab(0,   cy,   0,   12, 16, _CEIL)
    _slab(0,   cy,  16,   40, 18, _CEIL)

    # Exterior walls
    _xwall(X1, -8, Z1, y, wins=[(-20, 2.2, 1.0, 2.2)], col=_BRICK)
    _xwall(-8,  8, Z1, y, col=_BRICK)
    _xwall( 8, X2, Z1, y, wins=[(20,  2.2, 1.0, 2.2)], col=_BRICK)
    _zwall(Z1, Z2, X1, y, wins=[(-12, 2.2, 1.0, 2.2), (15, 2.2, 1.0, 2.2)], col=_BRICK)
    _zwall(Z1, Z2, X2, y, wins=[(-12, 2.2, 1.0, 2.2), (15, 2.2, 1.0, 2.2)], col=_BRICK)
    _xwall(X1, -6, Z2, y, wins=[(-18, 2.2, 1.0, 2.2)], col=_BRICK)
    _xwall(-6,  6, Z2, y, wins=[(0,   2.2, 1.0, 2.2)], col=_BRICK)
    _xwall( 6, X2, Z2, y, wins=[(18,  2.2, 1.0, 2.2)], col=_BRICK)

    # Interior partitions
    _zwall_door(Z1, 0, -8, y, door_cz=-12)
    _zwall_door(Z1, 0,  8, y, door_cz=-12)
    _xwall_door(X1, X2, 0, y, door_cx=-8, col=_PLASTER)
    _xwall_door(X1, X2, 0, y, door_cx=8,  col=_PLASTER)
    _xwall_door(-8, 8, 8, y, door_cx=0, col=_PLASTER)

    # Locked barriers
    _barrier(-8, y, -11, WT+0.1, 3.6, 2.6, 1750)
    _barrier(8,  y, -11, WT+0.1, 3.6, 2.6, 1750)
    _barrier(0,  y,  8,  6.0,    3.6, WT+0.1, 2000)


# ── Basement (y = -5..0) ─────────────────────────────────────────────────────
def _build_basement(y):
    # Smaller footprint: x:-22..22  z:-12..16
    BX1, BX2, BZ1, BZ2 = -22, 22, -12, 16

    _slab(0,  y,   2, 44, 28, _STONE_F)   # Boiler Room + Storage + Wine Cellar
    cy = y + FH
    _slab(0, cy, 2, 44, 28, _STONE)

    # Exterior basement walls (stone)
    _xwall(BX1, BX2, BZ1, y, wins=[(0, 2.0, 0.5, 1.5)], col=_STONE)
    _xwall(BX1, BX2, BZ2, y, col=_STONE)
    _zwall(BZ1, BZ2, BX1, y, wins=[(4, 2.0, 0.5, 1.5)], col=_STONE)
    _zwall(BZ1, BZ2, BX2, y, wins=[(4, 2.0, 0.5, 1.5)], col=_STONE)

    # Interior partitions
    _zwall_door(BZ1, BZ2, -6, y, door_cz=2, col=_STONE)
    _zwall_door(BZ1, BZ2,  6, y, door_cz=2, col=_STONE)
    _xwall_door(BX1, BX2, -3, y, door_cx=0, col=_STONE)

    # Boiler visual
    _b((0, y + 1.5, 6), (3, 3, 3), color.rgb32(55, 55, 55))

    # Locked barriers
    _barrier(-6, y, -6, WT+0.1, 3.6, 2.6, 1000)
    _barrier(6,  y, -6, WT+0.1, 3.6, 2.6, 1000)


# ── Rooftop (y = 15) ─────────────────────────────────────────────────────────
def _build_rooftop(y):
    # Flat roof deck
    _slab(0, y, 0, 62, 52, _ROOF, thick=0.4)
    # Parapet walls (knee-height around perimeter)
    ph = 1.5
    _solid(0,      y + 0.4, Z1,      60, ph, WT, _PARAPET)
    _solid(0,      y + 0.4, Z2,      60, ph, WT, _PARAPET)
    _solid(X1,     y + 0.4,  0,      WT, ph, 50, _PARAPET)
    _solid(X2,     y + 0.4,  0,      WT, ph, 50, _PARAPET)
    # Chimneys
    for cx, cz in [(-10, -10), (10, -10), (-8, 14), (8, 14)]:
        _b((cx, y + 0.4 + 2, cz), (1.2, 4, 1.2), color.rgb32(90, 78, 70))
    # Rooftop access hatch frame
    _b((0, y + 0.4 + 0.25, 0), (3, 0.5, 3), color.rgb32(70, 55, 35))


# ── Staircases ────────────────────────────────────────────────────────────────
def _build_stairs():
    # Ground → Floor 1 (main staircase, x:-4..4, z:-8..4, rises from y=0 to y=5)
    # Ramp going north (toward +z) while rising
    angle = -26   # ~atan(5/10) degrees
    _ramp(0, 2.5, -2.5, 8, 0.4, 11, angle, col=_STAIR)
    # Handrails
    _solid(-4.2, 0, -2.5, 0.2, 5.2, 11, color.rgb32(60, 42, 22))
    _solid(4.2,  0, -2.5, 0.2, 5.2, 11, color.rgb32(60, 42, 22))

    # Floor 1 → Floor 2 (same shaft, z:0..12, rises from y=5 to y=10)
    _ramp(0, 7.5, 6, 8, 0.4, 11, angle, col=_STAIR)
    _solid(-4.2, 5, 6, 0.2, 5.2, 11, color.rgb32(60, 42, 22))
    _solid(4.2,  5, 6, 0.2, 5.2, 11, color.rgb32(60, 42, 22))

    # Floor 2 → Rooftop (small stair, x:-2..2, z:6..12, y=10..15)
    _ramp(0, 12.5, 9, 4, 0.4, 11, angle, col=_STAIR)
    _solid(-2.2, 10, 9, 0.2, 5.2, 11, color.rgb32(60, 42, 22))
    _solid(2.2,  10, 9, 0.2, 5.2, 11, color.rgb32(60, 42, 22))

    # Basement stairs (center of ground floor, down from y=0 to y=-5)
    # Located at x:-3..3, z:4..12
    _ramp(0, -2.5, 8, 6, 0.4, 11, 26, col=_STAIR)
    _solid(-3.2, -5, 8, 0.2, 5.2, 11, color.rgb32(60, 42, 22))
    _solid(3.2,  -5, 8, 0.2, 5.2, 11, color.rgb32(60, 42, 22))
    _barrier(0, -0.2, 4, 6.0, 3.6, WT+0.1, 1500)  # locked until 1500 pts


# ── Lighting ──────────────────────────────────────────────────────────────────
def _build_lighting():
    sun = DirectionalLight()
    sun.look_at(Vec3(0.5, -1, 0.3))
    sun.color = color.rgb32(200, 180, 140)
    AmbientLight(color=color.rgba32(80, 80, 100, 255))
    sky = Sky()
    sky.color = color.rgb32(20, 20, 30)


# ── Entry facade details ──────────────────────────────────────────────────────
def _build_facade():
    y = 0
    # Front door frame
    _b((0, y + 2.0, Z1 - 0.3), (3.0, 4.2, 0.4), color.rgb32(50, 32, 14))
    # Double doors (decorative)
    _b((-0.75, y + 1.8, Z1 - 0.55), (1.3, 3.4, 0.15), color.rgb32(70, 45, 20))
    _b(( 0.75, y + 1.8, Z1 - 0.55), (1.3, 3.4, 0.15), color.rgb32(70, 45, 20))
    # Portico columns
    for cx in [-3.5, 3.5]:
        _b((cx, y + 2.5, Z1 - 1.5), (0.6, 5.0, 0.6), color.rgb32(210, 200, 185))
    # Portico roof slab
    _b((0, y + 5.1, Z1 - 1.0), (9, 0.4, 3), color.rgb32(190, 180, 165))
    # Steps up to entrance
    for i, (sh, sz) in enumerate([(0.3, Z1-0.6), (0.6, Z1-1.1), (0.9, Z1-1.6)]):
        _b((0, y + sh/2, sz), (5, sh, 1), color.rgb32(180, 170, 155))


# ── Main entry point ──────────────────────────────────────────────────────────
def create_zombies_map():
    window_spawns.clear()
    door_barriers.clear()

    # Ground plane under mansion
    _slab(0, -0.2, 0, 80, 80, _DIRT, thick=0.4)

    _build_ground(0)
    _build_floor1(FH)
    _build_floor2(FH * 2)
    _build_basement(-FH)
    _build_rooftop(FH * 3)
    _build_stairs()
    _build_facade()
    _build_lighting()

    return {
        'window_spawns': window_spawns,
        'door_barriers': door_barriers,
        'player_spawn':  player_spawn,
    }
