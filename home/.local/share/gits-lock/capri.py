#!/usr/bin/env python3
"""Frames of the Capri mascot for the lock screen (gits-lock-mascot, the Edgerunners theme): braille art, capri-0.txt ... next to this file.

Capri, the rogue engram of Cyberpunk: Edgerunners 2, as flat graphics: a mane of jagged crimson shards full of glitter, black blades
rimmed violet, a spiky hood, a big lime face plate under a white zigzag fringe, two big round ringed blue eyes and a small grin of fangs. The shards sway,
the glitter twinkles, the eyes look about and blink, the grin opens and closes. Drawn from code after the general motifs only,
nothing is traced from the show.
In braille every colour is a dot density: the glitter, the fangs and the eye glints solid, the face dense, the irises medium, the
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
SHARDS = [(_R.uniform(-170, 10) if k % 3 else _R.uniform(10, 170), _R.uniform(0.28, 0.55), _R.uniform(0.035, 0.08), _R.random(), k % 4 == 0)
          for k in range(30)]
GLITTER = [(_R.random(), _R.random(), _R.random()) for _ in range(1800)]
EYES = ((0.41, 0.465, 0.078, 0.0), (0.59, 0.455, 0.064, 0.4))   # centre, radius, a phase for where it looks and when it blinks


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
        cx, cy, r0 = 0.5, 0.45, 0.08
        bx, by = cx + dx * r0, cy + dy * r0
        jag = 0.45 + 0.2 * ph
        return [(bx + nx * w, by + ny * w), (bx + dx * L * jag + nx * w * 0.2, by + dy * L * jag + ny * w * 0.2),
                (bx + dx * L * (jag - 0.08) + nx * w * 0.9, by + dy * L * (jag - 0.08) + ny * w * 0.9),
                (bx + dx * L, by + dy * L), (bx - nx * w, by - ny * w)]

    # the crimson mass: a cloak falling down to the bottom, and the shards of the mane, outlined black with a violet rim
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    cloak = [(0.5, 0.4), (0.78, 0.55), (0.96, 1.0), (0.04, 1.0), (0.22, 0.55)]
    crimson = [cloak] + [shard(ang, L, w, ph, 1.0) for ang, L, w, ph, dark in SHARDS if not dark]
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

    # the head: a spiky black hood with a green chevron over it
    hood = [(0.5, 0.22), (0.55, 0.28), (0.62, 0.2), (0.64, 0.31), (0.74, 0.34), (0.69, 0.42), (0.72, 0.62), (0.6, 0.6), (0.5, 0.68),
            (0.4, 0.6), (0.28, 0.62), (0.31, 0.42), (0.26, 0.34), (0.36, 0.31), (0.38, 0.2), (0.45, 0.28)]
    poly(hood, "ink", "edge")
    poly([(0.58, 0.15), (0.65, 0.2), (0.62, 0.28), (0.56, 0.26), (0.6, 0.21)], "face", "ink")
    # the face plate: a big lime block, slanting a little, with a notch at the bottom
    poly([(0.32, 0.35), (0.68, 0.345), (0.69, 0.58), (0.57, 0.59), (0.5, 0.555), (0.43, 0.59), (0.31, 0.58)], "face", "ink")
    # the fringe: a white zigzag band over the eyes, its teeth bobbing a little
    bob = 0.006 * math.sin(a * 2)
    fringe = [(0.33, 0.33), (0.67, 0.325), (0.66, 0.36)]
    for k in range(6, -1, -1):   # the zigzag along the bottom edge, right to left
        x = 0.34 + 0.32 * k / 6
        fringe.append((x - 0.02, 0.36 + (0.035 + bob if k % 2 else 0.0)))
    poly(fringe, "white", "ink")
    # the eyes: big and round, a black rim, a white ring, the blue iris and a white pupil looking around, a glint; a blink now and then
    for ex, ey, r, ph in EYES:
        lx, ly = 0.1 * r * math.sin(a + ph * 9), 0.07 * r * math.sin(a * 2 + ph * 5)
        for rr, col, k in ((1.0, "ink", 0), (0.78, "white", 0.3), (0.64, "ink", 0.5), (0.54, "iris", 0.6), (0.22, "white", 1.0)):
            x, y = P(ex + lx * k, ey + ly * k)
            d.ellipse((x - rr * r * s, y - rr * r * s, x + rr * r * s, y + rr * r * s), fill=pal[col] + (255,))
        x, y = P(ex + lx - r * 0.3, ey + ly - r * 0.3)   # the glint
        d.ellipse((x - 0.1 * r * s, y - 0.1 * r * s, x + 0.1 * r * s, y + 0.1 * r * s), fill=pal["white"] + (255,))
        b = (t + ph) % 1
        shut = max(0.0, 1 - abs(b - 0.5) / 0.05)   # the lid comes down and goes back up
        if shut:
            poly([(ex - r, ey - r), (ex + r, ey - r), (ex + r, ey - r + 2 * r * shut), (ex - r, ey - r + 2 * r * shut)], "face")
            d.line([P(ex - r, ey - r + 2 * r * shut), P(ex + r, ey - r + 2 * r * shut)], fill=pal["ink"] + (255,), width=lw)
    # the grin: a small white wedge of fangs under the plate, opening and closing
    o = 0.05 + 0.03 * (0.5 + 0.5 * math.sin(a * 2))
    poly([(0.45, 0.6), (0.57, 0.597), (0.54, 0.6 + o * 0.5), (0.515, 0.6 + o)], "white", "ink")
    for fx in (0.48, 0.52):   # the gaps between the fangs
        poly([(fx, 0.598), (fx + 0.01, 0.598), (fx + 0.005, 0.598 + o * 0.4)], "ink")
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
