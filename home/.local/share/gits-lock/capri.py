#!/usr/bin/env python3
"""Frames of the Capri mascot for the lock screen (gits-lock-mascot, the Edgerunners theme): braille art, capri-0.txt ... next to this file.

Capri, the rogue engram of Cyberpunk: Edgerunners 2, as flat graphics: a mane of jagged crimson shards full of glitter, black blades
rimmed violet, a huge mane over a small face low in it: two lime plates either side of a black wedge, a big round blue eye in each
with black lashes, a thin white zigzag for a mouth, a thin black body under it. The mane and the bangs sway,
the glitter twinkles, the eyes look about and blink, the mouth wiggles. Drawn from code after the general motifs only,
nothing is traced from the show.
In braille every colour is a dot density: the glitter, the mouth and the pupils solid, the face dense, the irises medium, the
slime sparse, black empty.
  capri.py [COLUMNS [ROWS [FRAMES]]]   default 48 x 26, 24 frames (3 s a loop at 8 frames a second).  Needs Pillow and numpy.
  capri.py --sprite DIR                 dancer-0.png ... dancer-15.png in DIR instead: the same drawing in colour for the radio popup
                                        (gits-widgets/dancer.py)."""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SPRITE = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--sprite" else None
if SPRITE:
    sys.argv = sys.argv[:1]
COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 48
ROWS = int(sys.argv[2]) if len(sys.argv) > 2 else 26
FRAMES = int(sys.argv[3]) if len(sys.argv) > 3 else 24
SS = 4  # supersampling per dot
BITS = {(0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (0, 3): 0x40, (1, 3): 0x80}
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 + 1 / 32

# the colours of the drawing, and what each one becomes in braille (a grey level: the share of dots that are set)
COLOUR = dict(slime=(236, 22, 82), glitter=(255, 196, 222), ink=(10, 6, 18), edge=(108, 58, 236), face=(56, 238, 128),
              iris=(30, 90, 236), white=(250, 250, 252))
LEVEL = dict(slime=(64,) * 3, glitter=(64,) * 3, ink=(0,) * 3, edge=(0,) * 3, face=(200,) * 3, iris=(110,) * 3, white=(255,) * 3)

# the shards of the mane: angle (degrees, 0 = right, 90 = down), length, half width at the root, phase; crimson ones and dark ones
_R = random.Random(2)
SHARDS = [(_R.uniform(-185, 5) if k % 3 else _R.choice((_R.uniform(15, 55), _R.uniform(125, 165))), _R.uniform(0.32, 0.55),
           _R.uniform(0.04, 0.09), _R.random(), k % 5 == 0) for k in range(34)]
GLITTER = [(_R.random(), _R.random(), _R.random()) for _ in range(1800)]
EYES = ((0.405, 0.46, 0.06, 0.0), (0.61, 0.455, 0.06, 0.4))   # centre, radius, a phase for where it looks and when it blinks


def draw(t, W, H, pal, zoom=1.0):
    """One frame at loop time t (0..1) as an RGBA image W x H, in the palette pal (COLOUR or LEVEL); zoom > 1 closes in on the face."""
    a = t * 2 * math.pi
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = min(W, H) * zoom
    ox, oy = W / 2 - 0.5 * s, H / 2 - (0.5 - 0.06 * (zoom - 1)) * s
    lw = max(1, int(s * 0.008))

    def P(x, y):
        return ox + x * s, oy + y * s

    def poly(pts, col, outline=None):
        d.polygon([P(x, y) for x, y in pts], fill=pal[col] + (255,), outline=pal[outline] + (255,) if outline else None,
                  width=lw if outline else 0)

    def shard(ang, length, w, ph, grow):
        """A jagged blade from the head outwards, swaying; returns its points."""
        th = math.radians(ang + 6 * math.sin(a + ph * 6.3))
        dx, dy, nx, ny = math.cos(th), math.sin(th), -math.sin(th), math.cos(th)
        L = length * (1 + 0.07 * math.sin(a * 2 + ph * 9)) * grow
        cx, cy, r0 = 0.5, 0.42, 0.14
        bx, by = cx + dx * r0, cy + dy * r0
        jag = 0.45 + 0.2 * ph
        return [(bx + nx * w, by + ny * w), (bx + dx * L * jag + nx * w * 0.2, by + dy * L * jag + ny * w * 0.2),
                (bx + dx * L * (jag - 0.08) + nx * w * 0.9, by + dy * L * (jag - 0.08) + ny * w * 0.9),
                (bx + dx * L, by + dy * L), (bx - nx * w, by - ny * w)]

    # the crimson mass: a huge ragged mane round the head and the shards flying out of it, outlined black with a violet rim
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    mane = []
    for k in range(40):
        th = 2 * math.pi * k / 40
        r = (1.0 + 0.15 * ((k * 7) % 5) / 4 if k % 2 else 0.72) + 0.03 * math.sin(a + k)
        mane.append((0.5 + 0.46 * r * math.cos(th), 0.4 + 0.34 * r * math.sin(th) * (0.8 if math.sin(th) > 0 else 1.0)))
    crimson = [shard(ang, L, w, ph, 1.0) for ang, L, w, ph, dark in SHARDS if not dark] + [mane]
    for pts in crimson:
        poly(pts, "slime", "edge")
        md.polygon([P(x, y) for x, y in pts], fill=255)
    # glitter in the slime, twinkling
    sparkle = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sparkle)
    for gx, gy, gp in GLITTER:
        on = 0.5 + 0.5 * math.sin(a * 2 + gp * 40)
        if on > 0.55:
            x, y = P(gx, gy)
            r = s * 0.0035 * (0.6 + on)
            sd.ellipse((x - r, y - r, x + r, y + r), fill=pal["glitter"] + (255,))
    im.paste(sparkle, (0, 0), Image.composite(sparkle, Image.new("RGBA", im.size), mask).getchannel("A"))
    # the dark shards in front, rimmed violet
    for ang, L, w, ph, dark in SHARDS:
        if dark:
            poly(shard(ang, L * 0.9, w * 0.8, ph, 1.0), "ink", "edge")

    # the rest is small under all that hair: a thin black body, the head low in the mane
    k, (hx, hy) = 0.62, P(0.5, 0.66)
    s, ox, oy = s * k, hx - 0.5 * s * k, hy - 0.46 * s * k
    lw = max(1, int(s * 0.012))
    poly([(0.45, 0.6), (0.55, 0.6), (0.6, 0.8), (0.7, 0.86), (0.72, 1.0), (0.28, 1.0), (0.3, 0.86), (0.4, 0.8)], "ink", "edge")
    poly([(0.6, 0.86), (0.68, 0.9), (0.66, 0.98), (0.6, 0.95)], "face", "ink")
    poly([(0.3, 0.36), (0.5, 0.3), (0.7, 0.35), (0.71, 0.6), (0.6, 0.66), (0.5, 0.64), (0.4, 0.66), (0.29, 0.6)], "ink", "edge")
    # the face: two lime plates either side of a black wedge
    poly([(0.31, 0.37), (0.465, 0.335), (0.495, 0.48), (0.46, 0.56), (0.33, 0.56)], "face", "ink")
    poly([(0.525, 0.48), (0.555, 0.335), (0.69, 0.365), (0.68, 0.56), (0.55, 0.56)], "face", "ink")
    # the eyes: big and round, a black rim, a lime ring, the blue iris and a white pupil looking around, black ticks around them
    # like lashes; a blink now and then
    for ex, ey, r, ph in EYES:
        for k in range(5):
            th = math.radians(-150 + k * 60 + (40 if k > 2 else 0) + ph * 20)
            x0, y0 = ex + math.cos(th) * r * 0.9, ey + math.sin(th) * r * 0.9
            x1, y1 = ex + math.cos(th) * r * 1.45, ey + math.sin(th) * r * 1.45
            nx, ny = -math.sin(th) * r * 0.16, math.cos(th) * r * 0.16
            poly([(x0 + nx, y0 + ny), (x1, y1), (x0 - nx, y0 - ny)], "ink")
        lx, ly = 0.1 * r * math.sin(a + ph * 9), 0.07 * r * math.sin(a * 2 + ph * 5)
        for rr, col, k in ((1.0, "ink", 0), (0.8, "face", 0.2), (0.68, "ink", 0.4), (0.58, "iris", 0.6), (0.27, "white", 1.0)):
            x, y = P(ex + lx * k, ey + ly * k)
            d.ellipse((x - rr * r * s, y - rr * r * s, x + rr * r * s, y + rr * r * s), fill=pal[col] + (255,))
        b = (t + ph) % 1
        shut = max(0.0, 1 - abs(b - 0.5) / 0.05)   # the lid comes down and goes back up
        if shut:
            poly([(ex - r, ey - r), (ex + r, ey - r), (ex + r, ey - r + 2 * r * shut), (ex - r, ey - r + 2 * r * shut)], "face")
            d.line([P(ex - r, ey - r + 2 * r * shut), P(ex + r, ey - r + 2 * r * shut)], fill=pal["ink"] + (255,), width=lw)
    # the mouth: a thin white zigzag on the black under the plates, wiggling
    zig = [(0.44 + 0.12 * k / 6, 0.6 + (0.014 if k % 2 else 0) * (1 + 0.4 * math.sin(a * 2 + k))) for k in range(7)]
    d.line([P(x, y) for x, y in zig], fill=pal["white"] + (255,), width=max(1, int(s * 0.007)), joint="curve")
    # the bangs: crimson shards falling over the top of the head
    bangs = ((0.2, 0.26, 0.5, 0.1), (0.33, 0.36, 0.4, 0.5), (0.47, 0.5, 0.36, 0.8), (0.6, 0.6, 0.38, 0.3), (0.76, 0.75, 0.5, 0.6))
    poly([(0.12, 0.3), (0.5, 0.1), (0.88, 0.3), (0.8, 0.34), (0.2, 0.34)], "slime")
    for bx, tx, ty, ph in bangs:
        sw = 0.008 * math.sin(a + ph * 6)
        poly([(bx - 0.09, 0.3), (bx + 0.09, 0.3), (tx + sw, ty + abs(sw))], "slime")
    return im


