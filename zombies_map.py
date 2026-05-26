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

FH = 8.0    # floor height per level (was 5.0 — raised for headroom)
WT = 0.6    # wall thickness
DH = 5.5    # door/barrier height
DW = 5.0    # default door/barrier width

# Mansion x/z extents — 2× original (60×50 → 120×100)
X1, X2 = -60.0, 60.0
Z1, Z2 = -50.0, 50.0

# Public data filled by create_zombies_map()
window_spawns = []
door_barriers = []
player_spawn  = Vec3(0, 1.2, -40)


# ── Geometry helpers ──────────────────────────────────────────────────────────
def _b(pos, sc, col, coll=True):
    return Entity(model='cube', position=pos, scale=sc, color=col,
                  collider='box' if coll else None)


def _slab(cx, y, cz, w, d, col, thick=0.3):
    _b((cx, y, cz), (w, thick, d), col)


def _solid(cx, y_fl, cz, w, h, d, col):
    _b((cx, y_fl + h / 2, cz), (w, h, d), col)


def _steps(cx, y_base, z_start, w, rise, run, col=_STAIR):
    """Individual step cubes going in +z, rising from y_base to y_base+rise."""
    n = max(8, int(rise * 2))   # ~0.5-unit step height
    sh, sd = rise / n, run / n
    for i in range(n):
        h = (i + 1) * sh
        _b((cx, y_base + h / 2, z_start + (i + 0.5) * sd), (w, h, sd), col)


def _steps_down(cx, y_top, z_start, w, drop, run, col=_STAIR):
    """Step cubes going in +z while descending from y_top to y_top-drop."""
    n = max(8, int(drop * 2))
    sh, sd = drop / n, run / n
    y_bot = y_top - drop
    for i in range(n):
        h = (n - i) * sh
        _b((cx, y_bot + h / 2, z_start + (i + 0.5) * sd), (w, h, sd), col)


# Build a wall panel along X (fixed z) with optional window openings.
# wins = list of (win_center_x, win_w, win_sill, win_h)
def _xwall(x1, x2, z, y_fl, wins=(), col=_BRICK, thick=WT):
    h    = FH
    segs = _slice1d(x1, x2, [(w[0]-w[1]/2, w[0]+w[1]/2) for w in wins])
    for sx1, sx2 in segs:
        cx = (sx1 + sx2) / 2
        _solid(cx, y_fl, z, sx2 - sx1, h, thick, col)

    for wx, ww, wy, wh in wins:
        if wy > 0:
            _solid(wx, y_fl, z, ww, wy, thick, col)
        above = h - wy - wh
        if above > 0:
            _solid(wx, y_fl + wy + wh, z, ww, above, thick, col)
        _b((wx, y_fl + wy + wh/2, z), (ww + 0.3, wh + 0.3, thick + 0.2), _WIN_FRM, coll=False)
        _b((wx, y_fl + wy + wh/2, z), (ww - 0.1, wh - 0.1, 0.08), _WIN_GLS, coll=False)
        out_z = z - 4.0 if z <= (Z1 + Z2) / 2 else z + 4.0
        window_spawns.append(Vec3(wx, y_fl + 1.2, out_z))


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
        _b((x, y_fl + wy + wh/2, wz), (thick + 0.2, wh + 0.3, ww + 0.3), _WIN_FRM, coll=False)
        _b((x, y_fl + wy + wh/2, wz), (0.08, wh - 0.1, ww - 0.1), _WIN_GLS, coll=False)
        out_x = x - 4.0 if x <= (X1 + X2) / 2 else x + 4.0
        window_spawns.append(Vec3(out_x, y_fl + 1.2, wz))


# Interior X-axis wall with a doorway gap.
def _xwall_door(x1, x2, z, y_fl, door_cx, door_w=DW, col=_PLASTER, thick=WT):
    h  = FH
    dh = DH
    segs = _slice1d(x1, x2, [(door_cx - door_w/2, door_cx + door_w/2)])
    for sx1, sx2 in segs:
        _solid((sx1+sx2)/2, y_fl, z, sx2-sx1, h, thick, col)
    above = h - dh
    if above > 0:
        _solid(door_cx, y_fl + dh, z, door_w, above, thick, col)


