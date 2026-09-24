#!/usr/bin/env python3
"""Frames of the ICE mascot for the lock screen (gits-lock-mascot, the Neuromancer theme): braille art, ice-0.txt ... next to this file.

Intrusion Countermeasures Electronics as Gibson drew them: a turning wireframe icosahedron with an octahedron turning the other way
inside it, and data packets circling it. Edges in front are solid, the ones behind dotted.
  ice.py [COLUMNS [ROWS [FRAMES]]]   default 40 x 20, 24 frames (3 s a turn at 8 frames a second).  Needs numpy.
  ice.py --still FILE [COLUMNS ROWS]   one frame as braille text (the Neuromancer art set's banner.txt / dashboard.txt)
  ice.py --sprite DIR                  dancer-0.png ... RGBA frames for the radio popup (gits-widgets/dancer.py); needs Pillow too."""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODE, TARGET = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] in ("--still", "--sprite") else ("", "")
if MODE:
    sys.argv = sys.argv[:1] + sys.argv[3:]
COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 40
ROWS = int(sys.argv[2]) if len(sys.argv) > 2 else 20
FRAMES = int(sys.argv[3]) if len(sys.argv) > 3 else 24
BITS = {(0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (0, 3): 0x40, (1, 3): 0x80}

PHI = (1 + 5 ** 0.5) / 2
ICO_V = np.array([(-1, PHI, 0), (1, PHI, 0), (-1, -PHI, 0), (1, -PHI, 0), (0, -1, PHI), (0, 1, PHI), (0, -1, -PHI), (0, 1, -PHI),
                  (PHI, 0, -1), (PHI, 0, 1), (-PHI, 0, -1), (-PHI, 0, 1)], float) / math.sqrt(1 + PHI ** 2)
ICO_E = sorted({tuple(sorted((i, j))) for i in range(12) for j in range(12)
                if i != j and abs(np.linalg.norm(ICO_V[i] - ICO_V[j]) - 1.0515) < 0.05})
OCT_V = np.array([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)], float) * 0.5
OCT_E = [(i, j) for i in range(6) for j in range(i + 1, 6) if i // 2 != j // 2]


def rot(ax, ay):
    ca, sa, cb, sb = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay)
    rx = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]])
    ry = np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]])
    return ry @ rx


def draw(dots, verts, edges, W, H, scale):
    for i, j in edges:
        a, b = verts[i], verts[j]
        n = int(max(abs(a[0] - b[0]), abs(a[1] - b[1])) * scale * 1.5) + 2
        for k in range(n + 1):
            t = k / n
            x, y, z = a + (b - a) * t
            px, py = int(round(W / 2 + x * scale)), int(round(H / 2 - y * scale))
            if 0 <= px < W and 0 <= py < H and (z > -0.05 or (px + py) % 2 == 0):   # behind: every other dot
                dots[py, px] = True


def frame(f):
    W, H = COLS * 2, ROWS * 4
    dots = np.zeros((H, W), bool)
    scale = min(W, H) * 0.42
    t = f / FRAMES * 2 * math.pi
    draw(dots, ICO_V @ rot(0.45, t).T, ICO_E, W, H, scale)
    draw(dots, OCT_V @ rot(-t * 2, -t).T, OCT_E, W, H, scale)
    for k in range(6):                                     # data packets on a tilted orbit
        a = t * 2 + k * math.pi / 3
        x, y, z = 1.35 * math.cos(a), 0.35 * math.sin(a), 1.35 * math.sin(a)
        if z > -0.3 or k % 2 == 0:
            px, py = int(W / 2 + x * scale * 0.85), int(H / 2 - y * scale * 0.85)
            dots[max(py - 1, 0):py + 1, max(px - 1, 0):px + 1] = True
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


def sprite(out, frames=16, size=220):
    """The ICE as RGBA frames: front edges bright, back edges dim (dancer.py tints them)."""
    from PIL import Image, ImageDraw
    os.makedirs(out, exist_ok=True)
    for old in os.listdir(out):
        if old.startswith("dancer-") and old.endswith(".png"):
            os.remove(os.path.join(out, old))
    s2 = size * 2
    for n in range(frames):
        t = n / frames * 2 * math.pi
        im = Image.new("RGBA", (s2, s2), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        sc = s2 * 0.36
        for verts, edges, width in ((ICO_V @ rot(0.45, t).T, ICO_E, 5), (OCT_V @ rot(-t * 2, -t).T, OCT_E, 4)):
            for i, j in sorted(edges, key=lambda e: verts[e[0]][2] + verts[e[1]][2]):
                a, b = verts[i], verts[j]
                v = 255 if (a[2] + b[2]) > -0.1 else 110
                d.line((s2 / 2 + a[0] * sc, s2 / 2 - a[1] * sc, s2 / 2 + b[0] * sc, s2 / 2 - b[1] * sc), fill=(v, v, v, v), width=width)
        for k in range(6):
            ang = t * 2 + k * math.pi / 3
            x, y = 1.35 * math.cos(ang) * sc * 0.85, 0.35 * math.sin(ang) * sc * 0.85
            d.ellipse((s2 / 2 + x - 7, s2 / 2 - y - 7, s2 / 2 + x + 7, s2 / 2 - y + 7), fill=(255, 255, 255, 255))
        im.resize((size, size), Image.LANCZOS).save(os.path.join(out, f"dancer-{n}.png"))
    print(f"{frames} sprite frames of {size}x{size} in {out}")


def main():
    if MODE == "--still":
        os.makedirs(os.path.dirname(os.path.abspath(TARGET)), exist_ok=True)
        with open(TARGET, "w", encoding="utf-8") as fh:
            fh.write(frame(2) + "\n")
        return
    if MODE == "--sprite":
        return sprite(TARGET)
    for old in os.listdir(HERE):
        if old.startswith("ice-") and old.endswith(".txt"):
            os.remove(os.path.join(HERE, old))
    for n in range(FRAMES):
        with open(os.path.join(HERE, f"ice-{n}.txt"), "w", encoding="utf-8") as fh:
            fh.write(frame(n))
    print(f"{FRAMES} frames of {COLS}x{ROWS} braille cells in {HERE}")


if __name__ == "__main__":
    main()
