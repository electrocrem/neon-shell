#!/usr/bin/env python3
"""Original artwork of the Snow Crash, Akira, Blade Runner 2049, Evangelion and Marathon themes (neon-shell), drawn from code:
nothing here is copied from the books, films, shows or the game, only their colours and a few well-known motifs.

  tools/make-theme-art.py [OUT_DIR [THEME ...]]      default: assets/, every theme
    NAME_WALL.jpg       2560x1440 wallpaper (the name the theme file asks for: snowcrash_street.jpg, akira_neotokyo.jpg ...)
    NAME_lock_bg.jpg    1920x1200 lock-screen background: darker, the left third (clock, prompt) kept quiet
    NAME_banner.png     520x650 the terminal banner / fastfetch picture of the art set
    NAME.txt            braille text of the banner (the art set's banner.txt / dashboard.txt, 38 x 19)

Needs Pillow and numpy. Colours are the roles of home/.config/gits/themes/NAME.theme.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "assets")
ONLY = sys.argv[2:]


def font(names, size):
    for n in names:
        for d in ("/usr/share/fonts/TTF", "/usr/share/fonts/noto-cjk", "/usr/share/fonts/OTF", "/usr/share/fonts/noto"):
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


MONO = ["JetBrainsMonoNerdFont-Bold.ttf", "JetBrainsMono-Bold.ttf", "DejaVuSansMono-Bold.ttf"]
SANS = ["JetBrainsMonoNerdFont-ExtraBold.ttf", "DejaVuSans-Bold.ttf", "JetBrainsMono-Bold.ttf"]
CJK = ["NotoSansCJK-Bold.ttc", "NotoSansCJK-Regular.ttc", "NotoSansCJKjp-Bold.otf"]


def hx(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(w, h, stops):
    """Vertical gradient through [(t, colour), ...]."""
    t = np.linspace(0, 1, h)
    ts = [s[0] for s in stops]
    cols = np.array([s[1] for s in stops], float)
    ch = [np.interp(t, ts, cols[:, i]) for i in range(3)]
    a = np.dstack([np.broadcast_to(c[:, None], (h, w)) for c in ch]).astype("uint8")
    return Image.fromarray(a).convert("RGBA")


def glow_layer(size, draw_fn, blur):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    g = layer.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.alpha_composite(g)
    out.alpha_composite(g)
    out.alpha_composite(layer)
    return out


def text_glow(img, xy, text, fnt, fill, blur=6, anchor="ms"):
    img.alpha_composite(glow_layer(img.size, lambda dr: dr.text(xy, text, font=fnt, fill=fill, anchor=anchor), blur))


def radial(w, h, cx, cy, r, col, power=2.0, alpha=255):
    """A soft round light: alpha falls from the centre to r."""
    y, x = np.ogrid[:h, :w]
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
    a = (np.clip(1 - d, 0, 1) ** power * alpha).astype("uint8")
    lay = np.zeros((h, w, 4), "uint8")
    lay[..., :3] = col
    lay[..., 3] = a
    return Image.fromarray(lay)


def skyline(img, base, rng, col, lights, density=0.08, hmin=60, hmax=420, wmin=50, wmax=200):
    d = ImageDraw.Draw(img)
    w = img.size[0]
    d.rectangle((0, base, w, img.size[1]), fill=col + (255,))   # the ground: no sky shows through between the towers
    x, towers = -20, []
    while x < w:
        tw, th = rng.randint(wmin, wmax), rng.randint(hmin, hmax)
        d.rectangle((x, base - th, x + tw, img.size[1]), fill=col + (255,))
        if rng.random() < 0.25:
            d.line((x + tw / 2, base - th, x + tw / 2, base - th - rng.randint(20, 110)), fill=col + (255,), width=4)
        for wy in range(int(base - th + 12), base - 6, 13):
            for wx in range(x + 7, x + tw - 7, 11):
                if rng.random() < density:
                    d.rectangle((wx, wy, wx + 4, wy + 6), fill=rng.choice(lights) + (rng.randint(80, 210),))
        towers.append((x, tw, th))
        x += tw + rng.randint(-8, 14)
    return towers


def finish(img, rng_np, scan=0.92, grain=4):
    a = np.asarray(img.convert("RGB")).astype(float)
    a[::3] *= scan
    return Image.fromarray(np.clip(a + rng_np.normal(0, grain, a.shape[:2])[..., None], 0, 255).astype("uint8"))


def quiet_left(img, lo=0.12):
    """The lock screen: the clock, the prompt and the password field sit on the left, so the picture fades out there."""
    a = np.asarray(img.convert("RGB")).astype(float)
    w = a.shape[1]
    a *= np.clip((np.arange(w) / w - 0.16) / 0.24, lo, 1.0)[None, :, None]
    return Image.fromarray(a.clip(0, 255).astype("uint8"))


# ------------------------------------------------------------------------------------------------------------- Snow Crash
SC = dict(bg=hx("#0B0906"), orange=hx("#FF8A1F"), orange_b=hx("#FFB866"), pink=hx("#FF3FA0"), yellow=hx("#FFD23F"),
          fg=hx("#F2E4CC"), blue=hx("#4D8CFF"))


def snowcrash(w, h, lock=False):
    """The Street: a boulevard of light running to the horizon, avatars' billboards on both sides, the Black Sun above it."""
    rng, nrng = random.Random(1992), np.random.default_rng(1992)
    hor = int(h * 0.52)
    img = gradient(w, h, [(0, (4, 3, 6)), (0.45, (22, 10, 14)), (0.52, (60, 22, 18)), (0.53, (8, 6, 5)), (1, (3, 2, 2))])
    sx = w * (0.70 if lock else 0.5)
    # the Black Sun: a black disc with an ember corona
    sun_y, sun_r = hor - h * 0.17, h * 0.13
    img.alpha_composite(radial(w, h, sx, sun_y, sun_r * 2.6, SC["orange"], 2.4, 150))
    d = ImageDraw.Draw(img)
    d.ellipse((sx - sun_r, sun_y - sun_r, sx + sun_r, sun_y + sun_r), fill=(0, 0, 0, 255))
    img.alpha_composite(glow_layer(img.size, lambda dr: dr.ellipse((sx - sun_r, sun_y - sun_r, sx + sun_r, sun_y + sun_r),
                                                                  outline=SC["orange_b"] + (230,), width=4), 10))
    # the Street: lines to the vanishing point, cross lines closer together near the horizon
    road = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(road)
    for i in range(-14, 15):
        col = SC["yellow"] if i in (-1, 1) else SC["orange"]
        a = int(200 * (1 - abs(i) / 16) * (0.5 if lock else 1))
        rd.line((sx + i * 6, hor, sx + i * 210, h), fill=col + (a,), width=2 if abs(i) > 1 else 3)
    for k in range(1, 22):
        t = (k / 21) ** 2.3
        yy = hor + (h - hor) * t
        rd.line((0, yy, w, yy), fill=SC["orange"] + (int((30 + 120 * t) * (0.5 if lock else 1)),), width=1 if t < 0.4 else 2)
    img.alpha_composite(road.filter(ImageFilter.GaussianBlur(5)))
    img.alpha_composite(road)
    # billboards of the Street: lit panels on poles, smaller towards the horizon
    signs = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(signs)
    cj = font(CJK, 40)
    words = ["ストリート", "黒い太陽", "ハッカー", "ピザ", "メタバース", "アバター", "ラフト", "スノウ"]
    for k in range(14):
        t = 0.06 + 0.9 * (k / 13) ** 1.6
        side = -1 if k % 2 else 1
        yy = hor + (h - hor) * t
        xx = sx + side * (60 + 1400 * t)
        s = 18 + 220 * t
        col = rng.choice((SC["pink"], SC["orange"], SC["yellow"], SC["blue"]))
        sd.line((xx, yy, xx, yy - s * 1.2), fill=(10, 8, 6, 255), width=max(2, int(s / 20)))
        box = (xx - s, yy - s * 2.1, xx + s, yy - s * 1.2)
        sd.rectangle(box, fill=col + (60 if lock else 90,), outline=col + (230,), width=max(1, int(s / 40)))
        if s > 90 and not lock:
            f = font(CJK, int(s / 3.6))
            sd.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), rng.choice(words), font=f, fill=SC["fg"] + (230,), anchor="mm")
    img.alpha_composite(signs.filter(ImageFilter.GaussianBlur(9)))
    img.alpha_composite(signs)
    if lock:
        text_glow(img, (sx, sun_y - sun_r - 70), "THE BLACK SUN", font(MONO, 54), SC["orange"] + (120,), 12, "mm")
        return finish(quiet_left(img), nrng)
    text_glow(img, (w / 2, int(h * 0.075)), "THE DELIVERATOR BELONGS TO AN ELITE ORDER, A HALLOWED SUBCATEGORY.", font(MONO, 34),
              SC["fg"] + (235,), 8)
    text_glow(img, (w / 2, h - 56), "SNOW CRASH  //  THE STREET", font(MONO, 26), SC["orange_b"] + (230,), 6)
    return finish(img, nrng)


