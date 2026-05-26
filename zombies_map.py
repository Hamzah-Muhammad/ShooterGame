from ursina import *

# ── Gothic colour palette ─────────────────────────────────────────────────────
_EXT_STONE  = color.rgb32( 65,  62,  58)   # dark grey exterior stone
_INT_STONE  = color.rgb32( 50,  46,  42)   # rough basement stone
_PLASTER    = color.rgb32(185, 175, 160)   # interior plaster walls
_FLOOR_WOOD = color.rgb32( 80,  52,  28)   # dark oak floorboards
_FLOOR_TILE = color.rgb32( 30,  30,  30)   # black tile (foyer)
_FLOOR_TILE2= color.rgb32(200, 195, 185)   # white tile (foyer alternating)
_FLOOR_SLT  = color.rgb32( 55,  52,  50)   # slate (staircase / landings)
_CEIL_COL   = color.rgb32(160, 152, 140)   # ceiling plaster
_ROOF_COL   = color.rgb32( 30,  30,  38)   # near-black roof slab
_PARAPET    = color.rgb32( 65,  62,  58)   # parapet same as ext stone
_STAIR      = color.rgb32( 72,  65,  55)   # stair treads
_WIN_FRM    = color.rgb32( 28,  22,  14)   # very dark window frame
_WIN_GLS    = color.rgba32(60, 100, 140, 70)
_BARRIER    = color.rgb32( 90,  58,  28)   # barrier board colour
_GRASS      = color.rgb32( 62,  68,  38)   # dead grass ground
_ROAD       = color.rgb32( 72,  68,  64)   # cobblestone road
_FENCE      = color.rgb32( 28,  26,  25)   # wrought-iron fence
_POOL_WATER = color.rgb32( 12,  28,  22)   # near-black pool water
_POOL_TILE  = color.rgb32( 22,  30,  28)   # pool surround
_GH_IRON    = color.rgb32( 55,  68,  45)   # greenhouse tarnished iron
_GRAVEL     = color.rgb32( 85,  82,  76)   # gravel path

# ── Layout constants ──────────────────────────────────────────────────────────
FH  = 8.0    # floor height
WT  = 0.6    # wall thickness
DH  = 5.5    # door/barrier opening height
DW  = 5.0    # default door width

# Mansion extents
MX1, MX2 = -60.0, 60.0
MZ1, MZ2 = -40.0, 40.0

# Front yard / road (north, negative Z)
FY_Z1, FY_Z2 = -95.0, MZ1      # front yard z range
RD_Z1, RD_Z2 = -115.0, FY_Z1   # road z range

# Backyard (south, positive Z)
BY_Z1, BY_Z2 = MZ2, 150.0
GH_Z1, GH_Z2 = 115.0, 150.0    # greenhouse

# Lateral extents for outdoor areas
OUT_X1, OUT_X2 = -100.0, 100.0

# Public data
window_spawns = []
door_barriers = []
player_spawn  = Vec3(0, 1.2, -105)   # starting on the road


# ── Geometry primitives ───────────────────────────────────────────────────────
def _b(pos, sc, col, coll=True):
    return Entity(model='cube', position=pos, scale=sc, color=col,
                  collider='box' if coll else None)


def _slab(cx, y, cz, w, d, col, thick=0.3):
    _b((cx, y, cz), (w, thick, d), col)


def _solid(cx, y_fl, cz, w, h, d, col):
    _b((cx, y_fl + h / 2, cz), (w, h, d), col)


def _steps(cx, y_base, z_start, w, rise, run, col=_STAIR):
    n = max(8, int(rise * 2))
    sh, sd = rise / n, run / n
    for i in range(n):
        h = (i + 1) * sh
        _b((cx, y_base + h / 2, z_start + (i + 0.5) * sd), (w, h, sd), col)


def _steps_down(cx, y_top, z_start, w, drop, run, col=_STAIR):
    n = max(8, int(drop * 2))
    sh, sd = drop / n, run / n
    y_bot = y_top - drop
    for i in range(n):
        h = (n - i) * sh
        _b((cx, y_bot + h / 2, z_start + (i + 0.5) * sd), (w, h, sd), col)


