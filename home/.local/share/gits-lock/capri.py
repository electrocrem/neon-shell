#!/usr/bin/env python3
"""Frames of the Capri mascot for the lock screen (gits-lock-mascot, the Edgerunners theme): braille art, capri-0.txt ... next to this file.

Capri, the rogue engram of Cyberpunk: Edgerunners 2, as flat graphics: a lime face plate with four ringed eyes, a white spike above it
and a mane of crimson slime splashing around. The eyes look about out of step with each other and blink in turn, the splashes wave
and throw drops. Drawn from code after the general motifs only, nothing is traced from the show.
In braille every colour is a dot density: the spike and the pupils solid, the face dense, the irises medium, the slime sparse, black
(the outlines, the eye rings) empty.
  capri.py [COLUMNS [ROWS [FRAMES]]]   default 48 x 26, 24 frames (3 s a loop at 8 frames a second).  Needs Pillow and numpy.
  capri.py --sprite DIR                 dancer-0.png ... dancer-15.png in DIR instead: the same drawing in colour for the radio popup
                                        (gits-widgets/dancer.py)."""
import math
import os
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
COLOUR = dict(slime=(232, 20, 72), slime_hi=(255, 92, 130), face=(64, 236, 96), ink=(8, 6, 14), iris=(36, 92, 230), pupil=(245, 248, 255),
              spike=(250, 250, 250))
LEVEL = dict(slime=(40,) * 3, slime_hi=(90,) * 3, face=(205,) * 3, ink=(0,) * 3, iris=(105,) * 3, pupil=(255,) * 3, spike=(255,) * 3)

# the four eyes: centre, half width, half height, tilt (degrees), a phase for where they look and when they blink
EYES = ((0.37, 0.47, 0.105, 0.065, -8, 0.0), (0.63, 0.46, 0.09, 0.06, 6, 0.35),
        (0.36, 0.70, 0.085, 0.045, 4, 0.6), (0.62, 0.72, 0.115, 0.075, -4, 0.15))


def draw(t, W, H, pal):
    """One frame at loop time t (0..1) as an RGBA image W x H, in the palette pal (COLOUR or LEVEL)."""
    a = t * 2 * math.pi
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = min(W, H) / 1.08
    ox, oy = (W - s) / 2, (H - s * 1.04) / 2 + s * 0.02

    def P(x, y):
        return ox + x * s, oy + y * s

    def blob(x, y, r, col):
        cx, cy = P(x, y)
        d.ellipse((cx - r * s, cy - r * s, cx + r * s, cy + r * s), fill=col + (255,))

    # the mane of slime behind it all: a ragged hood and splashes waving out of it, throwing drops
    hood = [(0.5, -0.02), (0.6, 0.08), (0.74, 0.2), (0.83, 0.38), (0.86, 0.62), (0.92, 0.98), (0.08, 0.98), (0.14, 0.62),
            (0.17, 0.38), (0.26, 0.2), (0.4, 0.08)]
    d.polygon([P(x + 0.012 * math.sin(a + i * 1.7), y + 0.01 * math.cos(a * 2 + i)) for i, (x, y) in enumerate(hood)],
              fill=pal["slime"] + (255,))
    splashes = ((0.2, 0.42, -1, 0.6, 0.0), (0.18, 0.78, -1, 0.15, 0.4), (0.8, 0.36, 1, 0.75, 0.2), (0.84, 0.8, 1, 0.3, 0.7))
    for bx, by, side, rise, ph in splashes:
        for k in range(18):
            u = k / 17
            wave = math.sin(a + ph * 6 + u * 4) * 0.04 * u
            x = bx + side * u * 0.26
            y = by - rise * u * 0.3 + wave + 0.05 * u * u
            blob(x, y, 0.045 * (1 - u) + 0.008, pal["slime"])
        f = (t + ph) % 1   # a drop thrown off the tip
        blob(bx + side * (0.27 + 0.12 * f), by - rise * 0.3 + 0.05 - 0.1 * f + 0.25 * f * f, 0.016 * (1 - f) + 0.005, pal["slime_hi"])
    for i in range(10):   # glints on the slime
        x, y = 0.5 + 0.34 * math.cos(i * 2.3 + 0.4) * (0.6 + 0.4 * (i % 3) / 2), 0.15 + 0.08 * i
        if abs(x - 0.5) > 0.22:
            blob(x + 0.01 * math.sin(a + i), y, 0.012, pal["slime_hi"])
    # the white spike over the plate, with a broken edge at its foot
    d.polygon([P(0.42, 0.31), P(0.5, 0.06), P(0.58, 0.31), P(0.55, 0.28), P(0.53, 0.32), P(0.49, 0.27), P(0.46, 0.31)],
              fill=pal["spike"] + (255,))
    # the face plate: a lime trapezoid with a ragged top, black outline, the dark body under it
    d.polygon([P(0.28, 1.04), P(0.32, 0.93), P(0.68, 0.93), P(0.72, 1.04)], fill=pal["ink"] + (255,))
    plate = [P(0.26, 0.33), P(0.36, 0.32), P(0.4, 0.3), P(0.45, 0.33), P(0.6, 0.32), P(0.63, 0.29), P(0.66, 0.33), P(0.74, 0.33),
             P(0.70, 0.94), P(0.30, 0.94)]
    d.polygon(plate, fill=pal["face"] + (255,), outline=pal["ink"] + (255,), width=max(1, int(s * 0.012)))
    # the eyes: an almond of ink, two rings, the iris and the pupil looking around; the lids close once a loop
    for cx, cy, rw, rh, tilt, ph in EYES:
        b = (t + ph) % 1
        lid = 1.0 - max(0.0, 1 - abs(b - 0.5) / 0.06)   # a quick blink around b = 0.5
        lid = max(lid, 0.08)
        look = (0.35 * math.sin(a + ph * 9), 0.25 * math.sin(a * 2 + ph * 5))
        rot = math.radians(tilt)

        def E(u, v):   # eye space (-1..1) to picture
            x, y = u * rw, v * rh
            return P(cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot))
        top = [E(-1 + 2 * k / 24, -math.sin(math.pi * k / 24) * lid) for k in range(25)]
        bottom = [E(1 - 2 * k / 24, math.sin(math.pi * k / 24) * lid) for k in range(25)]
        outline = [E(-1.25 + 2.5 * k / 24, -math.sin(math.pi * k / 24) * (lid + 0.35)) for k in range(25)] + \
                  [E(1.25 - 2.5 * k / 24, math.sin(math.pi * k / 24) * (lid + 0.35)) for k in range(25)]
        d.polygon(outline, fill=pal["ink"] + (255,))
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.polygon(top + bottom, fill=pal["face"] + (255,))
        ix, iy = E(look[0], look[1])
        for r, col in ((0.95, "ink"), (0.8, "face"), (0.66, "ink"), (0.52, "iris"), (0.24, "pupil")):
            rr = r * rh * s * 1.25
            ld.ellipse((ix - rr, iy - rr, ix + rr, iy + rr), fill=pal[col] + (255,))
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).polygon(top + bottom, fill=255)
        im.paste(layer, (0, 0), mask)
    return im


def braille(t):
    W, H = COLS * 2, ROWS * 4
    lum = np.asarray(draw(t, W * SS, H * SS, LEVEL).convert("L")).astype(float) / 255
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