# ------------------------------------------------------------------------------------------------------------------ Akira
AK = dict(red=hx("#E5242B"), red_b=hx("#FF5F55"), white=(255, 250, 244), blue=hx("#3FA4F0"), fg=hx("#F2EEE8"), orange=hx("#FF6A1A"))


def akira(w, h, lock=False):
    """Neo-Tokyo at night: a white blast dome rising over the skyline, light rays, a red tail-light streak on the highway."""
    rng, nrng = random.Random(1988), np.random.default_rng(1988)
    base = int(h * 0.66)
    img = gradient(w, h, [(0, (5, 6, 14)), (0.55, (20, 22, 40)), (0.66, (40, 30, 44)), (1, (6, 5, 8))])
    cx = w * (0.68 if lock else 0.5)
    r = h * (0.30 if lock else 0.36)
    # the dome: a white-hot half sphere with a red rim and its glow
    img.alpha_composite(radial(w, h, cx, base, r * 2.2, AK["red"], 1.8, 130))
    img.alpha_composite(radial(w, h, cx, base, r * 1.35, AK["white"], 1.4, 170 if lock else 220))
    rays = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rdr = ImageDraw.Draw(rays)
    for k in range(28):
        ang = math.pi + math.pi * (k + rng.random()) / 28
        L = r * rng.uniform(1.4, 2.6)
        rdr.line((cx, base, cx + math.cos(ang) * L, base + math.sin(ang) * L), fill=AK["white"] + (rng.randint(20, 60),),
                 width=rng.randint(3, 10))
    img.alpha_composite(rays.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)
    d.pieslice((cx - r, base - r, cx + r, base + r), 180, 360, fill=AK["white"] + (255,))
    img.alpha_composite(glow_layer(img.size, lambda dr: dr.arc((cx - r, base - r, cx + r, base + r), 180, 360,
                                                              fill=AK["red_b"] + (255,), width=10), 18))
    # the city in front of the dome
    skyline(img, base, rng, (8, 8, 12), [AK["blue"], AK["fg"], AK["red_b"]], 0.07, 30, 210 if not lock else 170, 40, 150)
    # the highway: a dark band with a red streak (Kaneda's bike) bending through it
    hy = int(h * 0.80)
    d = ImageDraw.Draw(img)
    d.rectangle((0, hy, w, h), fill=(6, 5, 8, 255))
    d.line((0, hy, w, hy), fill=AK["blue"] + (120,), width=2)
    pts = [(x, hy + 70 + 40 * math.sin(x / w * math.pi * 1.3)) for x in range(-50, int(w * (0.55 if lock else 0.82)), 12)]

    def streak(dr):
        for i in range(len(pts) - 1):
            t = i / len(pts)
            dr.line((pts[i], pts[i + 1]), fill=AK["red_b"] + (int(40 + 215 * t),), width=int(3 + 18 * t))
    img.alpha_composite(glow_layer(img.size, streak, 16))
    if lock:
        text_glow(img, (cx, base - r - 60), "ネオ東京", font(CJK, 64), AK["red"] + (150,), 12, "mm")
        return finish(quiet_left(img), nrng)
    text_glow(img, (w * 0.08, int(h * 0.12)), "アキラ", font(CJK, 150), AK["red"] + (255,), 14, "ls")
    text_glow(img, (w * 0.08, int(h * 0.12) + 60), "NEO-TOKYO  //  2019", font(MONO, 34), AK["fg"] + (230,), 6, "ls")
    text_glow(img, (w / 2, h - 50), "THE CAPSULES  //  KANEDA", font(MONO, 26), AK["red_b"] + (230,), 6)
    return finish(img, nrng)