def _slice1d(lo, hi, cuts):
    edges = sorted(set([lo, hi] + [v for a, b in cuts for v in (max(lo, a), min(hi, b))]))
    segs = []
    for i in range(len(edges) - 1):
        mid = (edges[i] + edges[i + 1]) / 2
        if not any(a <= mid <= b for a, b in cuts):
            segs.append((edges[i], edges[i + 1]))
    return segs


def _xwall(x1, x2, z, y_fl, wins=(), col=_EXT_STONE, thick=WT):
    segs = _slice1d(x1, x2, [(w[0] - w[1] / 2, w[0] + w[1] / 2) for w in wins])
    for sx1, sx2 in segs:
        _solid((sx1 + sx2) / 2, y_fl, z, sx2 - sx1, FH, thick, col)
    for wx, ww, wy, wh in wins:
        if wy > 0:
            _solid(wx, y_fl, z, ww, wy, thick, col)
        above = FH - wy - wh
        if above > 0:
            _solid(wx, y_fl + wy + wh, z, ww, above, thick, col)
        _b((wx, y_fl + wy + wh / 2, z), (ww + 0.3, wh + 0.3, thick + 0.2), _WIN_FRM, coll=False)
        _b((wx, y_fl + wy + wh / 2, z), (ww - 0.1, wh - 0.1, 0.08), _WIN_GLS, coll=False)
        out_z = z - 4.0 if z <= (MZ1 + MZ2) / 2 else z + 4.0
        window_spawns.append(Vec3(wx, y_fl + 1.2, out_z))


def _zwall(z1, z2, x, y_fl, wins=(), col=_EXT_STONE, thick=WT):
    segs = _slice1d(z1, z2, [(w[0] - w[1] / 2, w[0] + w[1] / 2) for w in wins])
    for sz1, sz2 in segs:
        _solid(x, y_fl, (sz1 + sz2) / 2, thick, FH, sz2 - sz1, col)
    for wz, ww, wy, wh in wins:
        if wy > 0:
            _solid(x, y_fl, wz, thick, wy, ww, col)
        above = FH - wy - wh
        if above > 0:
            _solid(x, y_fl + wy + wh, wz, thick, above, ww, col)
        _b((x, y_fl + wy + wh / 2, wz), (thick + 0.2, wh + 0.3, ww + 0.3), _WIN_FRM, coll=False)
        _b((x, y_fl + wy + wh / 2, wz), (0.08, wh - 0.1, ww - 0.1), _WIN_GLS, coll=False)
        out_x = x - 4.0 if x <= (MX1 + MX2) / 2 else x + 4.0
        window_spawns.append(Vec3(out_x, y_fl + 1.2, wz))


def _xwall_door(x1, x2, z, y_fl, door_cx, door_w=DW, col=_PLASTER, thick=WT):
    segs = _slice1d(x1, x2, [(door_cx - door_w / 2, door_cx + door_w / 2)])
    for sx1, sx2 in segs:
        _solid((sx1 + sx2) / 2, y_fl, z, sx2 - sx1, FH, thick, col)
    above = FH - DH
    if above > 0:
        _solid(door_cx, y_fl + DH, z, door_w, above, thick, col)


def _zwall_door(z1, z2, x, y_fl, door_cz, door_w=DW, col=_PLASTER, thick=WT):
    segs = _slice1d(z1, z2, [(door_cz - door_w / 2, door_cz + door_w / 2)])
    for sz1, sz2 in segs:
        _solid(x, y_fl, (sz1 + sz2) / 2, thick, FH, sz2 - sz1, col)
    above = FH - DH
    if above > 0:
        _solid(x, y_fl + DH, door_cz, thick, above, door_w, col)


def _barrier(cx, y_fl, cz, w, h, d, cost):
    e = _b((cx, y_fl + h / 2, cz), (w, h, d), _BARRIER)
    rec = {'entity': e, 'cost': cost, 'open': False}
    door_barriers.append(rec)
    return rec