def braille(t):
    W, H = COLS * 2, ROWS * 4
    lum = np.asarray(draw(t, W * SS, H * SS, LEVEL, 1.45).convert("L")).astype(float) / 255
    lum = lum.reshape(H, SS, W, SS).mean((1, 3))
    yy, xx = np.mgrid[0:H, 0:W]
    dots = lum > BAYER[yy % 4, xx % 4]
    lines = []
    for r in range(ROWS):
        line = ""
        for c in range(COLS):
            code = 0
            for (dx, dy), bit in BITS.items():
                if dots[r * 4 + dy, c * 2 + dx]:
                    code |= bit
            line += chr(0x2800 + code)
        lines.append(line.rstrip("⠀") or "⠀")
    return "\n".join(lines)


def sprite(out, frames=16, size=260):
    """Capri in her colours as RGBA frames (dancer.py shows them as they are with style "color", as a hologram otherwise)."""
    os.makedirs(out, exist_ok=True)
    for old in os.listdir(out):
        if old.startswith("dancer-") and old.endswith(".png"):
            os.remove(os.path.join(out, old))
    for n in range(frames):
        draw(n / frames, size * 2, size * 2, COLOUR).resize((size, size), Image.LANCZOS).save(os.path.join(out, f"dancer-{n}.png"))
    print(f"{frames} sprite frames of {size}x{size} in {out}")


def main():
    if SPRITE:
        return sprite(SPRITE)
    for old in os.listdir(HERE):
        if old.startswith("capri-") and old.endswith(".txt"):
            os.remove(os.path.join(HERE, old))
    for n in range(FRAMES):
        with open(os.path.join(HERE, f"capri-{n}.txt"), "w", encoding="utf-8") as fh:
            fh.write(braille(n / FRAMES))
    print(f"{FRAMES} frames of {COLS}x{ROWS} braille cells in {HERE}")


if __name__ == "__main__":
    main()
