#!/usr/bin/env python3
"""Original artwork of the Lain theme (neon-shell), drawn from code: nothing here is copied from the show.

  tools/make-lain-art.py [OUT_DIR]      default: assets/
    lain_wires.jpg      2560x1440 wallpaper: telephone poles and their wires against a violet dusk, the red polka-dot shadows of the
                        show on the street, a lavender hologram of the dancing Lain (a frame of assets/lain-dance.gif) under the wires
    lain_lock_bg.jpg    1920x1200 lock-screen background: the same street at night, darker, with the Copland OS mark

Needs Pillow and numpy. Colours are the roles of home/.config/gits/themes/lain.theme.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageSequence

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "assets")

BG, SURFACE, FG = (11, 10, 16), (27, 22, 38), (232, 220, 203)
LAV, LAV_B, PINK, RED = (183, 156, 255), (214, 198, 255), (227, 161, 214), (200, 16, 46)


def font(names, size):
    for n in names:
        for d in ("/usr/share/fonts/TTF", "/usr/share/fonts/noto-cjk", "/usr/share/fonts/OTF", "/usr/share/fonts/noto"):
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


MONO = ["JetBrainsMonoNerdFont-Bold.ttf", "JetBrainsMono-Bold.ttf", "DejaVuSansMono-Bold.ttf"]
CJK = ["NotoSansCJK-Bold.ttc", "NotoSansCJK-Regular.ttc", "NotoSansCJKjp-Bold.otf"]


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def sky(w, h, top, mid, horizon, hy):
    """Vertical gradient: top -> mid at 55% of the horizon line -> horizon glow at hy."""
    y = np.arange(h)[:, None] / max(hy, 1)
    a = np.zeros((h, w, 3))
    for c in range(3):
        v = np.where(y < 0.55, top[c] + (mid[c] - top[c]) * (y / 0.55),
                     mid[c] + (horizon[c] - mid[c]) * np.clip((y - 0.55) / 0.45, 0, 1))
        a[..., c] = v
    return a


def poles_and_wires(d, w, h, ground, rnd, color, scale=1.0):
    """Telephone poles marching into the distance and the sagging wires between them."""
    poles = []
    x, height = -0.05 * w, 0.95 * h
    vanish = (0.72 * w, ground - 0.02 * h)
    for i in range(9):
        t = i / 8
        px = x + (vanish[0] - x) * (1 - (1 - t) ** 1.8)
        ph = height * (1 - t) ** 1.6 + 0.04 * h
        pw = max(2, 22 * scale * (1 - t) ** 1.5)
        base = ground + 0.08 * h * (1 - t)
        top = base - ph
        d.rectangle((px - pw / 2, top, px + pw / 2, base), fill=color)
        for k, arm in enumerate((0.0, 0.07, 0.14)):     # cross arms
            ay = top + ph * arm + 6
            aw = pw * (5.5 - k)
            d.rectangle((px - aw, ay, px + aw, ay + max(2, pw * 0.35)), fill=color)
        poles.append((px, top, pw, ph))
    for (x0, t0, w0, h0), (x1, t1, w1, h1) in zip(poles, poles[1:]):
        for k in range(6):
            arm = (0.0, 0.07, 0.14)[k % 3]
            side = -1 if k < 3 else 1
            a = (x0 + side * w0 * (5.5 - k % 3) * 0.8, t0 + h0 * arm + 6)
            b = (x1 + side * w1 * (5.5 - k % 3) * 0.8, t1 + h1 * arm + 6)
            sag = 0.05 * h * (1 - (x0 / w) * 0.6) * (0.8 + 0.4 * rnd.random())
            pts = [(a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s + sag * 4 * s * (1 - s)) for s in np.linspace(0, 1, 40)]
            d.line(pts, fill=color, width=max(1, round(2 * scale * (1 - x0 / w * 0.7))))
    # a few wires that cross the whole sky, like in the opening
    for k in range(5):
        y0, y1 = h * (0.08 + 0.07 * k), h * (0.02 + 0.09 * k + 0.1 * rnd.random())
        sag = h * (0.05 + 0.04 * rnd.random())
        pts = [(s * w, y0 + (y1 - y0) * s + sag * 4 * s * (1 - s)) for s in np.linspace(0, 1, 80)]
        d.line(pts, fill=color, width=max(2, round(3 * scale)))


def polka_shadow(img, poly, rnd, dot=9, gap=22, color=RED):
    """The show's shadows: flat black with red dots in them, in the shape of the polygon (a pole's shadow across the street)."""
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    layer = Image.new("RGBA", img.size, (6, 4, 8, 255))
    d = ImageDraw.Draw(layer)
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    for yy in range(int(min(ys)), int(max(ys)) + gap, gap):
        off = (gap // 2) if (yy // gap) % 2 else 0
        for xx in range(int(min(xs)) - gap + off, int(max(xs)) + gap, gap):
            r = dot * (0.75 + 0.25 * rnd.random())
            d.ellipse((xx - r / 2, yy - r / 2, xx + r / 2, yy + r / 2), fill=color + (255,))
    img.paste(layer, (0, 0), mask)


def pole_shadows(img, w, h, ground, rnd, **kw):
    """Long shadows of the near poles thrown across the street towards the viewer, and the dark mass of a building on the left."""
    polka_shadow(img, [(0, ground + 20), (w * 0.30, ground + 20), (w * 0.18, h), (0, h)], rnd, **kw)
    for x, width in ((w * 0.13, 70), (w * 0.26, 44), (w * 0.39, 28)):
        polka_shadow(img, [(x - width / 4, ground + 8), (x + width / 4, ground + 8), (x + width * 5, h), (x + width * 3, h)], rnd, **kw)


def hologram_lain(height, frame=3):
    """A frame of assets/lain-dance.gif as a lavender hologram: the white around her flood-filled away from the corners (as
    gits-widgets/dancer.py does), ink deep violet, light pale lavender, scan-lined, with a soft glow."""
    gif = Image.open(os.path.join(REPO, "assets", "lain-dance.gif"))
    fr = [f for f in ImageSequence.Iterator(gif)][frame % gif.n_frames]
    base = Image.new("RGBA", fr.size, (255, 255, 255, 255))
    base.alpha_composite(fr.convert("RGBA"))
    rgb = base.convert("RGB")
    flood = rgb.copy()
    for corner in ((0, 0), (flood.width - 1, 0), (0, flood.height - 1), (flood.width - 1, flood.height - 1)):
        if min(flood.getpixel(corner)) > 200:
            ImageDraw.floodfill(flood, corner, (255, 0, 255), thresh=18)
    mask = ~(np.asarray(flood) == (255, 0, 255)).all(axis=2)
    ys, xs = np.nonzero(mask)
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    lum = np.asarray(rgb.crop(box)).astype(float).mean(2) / 255
    m = mask[box[1]:box[3], box[0]:box[2]]
    t = np.clip(lum, 0, 1)[..., None] ** 0.8
    col = np.array((40.0, 22.0, 70.0)) * (1 - t) + np.array(LAV_B, float) * t
    scan = (np.arange(m.shape[0]) % 3 < 2)[:, None]
    alpha = m * np.where(scan, 235, 120)
    holo = Image.fromarray(np.dstack([col, alpha]).astype("uint8"), "RGBA")
    k = height / holo.height
    holo = holo.resize((max(1, round(holo.width * k)), height), Image.NEAREST)
    glow = Image.new("RGBA", holo.size, LAV + (0,))
    glow.putalpha(holo.getchannel("A").point(lambda v: v // 2))
    glow = glow.filter(ImageFilter.GaussianBlur(height / 30))
    out = Image.new("RGBA", holo.size, (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(holo)
    return out


def grain_and_scanlines(img, rnd, amount=10, lines=0.10):
    a = np.asarray(img).astype(float)
    noise = np.random.default_rng(rnd.randint(0, 1 << 30)).normal(0, amount, a.shape[:2])[..., None]
    a = a + noise
    a[::3] *= 1 - lines
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8"))


def text_glow(img, xy, text, fnt, fill, glow, blur=6, anchor="la"):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=fnt, fill=glow, anchor=anchor)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    ImageDraw.Draw(layer).text(xy, text, font=fnt, fill=fill, anchor=anchor)
    img.alpha_composite(layer)


def wires_wallpaper(w=2560, h=1440):
    rnd = random.Random(7)
    ground = int(h * 0.80)
    img = Image.fromarray(sky(w, h, (9, 8, 14), (58, 38, 86), (226, 150, 190), ground).astype("uint8")).convert("RGBA")
    # a low sun behind the haze
    sun = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sun).ellipse((w * 0.74 - 90, ground - 250, w * 0.74 + 90, ground - 70), fill=PINK + (200,))
    img.alpha_composite(sun.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(img)
    poles_and_wires(d, w, h, ground, rnd, (8, 6, 12, 255), scale=1.4)
    # the street, and the polka-dot shadows the poles throw on it
    d.rectangle((0, ground, w, h), fill=(14, 11, 20, 255))
    pole_shadows(img, w, h, ground, rnd, dot=10, gap=22)
    # Lain, a hologram standing under the wires
    lain = hologram_lain(int(h * 0.42))
    img.alpha_composite(lain, (int(w * 0.62), ground + 120 - lain.height))
    # captions in the middle of the sky, where the desktop widgets (left and right columns) do not cover them:
    # "present day, present time" down between the first poles, the title at the top centre
    cj = font(CJK, 50)
    for i, ch in enumerate("プレゼント・デイ"):
        text_glow(img, (int(w * 0.205), int(h * 0.14) + i * 62), ch, cj, FG + (235,), LAV + (160,), blur=8)
    for i, ch in enumerate("プレゼント・タイム"):
        text_glow(img, (int(w * 0.228), int(h * 0.19) + i * 62), ch, cj, LAV_B + (200,), PINK + (120,), blur=8)
    text_glow(img, (w / 2, 110), "serial experiments lain", font(MONO, 34), LAV_B + (230,), PINK + (150,), anchor="ms")
    text_glow(img, (w / 2, h - 60), "PRESENT DAY, PRESENT TIME  //  LAYER:01 WEIRD", font(MONO, 24), FG + (220,), LAV + (140,), anchor="ms")
    return grain_and_scanlines(img.convert("RGB"), rnd, amount=7, lines=0.12)


def lock_background(w=1920, h=1200):
    rnd = random.Random(11)
    ground = int(h * 0.84)
    img = Image.fromarray(sky(w, h, (5, 4, 8), (18, 13, 28), (58, 34, 70), ground).astype("uint8")).convert("RGBA")
    d = ImageDraw.Draw(img)
    poles_and_wires(d, w, h, ground, rnd, (3, 2, 6, 255), scale=1.0)
    d.rectangle((0, ground, w, h), fill=(8, 6, 12, 255))
    pole_shadows(img, w, h, ground, rnd, dot=7, gap=16, color=(120, 10, 30))
    # the Copland OS mark, faint, in the middle of the sky
    text_glow(img, (w / 2, h * 0.30), "COPLAND OS", font(MONO, 64), LAV + (70,), LAV + (60,), blur=14, anchor="mm")
    text_glow(img, (w / 2, h * 0.30 + 60), "ENTERPRISE", font(MONO, 22), LAV + (60,), LAV + (40,), blur=8, anchor="mm")
    return grain_and_scanlines(img.convert("RGB"), rnd, amount=5, lines=0.10)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    wires_wallpaper().save(os.path.join(OUT, "lain_wires.jpg"), quality=90)
    lock_background().save(os.path.join(OUT, "lain_lock_bg.jpg"), quality=90)
    print("wrote lain_wires.jpg, lain_lock_bg.jpg to", OUT)