# ── Ground floor (y = 0..FH) ──────────────────────────────────────────────────
# Room layout (design doc, Z flipped from +north doc to +south code):
#   Grand Foyer    x:-20..20   z:-40..-14
#   Library        x:-60..-20  z:-40..-14
#   Ballroom       x: 20..60   z:-40..-14
#   Staircase Hall x:-20..20   z:-14..14
#   Kitchen        x:-60..-20  z:-14..14
#   Dining Room    x: 20..60   z:-14..14
#   Rear Hall      x:-20..20   z: 14..40
#   Servant's Qrtrs x:-60..-20 z: 14..40
#   Butler's Pantry x: 20..60  z: 14..40
def _build_ground(y):
    cy = y + FH - 0.31

    # --- Floors ---
    # Foyer: chequered tile — approximate with dark tile slab
    _slab(  0, y, -27, 40, 26, _FLOOR_TILE)
    _slab(-40, y, -27, 40, 26, _FLOOR_WOOD)   # Library
    _slab( 40, y, -27, 40, 26, _FLOOR_WOOD)   # Ballroom
    _slab(  0, y,   0, 40, 28, _FLOOR_SLT)    # Staircase Hall
    _slab(-40, y,   0, 40, 28, _FLOOR_WOOD)   # Kitchen
    _slab( 40, y,   0, 40, 28, _FLOOR_WOOD)   # Dining Room
    _slab(  0, y,  27, 40, 26, _FLOOR_SLT)    # Rear Hall
    _slab(-40, y,  27, 40, 26, _FLOOR_WOOD)   # Servant's Quarters
    _slab( 40, y,  27, 40, 26, _FLOOR_WOOD)   # Butler's Pantry

    # --- Ceilings (staircase hall open shaft) ---
    _slab(  0, cy, -27, 40, 26, _CEIL_COL)
    _slab(-40, cy, -27, 40, 26, _CEIL_COL)
    _slab( 40, cy, -27, 40, 26, _CEIL_COL)
    # Staircase Hall omitted — open shaft
    _slab(-40, cy,   0, 40, 28, _CEIL_COL)
    _slab( 40, cy,   0, 40, 28, _CEIL_COL)
    _slab(  0, cy,  27, 40, 26, _CEIL_COL)
    _slab(-40, cy,  27, 40, 26, _CEIL_COL)
    _slab( 40, cy,  27, 40, 26, _CEIL_COL)

    # --- Exterior walls ---
    # Front z=MZ1=-40
    _xwall(MX1, -20, MZ1, y, wins=[(-44, 4, 1.5, 3.5)])
    _xwall(-20,  20, MZ1, y, wins=[(  0, 6, 1.0, 4.5)])   # double front doors (tall)
    _xwall( 20, MX2, MZ1, y, wins=[( 44, 4, 1.5, 3.5)])
    # Left x=MX1=-60
    _zwall(MZ1, -14, MX1, y, wins=[(-28, 4, 1.5, 3.5)])
    _zwall(-14,  14, MX1, y, wins=[(  0, 4, 1.5, 3.5)])
    _zwall( 14, MZ2, MX1, y, wins=[( 28, 4, 1.5, 3.5)])
    # Right x=MX2=60
    _zwall(MZ1, -14, MX2, y, wins=[(-28, 4, 1.5, 3.5)])
    _zwall(-14,  14, MX2, y, wins=[(  0, 4, 1.5, 3.5)])
    _zwall( 14, MZ2, MX2, y, wins=[( 28, 4, 1.5, 3.5)])
    # Back z=MZ2=40
    _xwall(MX1, -20, MZ2, y, wins=[(-40, 4, 1.5, 3.5)])
    _xwall(-20,  20, MZ2, y, wins=[(  0, 5, 1.0, 4.0)])   # rear doors
    _xwall( 20, MX2, MZ2, y, wins=[( 40, 4, 1.5, 3.5)])

    # --- Interior partitions ---
    # Foyer south wall (arch to staircase hall)
    _xwall_door(-20, 20, -14, y, door_cx=0,   door_w=10.0, col=_PLASTER)
    # Library | Foyer
    _zwall_door(MZ1, -14, -20, y, door_cz=-27, col=_PLASTER)
    # Ballroom | Foyer
    _zwall_door(MZ1, -14,  20, y, door_cz=-27, col=_PLASTER)
    # Kitchen | Staircase
    _zwall_door(-14, 14, -20, y, door_cz=0, col=_PLASTER)
    # Dining | Staircase
    _zwall_door(-14, 14,  20, y, door_cz=0, col=_PLASTER)
    # Rear Hall north wall
    _xwall_door(-20, 20, 14, y, door_cx=0, door_w=8.0, col=_PLASTER)
    # Servant's | Rear Hall
    _zwall_door(14, MZ2, -20, y, door_cz=27, col=_PLASTER)
    # Butler's | Rear Hall
    _zwall_door(14, MZ2,  20, y, door_cz=27, col=_PLASTER)
    # Library | Kitchen divider
    _xwall_door(MX1, -20, -14, y, door_cx=-40, col=_PLASTER)
    # Ballroom | Dining divider
    _xwall_door( 20, MX2, -14, y, door_cx= 40, col=_PLASTER)
    # Servant's | Kitchen divider
    _xwall_door(MX1, -20, 14, y, door_cx=-40, col=_PLASTER)
    # Butler's | Dining divider
    _xwall_door( 20, MX2, 14, y, door_cx= 40, col=_PLASTER)

    # --- Barriers ---
    _barrier(-20, y, -27, WT+0.1, DH, DW,   500)   # Foyer → Library
    _barrier( 20, y, -27, WT+0.1, DH, DW,   500)   # Foyer → Ballroom
    _barrier(  0, y,  14, 10.0,   DH, WT+0.1, 750) # Staircase → Rear Hall
    _barrier(  0, y,  40, 10.0,   DH, WT+0.1, 1500)# Rear → Backyard (back doors)


