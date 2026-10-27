#!/usr/bin/env python3
"""Frames of the Capri mascot for the lock screen (gits-lock-mascot, the Edgerunners theme): braille art, capri-0.txt ... next to this file.

A rogue engram given a body of slime: a girl modelled from soft signed-distance blobs joined with a wide smooth-union, so she runs
together like goo. Her feet melt into a puddle, her surface wobbles, drops fall from her lowered hand and she reaches up with the
other one (for the moon on the wallpaper). Ray-marched with numpy, swaying a little; shading is an ordered (Bayer) dither, the eyes
always lit. Drawn from code, an interpretation only: nothing is traced from the show.
  capri.py [COLUMNS [ROWS [FRAMES]]]   default 34 x 26, 24 frames (3 s a loop at 8 frames a second).  Needs numpy.
  capri.py --sprite DIR                 dancer-0.png ... dancer-15.png in DIR instead: RGBA frames for the radio popup
                                        (gits-widgets/dancer.py); needs Pillow too."""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SPRITE = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--sprite" else None
if SPRITE:
    sys.argv = sys.argv[:1]
COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 34
ROWS = int(sys.argv[2]) if len(sys.argv) > 2 else 26
FRAMES = int(sys.argv[3]) if len(sys.argv) > 3 else 24
SS = 2  # supersampling per dot
BITS = {(0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (0, 3): 0x40, (1, 3): 0x80}
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 + 1 / 32


def length(v):
    return np.sqrt((v * v).sum(-1))


def ellipsoid(p, c, r):
    r = np.asarray(r, float)
    q = (p - c) / r
    return (length(q) - 1) * r.min()


def capsule(p, a, b, r):
    a, b = np.asarray(a, float), np.asarray(b, float)
    pa, ba = p - a, b - a
    h = np.clip((pa * ba).sum(-1) / (ba * ba).sum(), 0, 1)
    return length(pa - ba * h[..., None]) - r


def smin(a, b, k=0.08):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


EYES = ((0.045, 1.80, 0.125), (-0.045, 1.80, 0.125))


def eyes(p):
    return np.min([ellipsoid(p, e, (0.026, 0.016, 0.03)) for e in EYES], axis=0)


def drops(t):
    """Where the falling drops are at loop time t (0..1): three from the lowered hand, each falling into the puddle."""
    out = []
    for k in range(3):
        f = (t * 2 + k / 3) % 1
        out.append(((-0.35 - 0.03 * f, 0.88 - 0.84 * f ** 1.6, 0.04), 0.03 + 0.012 * (1 - f)))
    return out


def scene(p, t):
    a = t * 2 * math.pi
    sway = 0.03 * math.sin(a)
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    d = ellipsoid(p, (sway, 1.80, 0.01), (0.115, 0.145, 0.12))                                # head
    d = smin(d, ellipsoid(p, (sway, 1.86, -0.03), (0.15, 0.12, 0.14)), 0.05)                   # hair on top
    for sx in (1, -1):                                                                        # two long strands of slime hair
        tip = (0.2 * sx + sway * 2, 1.30 + 0.03 * math.sin(a + sx), -0.03)
        d = smin(d, capsule(p, (0.11 * sx + sway, 1.84, -0.02), tip, 0.045), 0.06)
        d = smin(d, ellipsoid(p, (tip[0], tip[1] - 0.05, tip[2]), (0.035, 0.06, 0.035)), 0.04)  # a drop hanging off the end
    d = smin(d, capsule(p, (sway, 1.66, 0), (sway * 0.6, 1.52, 0), 0.045), 0.05)              # neck
    d = smin(d, ellipsoid(p, (sway * 0.5, 1.42, 0.01), (0.17, 0.13, 0.1)), 0.06)              # chest
    d = smin(d, capsule(p, (sway * 0.5, 1.34, 0), (0, 1.1, 0), 0.075), 0.08)                  # waist
    d = smin(d, ellipsoid(p, (0, 1.0, 0), (0.18, 0.12, 0.11)), 0.08)                          # hips
    for sx in (1, -1):                                                                        # legs
        d = smin(d, capsule(p, (0.08 * sx, 0.95, 0), (0.08 * sx, 0.52, 0.02), 0.06), 0.05)
        d = smin(d, capsule(p, (0.08 * sx, 0.52, 0.02), (0.09 * sx, 0.08, 0), 0.042), 0.05)
    reach = 0.04 * math.sin(a + 1)                                                            # the raised arm, reaching
    d = smin(d, capsule(p, (0.16, 1.5, 0), (0.33, 1.80 + reach, 0.04), 0.04), 0.05)
    d = smin(d, capsule(p, (0.33, 1.80 + reach, 0.04), (0.40, 2.14 + reach * 2, 0.06), 0.034), 0.04)
    d = smin(d, capsule(p, (-0.16, 1.5, 0), (-0.27, 1.18, 0.02), 0.04), 0.05)                 # the lowered arm, dripping
    d = smin(d, capsule(p, (-0.27, 1.18, 0.02), (-0.34, 0.92, 0.04), 0.036), 0.05)
    pool = 0.40 + 0.03 * math.sin(a * 2)
    d = smin(d, ellipsoid(p, (0, 0.0, 0), (pool, 0.06, pool * 0.75)), 0.18)                   # the puddle she stands in
    for c, r in drops(t):
        d = smin(d, length(p - np.array(c)) - r, 0.04)
    # goo: the surface ripples, slower low down
    d = d + 0.012 * np.sin(y * 14 - a * 2) * np.sin(x * 11 + z * 9 + a)
    return np.minimum(d, eyes(p))


def normal(p, t):
    e = 0.004
    n = np.stack([scene(p + np.array(v) * e, t) - scene(p - np.array(v) * e, t)
                  for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))], -1)
    return n / np.maximum(length(n)[..., None], 1e-9)