# Interior Z-axis wall with a doorway gap.
def _zwall_door(z1, z2, x, y_fl, door_cz, door_w=DW, col=_PLASTER, thick=WT):
    h  = FH
    dh = DH
    segs = _slice1d(z1, z2, [(door_cz - door_w/2, door_cz + door_w/2)])
    for sz1, sz2 in segs:
        _solid(x, y_fl, (sz1+sz2)/2, thick, h, sz2-sz1, col)
    above = h - dh
    if above > 0:
        _solid(x, y_fl + dh, door_cz, thick, above, door_w, col)


# Slice a 1D interval [lo, hi] with cut-out ranges.
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


# ── Ground floor (y = 0..FH) ─────────────────────────────────────────────────
def _build_ground(y):
    # === Floors ===
    _slab(  0, y, -35, 32, 30, _WOOD)      # Entry Hall      x:-16..16  z:-50..-20
    _slab(-38, y, -33, 44, 34, _WOOD)      # Living Room     x:-60..-16 z:-50..-16
    _slab( 38, y, -33, 44, 34, _WOOD)      # Dining Room     x:16..60   z:-50..-16
    _slab(  0, y,  -2, 24, 36, _STONE_F)   # Staircase Hall  x:-12..12  z:-20..16
    _slab(-36, y,   6, 48, 44, _WOOD)      # Library         x:-60..-12 z:-16..28
    _slab( 36, y,   6, 48, 44, _WOOD)      # Kitchen         x:12..60   z:-16..28
    _slab(  0, y,  28, 24, 24, _WOOD)      # Rear Hall       x:-12..12  z:16..40
    _slab(-36, y,  39, 48, 22, _WOOD)      # Rear Study      x:-60..-12 z:28..50
    _slab( 36, y,  39, 48, 22, _WOOD)      # Pantry          x:12..60   z:28..50

    # === Ceilings — offset -0.31 below the floor slab above to prevent Z-fighting.
    # Staircase Hall ceiling is intentionally omitted — the shaft is open-height
    # so the probe ray can reach step surfaces without hitting a ceiling mid-climb.
    cy = y + FH - 0.31
    _slab(  0, cy, -35, 32, 30, _CEIL)
    _slab(-38, cy, -33, 44, 34, _CEIL)
    _slab( 38, cy, -33, 44, 34, _CEIL)
    # _slab(  0, cy,  -2, 24, 36, _CEIL)  # Staircase Hall — omitted (open shaft)
    _slab(-36, cy,   6, 48, 44, _CEIL)
    _slab( 36, cy,   6, 48, 44, _CEIL)
    _slab(  0, cy,  28, 24, 24, _CEIL)
    _slab(-36, cy,  39, 48, 22, _CEIL)
    _slab( 36, cy,  39, 48, 22, _CEIL)

    # === Exterior walls ===
    # Front face z=Z1=-50
    _xwall(X1, -16, Z1, y, wins=[(-44, 4.4, 1.5, 3.5), (-30, 4.4, 1.5, 3.5)], col=_BRICK)
    _xwall(-16, 16, Z1, y, wins=[(0,   4.4, 1.5, 3.5)])
    _xwall( 16, X2, Z1, y, wins=[(30,  4.4, 1.5, 3.5), (44,  4.4, 1.5, 3.5)], col=_BRICK)
    # Left face x=X1=-60
    _zwall(Z1, -16, X1, y, wins=[(-36, 4.4, 1.5, 3.5)], col=_BRICK)
    _zwall(-16, 28, X1, y, wins=[(  4, 4.4, 1.5, 3.5)], col=_BRICK)
    _zwall( 28, Z2, X1, y, wins=[( 40, 4.4, 1.5, 3.5)], col=_BRICK)
    # Right face x=X2=60
    _zwall(Z1, -16, X2, y, wins=[(-36, 4.4, 1.5, 3.5)], col=_BRICK)
    _zwall(-16, 28, X2, y, wins=[(  4, 4.4, 1.5, 3.5)], col=_BRICK)
    _zwall( 28, Z2, X2, y, wins=[( 40, 4.4, 1.5, 3.5)], col=_BRICK)
    # Back face z=Z2=50
    _xwall(X1, -12, Z2, y, wins=[(-36, 4.4, 1.5, 3.5)], col=_BRICK)
    _xwall(-12,  12, Z2, y)
    _xwall(  12, X2, Z2, y, wins=[( 36, 4.4, 1.5, 3.5)], col=_BRICK)

    # === Interior partition walls ===
    _xwall_door(-16, 16, -20, y, door_cx=0,   door_w=8.0, col=_PLASTER)  # Entry Hall south
    _zwall_door(Z1, -16, -16, y, door_cz=-32)                             # Entry ↔ Living
    _zwall_door(Z1, -16,  16, y, door_cz=-32)                             # Entry ↔ Dining
    _xwall_door(X1, -12,  28, y, door_cx=-36, col=_PLASTER)               # Library north
    _zwall_door(-20, 16, -12, y, door_cz=0)                               # Library ↔ Staircase
    _xwall_door( 12, X2,  28, y, door_cx=36,  col=_PLASTER)               # Kitchen north
    _zwall_door(-20, 16,  12, y, door_cz=0)                               # Kitchen ↔ Staircase
    _zwall_door( 28, Z2, -12, y, door_cz=38)                              # Rear Hall ↔ Study
    _zwall_door( 28, Z2,  12, y, door_cz=38)                              # Rear Hall ↔ Pantry

    # === Locked barriers ===
    _barrier(-16, y, -22, WT+0.1, DH, DW,   500)  # Living → Library
    _barrier( 16, y, -22, WT+0.1, DH, DW,   500)  # Dining → Kitchen
    _barrier(  0, y,  16, 8.0,    DH, WT+0.1, 750) # Staircase → Rear Hall