# ── Upper floor (y = FH..2*FH) ────────────────────────────────────────────────
# Grand Foyer ceiling → Upper Landing / Study / Master Bedroom area
#   Study / Office     x:-60..-20  z:-40..-14
#   Master Bedroom     x: 20..60   z:-40..-14
#   Upper Landing      x:-20..20   z:-40..14   (open staircase shaft, no ceiling)
#   Trophy Room        x:-60..-20  z:-14..14
#   Guest Bedroom      x: 20..60   z:-14..14
#   Upper Corridor     x:-20..20   z:-14..14
#   Hidden Passage     narrow, behind kitchen/study (no separate room)
def _build_upper(y):
    cy = y + FH - 0.31

    # Floors
    _slab(-40, y, -27, 40, 26, _FLOOR_WOOD)   # Study
    _slab( 40, y, -27, 40, 26, _FLOOR_WOOD)   # Master Bedroom
    _slab(  0, y, -13, 40, 54, _FLOOR_SLT)    # Upper Landing + Corridor combined
    _slab(-40, y,   0, 40, 28, _FLOOR_WOOD)   # Trophy Room
    _slab( 40, y,   0, 40, 28, _FLOOR_WOOD)   # Guest Bedroom
    _slab(-40, y,  27, 40, 26, _FLOOR_WOOD)   # Servant's upper (unused/open)
    _slab( 40, y,  27, 40, 26, _FLOOR_WOOD)   # Rear upper

    # Ceilings (landing shaft open)
    _slab(-40, cy, -27, 40, 26, _CEIL_COL)
    _slab( 40, cy, -27, 40, 26, _CEIL_COL)
    # Upper Landing/Corridor — omit ceiling (open staircase shaft continues up)
    _slab(-40, cy,   0, 40, 28, _CEIL_COL)
    _slab( 40, cy,   0, 40, 28, _CEIL_COL)
    _slab(-40, cy,  27, 40, 26, _CEIL_COL)
    _slab( 40, cy,  27, 40, 26, _CEIL_COL)

    # Exterior walls
    _xwall(MX1, -20, MZ1, y, wins=[(-40, 4, 1.5, 3.5)])
    _xwall(-20,  20, MZ1, y, wins=[(  0, 8, 1.0, 4.0)])   # front balcony opening
    _xwall( 20, MX2, MZ1, y, wins=[( 40, 4, 1.5, 3.5)])
    _zwall(MZ1, -14, MX1, y, wins=[(-28, 4, 1.5, 3.5)])
    _zwall(-14,  14, MX1, y, wins=[(  0, 4, 1.5, 3.5)])
    _zwall( 14, MZ2, MX1, y, wins=[( 28, 4, 1.5, 3.5)])
    _zwall(MZ1, -14, MX2, y, wins=[(-28, 4, 1.5, 3.5)])
    _zwall(-14,  14, MX2, y, wins=[(  0, 4, 1.5, 3.5)])
    _zwall( 14, MZ2, MX2, y, wins=[( 28, 4, 1.5, 3.5)])
    _xwall(MX1, -20, MZ2, y)
    _xwall(-20,  20, MZ2, y)
    _xwall( 20, MX2, MZ2, y)

    # Interior partitions
    _zwall_door(MZ1, -14, -20, y, door_cz=-27, col=_PLASTER)
    _zwall_door(MZ1, -14,  20, y, door_cz=-27, col=_PLASTER)
    _xwall_door(-20, 20, -14, y, door_cx=0, door_w=10.0, col=_PLASTER)
    _zwall_door(-14, 14, -20, y, door_cz=0, col=_PLASTER)
    _zwall_door(-14, 14,  20, y, door_cz=0, col=_PLASTER)
    _xwall_door(MX1, -20, -14, y, door_cx=-40, col=_PLASTER)
    _xwall_door( 20, MX2, -14, y, door_cx= 40, col=_PLASTER)
    _xwall_door(-20, 20, 14, y, door_cx=0, door_w=8.0, col=_PLASTER)
    _xwall_door(MX1, -20, 14, y, door_cx=-40, col=_PLASTER)
    _xwall_door( 20, MX2, 14, y, door_cx= 40, col=_PLASTER)
    _zwall_door(14, MZ2, -20, y, door_cz=27, col=_PLASTER)
    _zwall_door(14, MZ2,  20, y, door_cz=27, col=_PLASTER)

    # Barriers
    _barrier(-20, y, -27, WT+0.1, DH, DW,  1000)
    _barrier( 20, y, -27, WT+0.1, DH, DW,  1000)
    _barrier(-20, y,   0, WT+0.1, DH, DW,  1250)  # Trophy Room barrier