# ------------------------------------------------------------------------------------------------------ Blade Runner 2049
BR = dict(orange=hx("#FF8C3A"), orange_b=hx("#FFB874"), teal=hx("#2EC4C6"), pink=hx("#E066B8"), fg=hx("#F5DEC0"), dust=(150, 70, 30))


def bladerunner(w, h, lock=False):
    """Las Vegas in the dust: an orange haze with a sun behind it, a stepped pyramid, the city's teal rain in front."""
    rng, nrng = random.Random(2049), np.random.default_rng(2049)
    base = int(h * 0.72)
    img = gradient(w, h, [(0, (40, 16, 6)), (0.45, (150, 66, 22)), (0.72, (205, 110, 46)), (0.73, (34, 16, 8)), (1, (12, 6, 4))])
    px = w * (0.68 if lock else 0.62)
    img.alpha_composite(radial(w, h, px - w * 0.18, h * 0.30, h * 0.45, BR["orange_b"], 2.0, 170))
    # the pyramid: stepped, with lit bands
    d = ImageDraw.Draw(img)
    steps, pw, ph = 9, w * 0.30, h * 0.44
    for s in range(steps):
        t0 = s / steps
        y0, y1 = base - ph * t0, base - ph * (t0 + 1 / steps)
        hw = pw / 2 * (1 - t0 * 0.92)
        col = lerp((70, 34, 14), (110, 56, 24), t0)
        d.polygon([(px - hw, y0), (px + hw, y0), (px + hw * 0.93, y1), (px - hw * 0.93, y1)], fill=col + (255,))
        d.line((px - hw * 0.96, y1 + 3, px + hw * 0.96, y1 + 3), fill=BR["orange_b"] + (90,), width=2)
    # a second pyramid far out in the dust, paler
    qx, qw, qh = w * (0.30 if not lock else 0.40), w * 0.13, h * 0.20
    for st in range(6):
        t0 = st / 6
        y0, y1 = base - qh * t0, base - qh * (t0 + 1 / 6)
        hw = qw / 2 * (1 - t0 * 0.92)
        d.polygon([(qx - hw, y0), (qx + hw, y0), (qx + hw * 0.93, y1), (qx - hw * 0.93, y1)], fill=(150, 76, 34, 255))
    # the dust: horizontal haze bands
    haze = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(haze)
    for _ in range(40):
        y = rng.uniform(h * 0.3, base + 20)
        hd.rectangle((0, y, w, y + rng.uniform(6, 40)), fill=BR["orange"] + (rng.randint(10, 28),))
    img.alpha_composite(haze.filter(ImageFilter.GaussianBlur(20)))
    d = ImageDraw.Draw(img)
    d.rectangle((0, base, w, h), fill=(22, 11, 6, 255))
    # the city at the bottom left: teal neon and rain
    city = Image.new("RGBA", img.size, (0, 0, 0, 0))
    skyline(city, h, rng, (10, 12, 14), [BR["teal"], BR["pink"], BR["fg"]], 0.10, 80, int(h * 0.28), 40, 140)
    mask = np.zeros((h, w), "uint8")
    mask[:, : int(w * (0.30 if lock else 0.42))] = 255
    city.putalpha(Image.fromarray(np.minimum(np.asarray(city.getchannel("A")), mask)))
    img.alpha_composite(city)
    cj = font(CJK, 40)
    for k, word in enumerate(["ジョイ", "アタリ", "ソニー"]):
        x0 = w * (0.04 + 0.11 * k) + 30
        if lock and x0 > w * 0.28:
            continue
        col = (BR["teal"], BR["pink"], BR["teal"])[k]
        img.alpha_composite(glow_layer(img.size, lambda dr, word=word, col=col, x0=x0: [
            dr.text((x0, h * 0.74 + i * 46), ch, font=cj, fill=col + (255,), anchor="mt") for i, ch in enumerate(word)], 10))
    rain = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rn = ImageDraw.Draw(rain)
    for _ in range(1400):
        x, y = rng.uniform(0, w * 0.5), rng.uniform(0, h)
        rn.line((x, y, x - 8, y + 34), fill=BR["teal"] + (int(rng.uniform(30, 90) * (1 - x / (w * 0.5))),), width=1)
    img.alpha_composite(rain)
    if lock:
        text_glow(img, (px, base - ph - 70), "INTERLINKED", font(MONO, 50), BR["orange_b"] + (140,), 12, "mm")
        return finish(quiet_left(img), nrng)
    text_glow(img, (w * 0.62, int(h * 0.09)), "ALL THOSE MOMENTS WILL BE LOST IN TIME, LIKE TEARS IN RAIN.", font(MONO, 32),
              BR["fg"] + (235,), 8)
    text_glow(img, (w / 2, h - 50), "LAS VEGAS  //  2049  //  INTERLINKED", font(MONO, 26), BR["orange_b"] + (230,), 6)
    return finish(img, nrng)