# ── Floor 1 (y = FH..2*FH) ───────────────────────────────────────────────────
def _build_floor1(y):
    _slab(-38, y, -33, 44, 34, _WOOD)      # Master Bedroom
    _slab( 38, y, -33, 44, 34, _WOOD)      # Study
    _slab(  0, y,  -2, 24, 36, _STONE_F)   # Upper Landing
    _slab(-36, y,   6, 48, 44, _WOOD)      # Trophy Room
    _slab( 36, y,   6, 48, 44, _WOOD)      # Bedroom 2
    _slab(  0, y,  28, 24, 24, _WOOD)      # Corridor
    _slab(-36, y,  39, 48, 22, _WOOD)      # Guest Suite
    _slab( 36, y,  39, 48, 22, _WOOD)      # Servants Quarters

    cy = y + FH - 0.31
    _slab(-38, cy, -33, 44, 34, _CEIL)
    _slab( 38, cy, -33, 44, 34, _CEIL)
    # _slab(  0, cy,  -2, 24, 36, _CEIL)  # Upper Landing — omitted (open shaft)
    _slab(-36, cy,   6, 48, 44, _CEIL)
    _slab( 36, cy,   6, 48, 44, _CEIL)
    _slab(  0, cy,  28, 24, 24, _CEIL)
    _slab(-36, cy,  39, 48, 22, _CEIL)
    _slab( 36, cy,  39, 48, 22, _CEIL)

    # Exterior walls
    _xwall(X1, -16, Z1, y, wins=[(-40, 4.4, 1.5, 3.5)], col=_BRICK)
    _xwall(-16, 16, Z1, y, wins=[(  0, 4.4, 1.5, 3.5)], col=_BRICK)
    _xwall( 16, X2, Z1, y, wins=[( 40, 4.4, 1.5, 3.5)], col=_BRICK)
    _zwall(Z1, -16, X1, y, wins=[(-36, 4.4, 1.5, 3.5)], col=_BRICK)
    _zwall(-16, 28, X1, y, wins=[(  4, 4.4, 1.5, 3.5)], col=_BRICK)
    _zwall( 28, Z2, X1, y, wins=[( 40, 4.4, 1.5, 3.5)], col=_BRICK)
    _zwall(Z1, -16, X2, y, wins=[(-36, 4.4, 1.5, 3.5)], col=_BRICK)
    _zwall(-16, 28, X2, y, wins=[(  4, 4.4, 1.5, 3.5)], col=_BRICK)
    _zwall( 28, Z2, X2, y, wins=[( 40, 4.4, 1.5, 3.5)], col=_BRICK)
    _xwall(X1, -12, Z2, y, col=_BRICK)
    _xwall(-12,  12, Z2, y, col=_BRICK)
    _xwall(  12, X2, Z2, y, col=_BRICK)

    # Interior partitions
    _xwall_door(X1,  -16, -20, y, door_cx=-38)
    _xwall_door( 16, X2,  -20, y, door_cx=38)
    _zwall_door(Z1,  -16, -16, y, door_cz=-32)
    _zwall_door(Z1,  -16,  16, y, door_cz=-32)
    _zwall_door(-20,  16, -12, y, door_cz=0)
    _zwall_door(-20,  16,  12, y, door_cz=0)
    _xwall_door(X1,  -12,  28, y, door_cx=-36, col=_PLASTER)
    _xwall_door( 12, X2,   28, y, door_cx=36,  col=_PLASTER)
    _zwall_door( 28, Z2,  -12, y, door_cz=38)
    _zwall_door( 28, Z2,   12, y, door_cz=38)

    # Locked barriers
    _barrier(-16, y, -22, WT+0.1, DH, DW,    1000)
    _barrier( 16, y, -22, WT+0.1, DH, DW,    1000)
    _barrier(  0, y,  16, 8.0,    DH, WT+0.1, 1250)