# ── Rooftop (y = 2*FH) ────────────────────────────────────────────────────────
def _build_rooftop(y):
    _slab(0, y, 0, 122, 82, _ROOF_COL, thick=0.5)
    ph = 2.5
    _solid(  0, y + 0.5, MZ1, 122, ph, WT, _PARAPET)
    _solid(  0, y + 0.5, MZ2, 122, ph, WT, _PARAPET)
    _solid(MX1, y + 0.5,   0, WT, ph,  82, _PARAPET)
    _solid(MX2, y + 0.5,   0, WT, ph,  82, _PARAPET)
    # Observatory tower stub (SE corner) — just a raised platform
    _b((50, y + 0.5 + 4, 28), (10, 8, 10), _EXT_STONE)


# ── Basement (y = -FH..0) ─────────────────────────────────────────────────────
# Wine Cellar   x:-60..-10  z:-20..0
# Boiler Room   x:-10..10   z:-20..20
# Storage Room  x: 10..60   z:-20..0
# Ritual Chamber x:-60..-10 z: 0..20
# Central Vault  x: 10..60  z: 0..20
def _build_basement(y):
    cy = y + FH - 0.31

    _slab(-35, y, -10, 50, 20, _FLOOR_SLT)   # Wine Cellar
    _slab(  0, y,   0, 20, 40, _FLOOR_SLT)   # Boiler Room
    _slab( 35, y, -10, 50, 20, _FLOOR_SLT)   # Storage
    _slab(-35, y,  10, 50, 20, _FLOOR_SLT)   # Ritual Chamber
    _slab( 35, y,  10, 50, 20, _FLOOR_SLT)   # Central Vault

    _slab(-35, cy, -10, 50, 20, _INT_STONE)
    _slab(  0, cy,   0, 20, 40, _INT_STONE)
    _slab( 35, cy, -10, 50, 20, _INT_STONE)
    _slab(-35, cy,  10, 50, 20, _INT_STONE)
    _slab( 35, cy,  10, 50, 20, _INT_STONE)

    BX1, BX2, BZ1, BZ2 = -60.0, 60.0, -20.0, 20.0
    _xwall(BX1, BX2, BZ1, y, wins=[(0, 4, 1.0, 3.0)], col=_INT_STONE)
    _xwall(BX1, BX2, BZ2, y, col=_INT_STONE)
    _zwall(BZ1, BZ2, BX1, y, wins=[(0, 4, 1.0, 3.0)], col=_INT_STONE)
    _zwall(BZ1, BZ2, BX2, y, wins=[(0, 4, 1.0, 3.0)], col=_INT_STONE)

    _zwall_door(BZ1, BZ2, -10, y, door_cz=0, col=_INT_STONE)
    _zwall_door(BZ1, BZ2,  10, y, door_cz=0, col=_INT_STONE)
    _xwall_door(BX1, BX2,   0, y, door_cx=-35, col=_INT_STONE)
    _xwall_door(BX1, BX2,   0, y, door_cx= 35, col=_INT_STONE)

    # Boiler prop
    _b((0, y + 3, 10), (6, 6, 6), color.rgb32(55, 40, 35))

    # Barriers
    _barrier(-10, y, -10, WT+0.1, DH, DW, 1500)  # Wine Cellar entry
    _barrier( 10, y,  10, WT+0.1, DH, DW, 2000)  # Ritual Chamber entry


