from ursina import *

# ── Point reward constants ────────────────────────────────────────────────────
HIT_REWARD           = 10    # every bullet that connects
KILL_REWARD          = 50    # bonus when zombie dies (normal)
HEADSHOT_KILL_REWARD = 100   # bonus when zombie dies via headshot

# ── State ─────────────────────────────────────────────────────────────────────
points     = 0
_hud_pts   = None   # bottom-left counter
_hud_delta = None   # transient "+N pts" line below counter
_flash_t   = 0.0
_delta_t   = 0.0
_FLASH_DUR = 1.0
_DELTA_DUR = 1.2


def init_hud():
    global _hud_pts, _hud_delta, points
    points = 0

    _hud_pts = Text(
        text='0 pts',
        position=(-0.84, -0.43),
        origin=(-0.5, 0),
        scale=2.2,
        color=color.white,
        parent=camera.ui,
    )
    _hud_delta = Text(
        text='',
        position=(-0.84, -0.48),
        origin=(-0.5, 0),
        scale=1.4,
        color=color.yellow,
        parent=camera.ui,
        enabled=False,
    )


def add_points(amount, label=None):
    global points, _flash_t, _delta_t
    points  += amount
    _flash_t = _FLASH_DUR
    _delta_t = _DELTA_DUR
    _refresh_hud()
    if _hud_delta:
        _hud_delta.text    = label if label else f'+{amount} pts'
        _hud_delta.enabled = True
        _hud_delta.color   = color.yellow


def spend_points(amount):
    global points
    if points < amount:
        return False
    points -= amount
    _refresh_hud()
    return True


def _refresh_hud():
    if _hud_pts:
        _hud_pts.text = f'{points:,} pts'


def update(dt):
    global _flash_t, _delta_t

    if _hud_pts is None:
        return

    # Flash counter yellow → white
    if _flash_t > 0:
        _flash_t = max(0.0, _flash_t - dt)
        t = _flash_t / _FLASH_DUR          # 1 → 0
        b = int(lerp(255, 0, t))           # 0 → 255 (white) as t fades
        _hud_pts.color = color.rgb32(255, 255, b)
    else:
        _hud_pts.color = color.white

    # Fade out delta line
    if _delta_t > 0:
        _delta_t = max(0.0, _delta_t - dt)
        alpha = _delta_t / _DELTA_DUR
        _hud_delta.color = color.rgba(1, 1, 0, alpha)
        if _delta_t == 0:
            _hud_delta.enabled = False


# ── Convenience callbacks (called by zombie hit/kill logic) ───────────────────
def on_hit(world_pos=None):
    add_points(HIT_REWARD, f'+{HIT_REWARD}')


def on_kill(headshot=False, world_pos=None):
    reward = HEADSHOT_KILL_REWARD if headshot else KILL_REWARD
    label  = f'+{reward}  HEADSHOT!' if headshot else f'+{reward}  KILL'
    add_points(reward, label)