# ------------------------------------------------------------------------------------------------------------- Evangelion
EV = dict(purple=hx("#9D5CF0"), purple_b=hx("#C49BFF"), green=hx("#8BF23A"), orange=hx("#FF9D1A"), red=hx("#FF4520"), fg=hx("#ECE6F5"))


def hexfield(img, cx, cy, R, cell, col, strength=1.0):
    """An AT field: a hexagonal tiling, brightest on a ring, fading out."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dx, dy = cell * 1.5, cell * math.sqrt(3)
    n = int(R / cell) + 2
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x = cx + i * dx
            y = cy + j * dy + (dy / 2 if i % 2 else 0)
            r = math.hypot(x - cx, y - cy) / R
            if r > 1:
                continue
            a = int(255 * strength * (0.15 + 0.85 * math.exp(-((r - 0.82) / 0.12) ** 2)) * (1 - r ** 4))
            pts = [(x + cell * 0.92 * math.cos(math.pi / 3 * k), y + cell * 0.92 * math.sin(math.pi / 3 * k)) for k in range(6)]
            d.polygon(pts, outline=col + (a,), width=2)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(6)))
    img.alpha_composite(lay)


def evangelion(w, h, lock=False):
    """Tokyo-3 at dusk: an AT field opening over the city, a cross of light on the horizon, a warning band."""
    rng, nrng = random.Random(1995), np.random.default_rng(1995)
    base = int(h * 0.70)
    img = gradient(w, h, [(0, (10, 6, 22)), (0.5, (40, 18, 62)), (0.70, (110, 40, 70)), (0.71, (10, 8, 14)), (1, (6, 4, 10))])
    # the cross of light
    cx = w * (0.80 if not lock else 0.84)

    def cross(dr):
        dr.rectangle((cx - 16, base - h * 0.62, cx + 16, base), fill=(255, 235, 245, 230))
        dr.rectangle((cx - h * 0.16, base - h * 0.48, cx + h * 0.16, base - h * 0.48 + 26), fill=(255, 235, 245, 230))
    img.alpha_composite(radial(w, h, cx, base - h * 0.3, h * 0.5, (255, 120, 170), 2.2, 110))
    img.alpha_composite(glow_layer(img.size, cross, 22))
    hexfield(img, w * (0.62 if lock else 0.42), h * 0.40, h * 0.36, 34, EV["orange"], 0.9 if not lock else 0.6)
    skyline(img, base, rng, (12, 9, 18), [EV["green"], EV["fg"], EV["purple_b"]], 0.09, 60, 300)
    d = ImageDraw.Draw(img)
    # a warning band across the bottom: diagonal stripes and a label
    by = h - (130 if not lock else 90)
    band = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    bd.rectangle((0, by, w, by + 54), fill=(12, 8, 6, 230))
    for x in range(-60, w + 60, 46):
        bd.polygon([(x, by + 54), (x + 22, by + 54), (x + 54, by), (x + 32, by)], fill=EV["orange"] + (200,))
    img.alpha_composite(band)
    lab = "EMERGENCY  緊急  EMERGENCY  緊急  EMERGENCY"
    tf = font(CJK, 34)
    tw = d.textlength(lab, font=tf)
    bx = (w - tw) / 2 if not lock else w * 0.55
    d.rectangle((bx - 20, by + 4, bx + tw + 20, by + 50), fill=(12, 8, 6, 255))
    d.text((bx, by + 27), lab, font=tf, fill=EV["orange"] + (255,), anchor="lm")
    if lock:
        text_glow(img, (w * 0.62, h * 0.40), "第3新東京市", font(CJK, 60), EV["green"] + (140,), 12, "mm")
        return finish(quiet_left(img), nrng)
    text_glow(img, (w * 0.06, h * 0.13), "新世紀", font(CJK, 110), EV["fg"] + (245,), 10, "ls")
    text_glow(img, (w * 0.06, h * 0.13 + 70), "GOD'S IN HIS HEAVEN. ALL'S RIGHT WITH THE WORLD.", font(MONO, 30), EV["green"] + (235,), 8, "ls")
    return finish(img, nrng)


# --------------------------------------------------------------------------------------------------------------- Marathon
MA = dict(lime=hx("#C8FF1A"), pink=hx("#FF3D8B"), blue=hx("#2F7BFF"), paper=hx("#EDEFE4"), black=hx("#0A0B09"), grey=(40, 43, 36))


def marathon(w, h, lock=False):
    """Flat print graphics: a lime slab, a target, a barcode, halftone dots and small technical labels on near-black.
    No glow, no blur: the look is ink on paper."""
    rng, nrng = random.Random(2025), np.random.default_rng(2025)
    img = Image.new("RGBA", (w, h), MA["black"] + (255,))
    d = ImageDraw.Draw(img)
    s = h / 1440
    ox = w * (0.40 if lock else 0.0)
    # a fine grid
    for x in range(0, w, int(80 * s)):
        d.line((x, 0, x, h), fill=MA["grey"] + (255,), width=1)
    for y in range(0, h, int(80 * s)):
        d.line((0, y, w, y), fill=MA["grey"] + (255,), width=1)
    k = 0.45 if lock else 1.0

    def c(col):
        return tuple(int(v * k + MA["black"][i] * (1 - k)) for i, v in enumerate(col)) + (255,)
    # the lime slab with a cut corner
    x0, y0, x1, y1 = ox + w * 0.36, h * 0.16, ox + w * 0.86, h * 0.70
    if lock:
        x0, x1 = ox + w * 0.10, ox + w * 0.50
    cut = 140 * s
    d.polygon([(x0, y0), (x1 - cut, y0), (x1, y0 + cut), (x1, y1), (x0, y1)], fill=c(MA["lime"]))
    # halftone dots fading across the slab
    for yy in range(int(y0 + 30 * s), int(y1), int(22 * s)):
        for xx in range(int(x0 + 30 * s), int(x1), int(22 * s)):
            r = 9 * s * max(0.0, (xx - x0) / (x1 - x0) - 0.35)
            if r > 0.6:
                d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=c(MA["black"]))
    # the target
    tx, ty, tr = (ox + w * 0.30, h * 0.62, 260 * s) if not lock else (ox + w * 0.42, h * 0.62, 200 * s)
    for i, col in enumerate((MA["paper"], MA["black"], MA["pink"], MA["black"], MA["paper"])):
        rr = tr * (1 - i * 0.19)
        d.ellipse((tx - rr, ty - rr, tx + rr, ty + rr), fill=c(col))
    d.line((tx - tr * 1.3, ty, tx + tr * 1.3, ty), fill=c(MA["paper"]), width=int(4 * s))
    d.line((tx, ty - tr * 1.3, tx, ty + tr * 1.3), fill=c(MA["paper"]), width=int(4 * s))
    # a barcode
    bx, by = (x1 - 520 * s, y1 + 60 * s)
    for i in range(70):
        bw = rng.choice((2, 3, 5, 8)) * s
        if rng.random() < 0.62:
            d.rectangle((bx, by, bx + bw, by + 110 * s), fill=c(MA["paper"]))
        bx += bw + 2 * s
    # an electric-blue bar and pink ticks
    d.rectangle((ox + w * 0.06, h * 0.83, ox + w * (0.30 if not lock else 0.18), h * 0.83 + 18 * s), fill=c(MA["blue"]))
    for i in range(12):
        d.rectangle((x0 + i * 34 * s, y0 - 40 * s, x0 + i * 34 * s + 16 * s, y0 - 22 * s), fill=c(MA["pink"]))
    big, small = font(SANS, int(150 * s)), font(MONO, int(26 * s))
    lab = MA["black"] + (255,)
    if not lock:
        d.text((x0 + 40 * s, y1 - 40 * s), "RUNNER", font=big, fill=lab, anchor="ls")
        d.text((x0 + 44 * s, y0 + 50 * s), "UESC MARATHON // TAU CETI IV // SHELL 07", font=small, fill=lab, anchor="lt")
        d.text((w * 0.06, h * 0.10), "タウ・セチ", font=font(CJK, int(90 * s)), fill=c(MA["paper"]), anchor="lt")
        d.text((w * 0.06, h * 0.10 + 120 * s), "EXTRACTION WINDOW OPEN", font=small, fill=c(MA["lime"]), anchor="lt")
        d.text((w * 0.06, h * 0.83 + 40 * s), "ZONE 04 / PERIMETER / NO SIGNAL", font=small, fill=c(MA["paper"]), anchor="lt")
    else:
        d.text((x0 + 30 * s, y1 - 30 * s), "SHELL", font=font(SANS, int(110 * s)), fill=c(MA["black"]), anchor="ls")
    return finish(quiet_left(img, 0.25) if lock else img, nrng, scan=0.97, grain=3)


# ------------------------------------------------------------------------------------------------------------- the sets
THEMES = {
    "snowcrash": (snowcrash, "snowcrash_street.jpg", (0.31, 0.104)),
    "akira": (akira, "akira_neotokyo.jpg", (0.31, 0.104)),
    "bladerunner": (bladerunner, "bladerunner_vegas.jpg", (0.43, 0.104)),
    "evangelion": (evangelion, "evangelion_tokyo3.jpg", (0.59, 0.07)),
    "marathon": (marathon, "marathon_tauceti.jpg", (0.30, 0.104)),
}
BITS = ((0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (0, 3, 0x40), (1, 3, 0x80))


def braille(img, cols=38, rows=19):
    """The picture as braille dots: light parts set, dithered (Floyd-Steinberg), empty cells as braille blank."""
    g = img.convert("L").resize((cols * 2, rows * 4), Image.LANCZOS)
    a = np.asarray(g).astype(float)
    lo, hi = np.percentile(a, (45, 99))   # these pictures are mostly night: the darker half stays empty, the lit shapes dither
    a = np.clip((a - lo) / max(1.0, hi - lo), 0, 1) ** 0.8 * 255
    dots = np.asarray(Image.fromarray(a.astype("uint8")).convert("1")).astype(bool)
    lines = []
    for r in range(rows):
        s = ""
        for c in range(cols):
            v = 0
            for dx, dy, bit in BITS:
                if dots[r * 4 + dy, c * 2 + dx]:
                    v |= bit
            s += chr(0x2800 + v)
        lines.append(s.rstrip("⠀"))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, (fn, wall_name, (fx, fy)) in THEMES.items():
        if ONLY and name not in ONLY:
            continue
        wall = fn(2560, 1440)
        wall.save(os.path.join(OUT, wall_name), quality=90)
        x0, y0 = int(2560 * fx), int(1440 * fy)   # 960 x 1200: clear of the captions at the top and the bottom
        banner = wall.crop((x0, y0, x0 + 960, y0 + 1200)).resize((520, 650), Image.LANCZOS)
        banner.save(os.path.join(OUT, name + "_banner.png"), optimize=True)
        with open(os.path.join(OUT, name + ".txt"), "w") as f:
            f.write(braille(banner))
        fn(1920, 1200, lock=True).save(os.path.join(OUT, name + "_lock_bg.jpg"), quality=90)
        print("wrote", wall_name, name + "_lock_bg.jpg", name + "_banner.png", name + ".txt")