# ── Staircases ────────────────────────────────────────────────────────────────
def _build_stairs():
    # Ground → Upper (Staircase Hall, z: -14..2, ascending +z)
    _steps(0, 0, -14, 16, FH, 16)

    # Upper → Rooftop (continuing shaft, z: 2..18)
    _steps(0, FH, 2, 14, FH, 16)

    # Basement (descending, z: 2..22)
    _steps_down(0, 0, 2, 12, FH, 20)
    _barrier(0, -0.2, 2, 12, DH, WT + 0.1, 1000)


# ── Front yard & road ─────────────────────────────────────────────────────────
def _build_front_yard():
    # Ground planes
    _slab(0, -0.35, (FY_Z1 + FY_Z2) / 2, OUT_X2 - OUT_X1, FY_Z2 - FY_Z1, _GRASS, thick=0.35)
    _slab(0, -0.35, (RD_Z1 + RD_Z2) / 2, OUT_X2 - OUT_X1, RD_Z2 - RD_Z1, _ROAD, thick=0.35)

    # Iron fence across front yard, gap in middle for gate
    gate_half = 5.0
    _solid(-50,          -0.35, FY_Z1, OUT_X2 - gate_half - 50, 3.5, WT, _FENCE)
    _solid( 50,          -0.35, FY_Z1, OUT_X2 - gate_half - 50, 3.5, WT, _FENCE)
    # Gate posts
    _b((-gate_half - 1, -0.35 + 2.5, FY_Z1), (0.8, 5.0, 0.8), _FENCE)
    _b(( gate_half + 1, -0.35 + 2.5, FY_Z1), (0.8, 5.0, 0.8), _FENCE)

    # Gravestones (6)
    for gx, gz in [(-30, -85), (-15, -78), (5, -82), (20, -73), (-25, -68), (12, -65)]:
        _b((gx, 0.5, gz), (1.5, 2.0, 0.3), color.rgb32(80, 78, 74))

    # Dry fountain (centre of front yard)
    _b((0, 0.4, -70), (5, 0.8, 5), color.rgb32(88, 84, 78))
    _b((0, 0.8, -70), (3, 0.5, 3), color.rgb32(78, 74, 68))

    # Gravel path from gate to mansion front door
    _slab(0, -0.2, -57.5, 8, 15, _GRAVEL, thick=0.2)

    # Window spawns from fence gaps (front entry points)
    for gx in [-40, -20, 20, 40]:
        window_spawns.append(Vec3(gx, 1.0, FY_Z1 - 2))