def render(t, W, H):
    """Orthographic camera a little above her, swaying +-20 degrees around her. Returns brightness 0..1 per dot."""
    w, h = W * SS, H * SS
    span_y = 2.5
    span_x = span_y * w / h  # braille dots are square
    xs = (np.arange(w) + 0.5) / w * span_x - span_x / 2
    ys = (1 - (np.arange(h) + 0.5) / h) * span_y - span_y / 2
    X, Y = np.meshgrid(xs, ys)
    yaw = math.radians(90 + 20 * math.sin(t * 2 * math.pi))
    el = math.radians(8)
    fwd = np.array([-math.cos(el) * math.cos(yaw), -math.sin(el), -math.cos(el) * math.sin(yaw)])
    right = np.array([-math.sin(yaw), 0, math.cos(yaw)])
    up = np.cross(fwd, right)
    target = np.array([0.04, 1.15, 0])
    o = target - fwd * 6 + X[..., None] * right + Y[..., None] * up
    tt = np.zeros(X.shape)
    hit = np.zeros(X.shape, bool)
    live = np.ones(X.shape, bool)  # rays still marching: only those are evaluated
    for _ in range(72):
        idx = np.nonzero(live)
        if not idx[0].size:
            break
        d = scene(o[idx] + fwd * tt[idx][..., None], t)
        tt[idx] += d * 0.8   # the ripple bends the distance field: step a little short
        done = d < 0.003
        hit[idx[0][done], idx[1][done]] = True
        live[idx[0][done | (tt[idx] > 9)], idx[1][done | (tt[idx] > 9)]] = False
    lum = np.zeros(X.shape)
    if hit.any():
        p = o[hit] + fwd * tt[hit][..., None]
        n = normal(p, t)
        light = np.array([0.5, 0.75, 0.45])
        light /= np.linalg.norm(light)
        diff = np.clip((n * light).sum(-1), 0, 1)
        half = light - fwd
        half /= np.linalg.norm(half)
        spec = np.clip((n * half).sum(-1), 0, 1) ** 24          # wet highlights
        rim = np.clip(1 + (n * fwd).sum(-1), 0, 1) ** 3
        shade = np.clip(0.18 + 0.75 * diff + 0.9 * spec + 0.5 * rim, 0, 1)
        lum[hit] = np.where(eyes(p) < 0.01, 1.0, shade)
    return lum.reshape(H, SS, W, SS).mean((1, 3))


def braille(lum):
    H, W = lum.shape
    yy, xx = np.mgrid[0:H, 0:W]
    dots = lum > BAYER[yy % 4, xx % 4]
    lines = []
    for r in range(H // 4):
        line = ""
        for c in range(W // 2):
            code = 0
            for (dx, dy), bit in BITS.items():
                if dots[r * 4 + dy, c * 2 + dx]:
                    code |= bit
            line += chr(0x2800 + code)
        lines.append(line.rstrip("⠀") or "⠀")
    return "\n".join(lines)


def sprite(out, frames=16, w=180, h=260):
    """Capri as RGBA frames: brightness as grey, coverage as alpha (dancer.py tints them like the dancing Lain)."""
    from PIL import Image
    os.makedirs(out, exist_ok=True)
    for old in os.listdir(out):
        if old.startswith("dancer-") and old.endswith(".png"):
            os.remove(os.path.join(out, old))
    for n in range(frames):
        lum = render(n / frames, w, h)
        g = (np.clip(lum, 0, 1) * 255).astype("uint8")
        a = (np.clip(lum * 4, 0, 1) * 255).astype("uint8")
        Image.fromarray(np.dstack([g, g, g, a]), "RGBA").save(os.path.join(out, f"dancer-{n}.png"))
    print(f"{frames} sprite frames of {w}x{h} in {out}")


def main():
    if SPRITE:
        return sprite(SPRITE)
    for old in os.listdir(HERE):
        if old.startswith("capri-") and old.endswith(".txt"):
            os.remove(os.path.join(HERE, old))
    for n in range(FRAMES):
        with open(os.path.join(HERE, f"capri-{n}.txt"), "w", encoding="utf-8") as fh:
            fh.write(braille(render(n / FRAMES, COLS * 2, ROWS * 4)))
    print(f"{FRAMES} frames of {COLS}x{ROWS} braille cells in {HERE}")


if __name__ == "__main__":
    main()
