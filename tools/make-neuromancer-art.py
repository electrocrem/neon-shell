#!/usr/bin/env python3
"""Original artwork of the Neuromancer theme (neon-shell), drawn from code.

  tools/make-neuromancer-art.py [OUT_DIR]      default: assets/
    neuromancer_chiba.jpg      2560x1440 wallpaper: a dead-channel sky over the Chiba port skyline and its neon, cyberspace below
    neuromancer_lock_bg.jpg    1920x1200 lock-screen background: cyberspace at night, ICE towers, WINTERMUTE

Needs Pillow and numpy. Colours are the roles of home/.config/gits/themes/neuromancer.theme.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "assets")

BG, FG = (7, 9, 10), (214, 222, 226)
GREEN, GREEN_B, MAGENTA, AMBER, BLUE = (59, 255, 142), (157, 255, 198), (255, 46, 151), (245, 230, 99), (58, 160, 255)


def font(names, size):
    for n in names:
        for d in ("/usr/share/fonts/TTF", "/usr/share/fonts/noto-cjk", "/usr/share/fonts/OTF", "/usr/share/fonts/noto"):
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


MONO = ["JetBrainsMonoNerdFont-Bold.ttf", "JetBrainsMono-Bold.ttf", "DejaVuSansMono-Bold.ttf"]
CJK = ["NotoSansCJK-Bold.ttc", "NotoSansCJK-Regular.ttc"]


def glow_layer(size, draw_fn, blur):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    g = layer.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.alpha_composite(g)
    out.alpha_composite(g)
    out.alpha_composite(layer)
    return out


def dead_channel(w, h, top, rng):
    """The sky: television static, darker towards the top, with scan lines and a drifting brighter band."""
    y = np.linspace(0, 1, top)[:, None]
    base = 40 + 70 * y
    noise = rng.normal(0, 26, (top, w))
    band = 30 * np.exp(-((np.arange(top)[:, None] - top * 0.62) / (top * 0.05)) ** 2)
    v = np.clip(base + noise + band, 0, 255)
    v[::3] *= 0.78
    a = np.dstack([v * 0.93, v * 0.98, v]).astype("uint8")
    return Image.fromarray(a)


def cyberspace(img, top, h, w, rng, vanish_x, intensity=1.0):
    """A green perspective grid from `top` down, with glowing data blocks (ICE) standing on it."""
    d = ImageDraw.Draw(img)
    horizon = top
    for i in range(-40, 41):                                      # lines to the vanishing point
        x_far = vanish_x + i * 18
        x_near = vanish_x + i * 240
        a = int(110 * intensity * (1 - abs(i) / 44))
        d.line((x_far, horizon, x_near, h), fill=GREEN + (a,), width=1)
    for k in range(1, 26):                                        # cross lines, closer together near the horizon
        t = (k / 25) ** 2.2
        yy = horizon + (h - horizon) * t
        d.line((0, yy, w, yy), fill=GREEN + (int(40 + 120 * t * intensity),), width=1 if t < 0.4 else 2)
    # ICE: a few wireframe data towers standing on the grid far out, near the horizon, drawn as a separate glowing layer
    blocks = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(blocks)
    for _ in range(9):
        t = rng.uniform(0.04, 0.30)
        yy = horizon + (h - horizon) * t
        s = 30 + 180 * t
        xx = vanish_x + rng.choice((-1, 1)) * rng.uniform(0.2, 1.4) * (w * 0.5) * t * 2.2
        hh = s * rng.uniform(1.2, 3.0)
        col = rng.choice((GREEN, GREEN, BLUE, MAGENTA))
        a_line = int(210 * intensity)
        bd.rectangle((xx - s / 2, yy - hh, xx + s / 2, yy), outline=col + (a_line,), width=2)
        top = [(xx - s / 2, yy - hh), (xx + s / 2, yy - hh), (xx + s * 0.8, yy - hh - s * 0.3), (xx - s * 0.2, yy - hh - s * 0.3)]
        bd.line(top + [top[0]], fill=col + (a_line,), width=2)
        bd.line(((xx + s / 2, yy), (xx + s * 0.8, yy - s * 0.3), (xx + s * 0.8, yy - hh - s * 0.3)), fill=col + (a_line,), width=2)
        for k in range(1, int(hh // 14)):                              # the data inside: faint horizontal rungs
            bd.line((xx - s / 2 + 4, yy - k * 14, xx + s / 2 - 4, yy - k * 14), fill=col + (int(70 * intensity),), width=1)
    glow = blocks.filter(ImageFilter.GaussianBlur(7))
    img.alpha_composite(glow)
    img.alpha_composite(blocks)


def skyline(img, base, w, rng):
    """Chiba: towers against the static, lit windows, vertical neon signs."""
    d = ImageDraw.Draw(img)
    x = -20
    towers = []
    while x < w:
        tw = rng.randint(60, 220)
        th = rng.randint(80, 480)
        d.rectangle((x, base - th, x + tw, base + 4), fill=BG + (255,))
        if rng.random() < 0.3:                                      # antenna
            d.line((x + tw / 2, base - th, x + tw / 2, base - th - rng.randint(30, 120)), fill=BG + (255,), width=4)
        for wy in range(int(base - th + 14), base - 8, 14):          # windows
            for wx in range(x + 8, x + tw - 8, 12):
                if rng.random() < 0.10:
                    d.rectangle((wx, wy, wx + 5, wy + 6), fill=rng.choice((AMBER, GREEN, FG, MAGENTA)) + (rng.randint(90, 200),))
        towers.append((x, tw, th))
        x += tw + rng.randint(-10, 18)
    return towers


def neon_signs(img, base, towers, rng):
    cj = font(CJK, 46)
    picks = sorted(towers, key=lambda t: -t[2])[:7]
    words = ["千葉", "仁清", "チャツボ", "電脳", "忍者", "夜の街", "ジャック"]
    for (x, tw, th), word in zip(picks, words):
        col = rng.choice((MAGENTA, GREEN, BLUE, MAGENTA))
        sx, sy = x + tw / 2, base - th + 40

        def draw(dr, word=word, col=col, sx=sx, sy=sy):
            for i, ch in enumerate(word):
                dr.text((sx, sy + i * 52), ch, font=cj, fill=col + (255,), anchor="mt")
        img.alpha_composite(glow_layer(img.size, draw, 10))


def text_glow(img, xy, text, fnt, fill, glow, blur=6, anchor="ms"):
    img.alpha_composite(glow_layer(img.size, lambda dr: dr.text(xy, text, font=fnt, fill=fill, anchor=anchor), blur))


def chiba(w=2560, h=1440):
    rng, nrng = random.Random(1984), np.random.default_rng(1984)
    base = int(h * 0.58)
    img = dead_channel(w, h, base, nrng).convert("RGBA")
    img = img.crop((0, 0, w, h))
    full = Image.new("RGBA", (w, h), BG + (255,))
    full.paste(img, (0, 0))
    img = full
    towers = skyline(img, base, w, rng)
    neon_signs(img, base, towers, rng)
    cyberspace(img, base + 6, h, w, rng, vanish_x=w / 2)
    text_glow(img, (w / 2, int(h * 0.09)), "THE SKY ABOVE THE PORT WAS THE COLOR OF TELEVISION,", font(MONO, 38), FG + (240,), GREEN + (120,), blur=8)
    text_glow(img, (w / 2, int(h * 0.09) + 54), "TUNED TO A DEAD CHANNEL.", font(MONO, 38), FG + (240,), GREEN + (120,), blur=8)
    text_glow(img, (w / 2, h - 60), "NEUROMANCER  //  JACK IN", font(MONO, 26), GREEN_B + (230,), GREEN + (150,), blur=6)
    a = np.asarray(img.convert("RGB")).astype(float)
    a[::3] *= 0.9
    return Image.fromarray(np.clip(a + nrng.normal(0, 4, a.shape[:2])[..., None], 0, 255).astype("uint8"))


def lock_background(w=1920, h=1200):
    rng, nrng = random.Random(2035), np.random.default_rng(2035)
    img = Image.new("RGBA", (w, h), (4, 6, 6, 255))
    cyberspace(img, int(h * 0.60), h, w, rng, vanish_x=w * 0.62, intensity=0.38)
    text_glow(img, (w * 0.62, h * 0.40), "WINTERMUTE", font(MONO, 72), GREEN + (60,), GREEN + (50,), blur=14, anchor="mm")
    a = np.asarray(img.convert("RGB")).astype(float)
    # the clock, the prompt and the password field sit on the left: fade the grid out there
    a *= np.clip((np.arange(w) / w - 0.18) / 0.22, 0.12, 1.0)[None, :, None]
    a[::3] *= 0.9
    return Image.fromarray(np.clip(a + nrng.normal(0, 3, a.shape[:2])[..., None], 0, 255).astype("uint8"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    chiba().save(os.path.join(OUT, "neuromancer_chiba.jpg"), quality=90)
    lock_background().save(os.path.join(OUT, "neuromancer_lock_bg.jpg"), quality=90)
    print("wrote neuromancer_chiba.jpg, neuromancer_lock_bg.jpg to", OUT)