# ── Backyard ──────────────────────────────────────────────────────────────────
def _build_backyard():
    # Ground
    _slab(0, -0.35, (BY_Z1 + BY_Z2) / 2, OUT_X2 - OUT_X1, BY_Z2 - BY_Z1, _GRASS, thick=0.35)

    # Swimming pool (left side) x:-90..-40, z:55..80
    pool_cx, pool_cz = -65.0, 67.5
    pool_w, pool_d   = 50.0, 25.0
    pool_depth       = 2.0
    # Pool surround
    _slab(pool_cx, 0.0, pool_cz, pool_w + 2, pool_d + 2, _POOL_TILE, thick=0.3)
    # Pool water (recessed floor)
    _slab(pool_cx, -pool_depth, pool_cz, pool_w - 1, pool_d - 1, _POOL_WATER, thick=0.2)
    # Pool walls (sides so player can't walk into void)
    _solid(pool_cx,            -pool_depth, pool_cz - pool_d/2, pool_w, pool_depth, WT, _POOL_TILE)
    _solid(pool_cx,            -pool_depth, pool_cz + pool_d/2, pool_w, pool_depth, WT, _POOL_TILE)
    _solid(pool_cx - pool_w/2, -pool_depth, pool_cz, WT, pool_depth, pool_d, _POOL_TILE)
    _solid(pool_cx + pool_w/2, -pool_depth, pool_cz, WT, pool_depth, pool_d, _POOL_TILE)
    # Diving board
    _b((pool_cx - pool_w/2 + 2, 1.2, pool_cz), (5, 0.3, 1.2), color.rgb32(80, 70, 60))

    # Stone path down the centre
    _slab(0, -0.1, 70, 8, 55, _GRAVEL, thick=0.2)

    # Stone angel statue
    _b((0, 1.2, 80), (2, 3, 2), color.rgb32(130, 125, 118))

    # Swing set (right side) x:40..75, z:55..85
    sw_cx = 57.5
    _b((sw_cx - 7, 3.5, 70), (1.0, 7.0, 1.0), _FENCE)   # left post
    _b((sw_cx + 7, 3.5, 70), (1.0, 7.0, 1.0), _FENCE)   # right post
    _b((sw_cx,     7.0, 70), (15, 0.4, 0.4), _FENCE)    # top bar
    _b((sw_cx - 3, 3.5, 70), (0.2, 6.0, 0.2), _FENCE)  # chain L
    _b((sw_cx + 3, 3.5, 70), (0.2, 6.0, 0.2), _FENCE)  # chain R
    _b((sw_cx,     0.6, 70), (3.0, 0.4, 0.8), color.rgb32(60, 40, 20))  # seat
    # Iron bench
    _b((55, 0.5, 80), (5, 1.0, 1.8), color.rgb32(40, 38, 36))

    # Stone bench near path
    _b((-12, 0.5, 72), (4, 0.8, 1.5), color.rgb32(90, 85, 78))
    _b(( 12, 0.5, 72), (4, 0.8, 1.5), color.rgb32(90, 85, 78))

    # Crumbling wall separating yard from greenhouse
    _solid(0, 0, 108, 200, 2.5, WT, _EXT_STONE)
    # Gap in wall for greenhouse access
    _barrier(0, 0, 108, 10, DH, WT + 0.1, 2500)  # Greenhouse 2500pts

    # Pool zombie spawn points
    for gx in [-75, -65, -55]:
        window_spawns.append(Vec3(gx, 1.0, BY_Z1 + 2))