# ── Floor 2 (y = 2*FH..3*FH) ─────────────────────────────────────────────────
def _build_floor2(y):
    _slab(-38, y, -25, 44, 50, _WOOD)      # Bedroom 3
    _slab( 38, y, -25, 44, 50, _WOOD)      # Bedroom 4
    _slab(  0, y,   0, 24, 32, _STONE_F)   # Central Hall
    _slab(  0, y,  32, 80, 36, _WOOD)      # Sitting Room

    cy = y + FH - 0.31
    _slab(-38, cy, -25, 44, 50, _CEIL)
    _slab( 38, cy, -25, 44, 50, _CEIL)
    # _slab(  0, cy,   0, 24, 32, _CEIL)  # Central Hall — omitted (open shaft)
    _slab(  0, cy,  32, 80, 36, _CEIL)

    # Exterior walls
    _xwall(X1, -16, Z1, y, wins=[(-40, 4.4, 1.5, 3.5)], col=_BRICK)
    _xwall(-16, 16, Z1, y, col=_BRICK)
    _xwall( 16, X2, Z1, y, wins=[( 40, 4.4, 1.5, 3.5)], col=_BRICK)
    _zwall(Z1, Z2, X1, y, wins=[(-24, 4.4, 1.5, 3.5), (30, 4.4, 1.5, 3.5)], col=_BRICK)
    _zwall(Z1, Z2, X2, y, wins=[(-24, 4.4, 1.5, 3.5), (30, 4.4, 1.5, 3.5)], col=_BRICK)
    _xwall(X1, -12, Z2, y, wins=[(-36, 4.4, 1.5, 3.5)], col=_BRICK)
    _xwall(-12,  12, Z2, y, wins=[(  0, 4.4, 1.5, 3.5)], col=_BRICK)
    _xwall(  12, X2, Z2, y, wins=[( 36, 4.4, 1.5, 3.5)], col=_BRICK)

    # Interior partitions
    _zwall_door(Z1, 0, -16, y, door_cz=-24)
    _zwall_door(Z1, 0,  16, y, door_cz=-24)
    _xwall_door(X1, X2, 0, y, door_cx=-16, col=_PLASTER)
    _xwall_door(X1, X2, 0, y, door_cx=16,  col=_PLASTER)
    _xwall_door(-16, 16, 16, y, door_cx=0,  col=_PLASTER)

    # Locked barriers
    _barrier(-16, y, -22, WT+0.1, DH, DW,     1750)
    _barrier( 16, y, -22, WT+0.1, DH, DW,     1750)
    _barrier(  0, y,  16, 12.0,   DH, WT+0.1,  2000)