# ── Greenhouse ────────────────────────────────────────────────────────────────
def _build_greenhouse():
    GH_CX  = 0.0
    GH_CZ  = (GH_Z1 + GH_Z2) / 2   # 132.5
    GH_W   = 55.0
    GH_D   = 35.0
    GH_H   = 6.0

    # Floor
    _slab(GH_CX, -0.2, GH_CZ, GH_W, GH_D, _GH_IRON, thick=0.3)

    # Walls (tarnished iron frames — low opacity glass panes approximate)
    _solid(GH_CX,            0, GH_Z1, GH_W, GH_H, WT, _GH_IRON)
    _solid(GH_CX,            0, GH_Z2, GH_W, GH_H, WT, _GH_IRON)
    _solid(GH_CX - GH_W / 2, 0, GH_CZ, WT, GH_H, GH_D, _GH_IRON)
    _solid(GH_CX + GH_W / 2, 0, GH_CZ, WT, GH_H, GH_D, _GH_IRON)

    # Roof slab
    _slab(GH_CX, GH_H, GH_CZ, GH_W, GH_D, _GH_IRON, thick=0.3)

    # Door opening in front wall (already covered by barrier in backyard)
    # Vine / plant props (purely visual, no collider)
    for vx, vz in [(-18, 120), (10, 125), (-5, 135), (20, 130), (-22, 140)]:
        _b((vx, 1.5, vz), (3, 3, 3), color.rgb32(30, 55, 20), coll=False)

    # Trapdoor hint
    _b((0, 0.1, GH_CZ + 5), (2.5, 0.15, 2.5), color.rgb32(45, 32, 18))

    # Zombie spawn (side vent)
    window_spawns.append(Vec3(GH_CX + GH_W / 2 + 2, 1.0, GH_CZ))


# ── Underground tunnel (basement → greenhouse) ────────────────────────────────
def _build_tunnel():
    # Runs z: 20 (basement) → 115 (greenhouse trapdoor), y: -FH
    TY = -FH
    TL = 95.0   # length
    TW = 3.0
    TH = 3.5
    tz_center = (20 + 115) / 2   # 67.5
    _slab(0, TY, tz_center, TW, TL, _INT_STONE, thick=0.3)         # floor
    _solid(0, TY, 20,       TW, TH, WT, _INT_STONE)                # south cap
    _solid(0, TY, 115,      TW, TH, WT, _INT_STONE)                # north cap
    _solid(-TW/2, TY, tz_center, WT, TH, TL, _INT_STONE)           # left wall
    _solid( TW/2, TY, tz_center, WT, TH, TL, _INT_STONE)           # right wall
    _slab(0, TY + TH, tz_center, TW, TL, _INT_STONE, thick=0.3)    # ceiling


# ── Mansion facade detail ─────────────────────────────────────────────────────
def _build_facade():
    y = 0
    # Portico — 3-step stone plinth
    for i, (sh, sz) in enumerate([(0.4, MZ1 - 1.0), (0.8, MZ1 - 2.0), (1.2, MZ1 - 3.0)]):
        _b((0, sh / 2, sz), (12, sh, 1.5), color.rgb32(75, 72, 68))
    # Columns either side of front door
    for cx in [-8.0, 8.0]:
        _b((cx, y + 5.0, MZ1 - 3.5), (1.2, 10.0, 1.2), color.rgb32(80, 76, 72))
    # Portico lintel
    _b((0, y + 10.3, MZ1 - 2.0), (20, 0.7, 6), color.rgb32(75, 72, 68))


# ── Lighting ──────────────────────────────────────────────────────────────────
def _build_lighting():
    moon = DirectionalLight()
    moon.look_at(Vec3(0.4, -1, 0.25))
    moon.color = color.rgb32(140, 155, 180)   # pale blue-white moonlight
    AmbientLight(color=color.rgba32(20, 18, 28, 255))
    sky = Sky()
    sky.color = color.rgb32(8, 10, 22)        # near-black night sky


# ── Main entry ────────────────────────────────────────────────────────────────
def create_zombies_map():
    window_spawns.clear()
    door_barriers.clear()

    # Single unified ground plane (mansion sits on top)
    _slab(0, -0.4, 0, 300, 300, _GRASS, thick=0.4)

    _build_ground(0)
    _build_upper(FH)
    _build_rooftop(FH * 2)
    _build_basement(-FH)
    _build_stairs()
    _build_facade()
    _build_front_yard()
    _build_backyard()
    _build_greenhouse()
    _build_tunnel()
    _build_lighting()

    return {
        'window_spawns': window_spawns,
        'door_barriers': door_barriers,
        'player_spawn':  player_spawn,
    }