# ── Basement (y = -FH..0) ─────────────────────────────────────────────────────
def _build_basement(y):
    BX1, BX2, BZ1, BZ2 = -44, 44, -24, 32

    _slab(0, y, 4, 88, 56, _STONE_F)
    cy = y + FH - 0.31
    _slab(0, cy, 4, 88, 56, _STONE)

    _xwall(BX1, BX2, BZ1, y, wins=[(0, 4.0, 1.0, 3.0)], col=_STONE)
    _xwall(BX1, BX2, BZ2, y, col=_STONE)
    _zwall(BZ1, BZ2, BX1, y, wins=[(8, 4.0, 1.0, 3.0)], col=_STONE)
    _zwall(BZ1, BZ2, BX2, y, wins=[(8, 4.0, 1.0, 3.0)], col=_STONE)

    _zwall_door(BZ1, BZ2, -12, y, door_cz=4, col=_STONE)
    _zwall_door(BZ1, BZ2,  12, y, door_cz=4, col=_STONE)
    _xwall_door(BX1, BX2,  -6, y, door_cx=0, col=_STONE)

    _b((0, y + 3, 12), (6, 6, 6), color.rgb32(55, 55, 55))  # Boiler

    _barrier(-12, y, -12, WT+0.1, DH, DW, 1000)
    _barrier( 12, y, -12, WT+0.1, DH, DW, 1000)


# ── Rooftop (y = 3*FH) ───────────────────────────────────────────────────────
def _build_rooftop(y):
    _slab(0, y, 0, 122, 102, _ROOF, thick=0.4)
    ph = 2.5
    _solid(  0, y + 0.4, Z1,  120, ph, WT, _PARAPET)
    _solid(  0, y + 0.4, Z2,  120, ph, WT, _PARAPET)
    _solid(X1, y + 0.4,   0, WT, ph, 100, _PARAPET)
    _solid(X2, y + 0.4,   0, WT, ph, 100, _PARAPET)
    for cx, cz in [(-20, -20), (20, -20), (-16, 28), (16, 28)]:
        _b((cx, y + 0.4 + 3, cz), (2.4, 6, 2.4), color.rgb32(90, 78, 70))
    _b((0, y + 0.4 + 0.3, 0), (6, 0.6, 6), color.rgb32(70, 55, 35))


# ── Staircases ────────────────────────────────────────────────────────────────
def _build_stairs():
    # Ground → Floor 1 (Staircase Hall, z: -18..0, y: 0..FH)
    _steps(0, 0, -18, 16, FH, 18)

    # Floor 1 → Floor 2 (Upper Landing, z: 0..16, y: FH..2*FH)
    _steps(0, FH, 0, 16, FH, 16)

    # Floor 2 → Rooftop (Central Hall, z: -8..8, y: 2*FH..3*FH)
    _steps(0, FH * 2, -8, 10, FH, 16)

    # Basement stairs (Staircase Hall, z: 8..28, descending y: 0..-FH)
    _steps_down(0, 0, 8, 12, FH, 20)
    _barrier(0, -0.2, 8, 12, DH, WT + 0.1, 1500)


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
    _b((0,    y + 3.5, Z1 - 0.5), (6.0, 7.0, 0.6), color.rgb32(50, 32, 14))
    _b((-1.4, y + 3.2, Z1 - 0.9), (2.6, 6.4, 0.2), color.rgb32(70, 45, 20))
    _b(( 1.4, y + 3.2, Z1 - 0.9), (2.6, 6.4, 0.2), color.rgb32(70, 45, 20))
    for cx in [-7.0, 7.0]:
        _b((cx, y + 4.5, Z1 - 3.0), (1.2, 9.0, 1.2), color.rgb32(210, 200, 185))
    _b((0, y + 9.2, Z1 - 2.0), (18, 0.7, 6), color.rgb32(190, 180, 165))
    for step_h, step_z in [(0.4, Z1 - 1.0), (0.8, Z1 - 2.0), (1.2, Z1 - 3.0)]:
        _b((0, y + step_h / 2, step_z), (9, step_h, 1.5), color.rgb32(180, 170, 155))


# ── Main entry point ──────────────────────────────────────────────────────────
def create_zombies_map():
    window_spawns.clear()
    door_barriers.clear()

    # Ground plane — lowered to -0.4 so it doesn't Z-fight with floor slabs at y=0
    _slab(0, -0.4, 0, 160, 160, _DIRT, thick=0.4)

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
