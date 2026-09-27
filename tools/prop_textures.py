"""Texture sets for the trunk props, built from Poly Haven scans (CC0).

    .venv/bin/python tools/prop_textures.py

Writes 512 px tiles (col / rough / nor) into assets-src/props_tex for the
hand-made props, and the full-size pegboard for the underside of the false
floor (2048 x 1024, one texel per 0.7 mm, holes on a one-inch grid). The
Blender build bakes contact shadows into the pegboard colour afterwards.
"""
import json
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'assets-src', 'polyhaven', 'tex')
OUT = os.path.join(ROOT, 'assets-src', 'props_tex')

# the pegboard face of the false floor (metres), and its hole grid
BOARD_W, BOARD_L = 1.42, 0.78
PITCH = 0.0254
HOLE_R = 0.0032


def load(name, kind, mode='RGB'):
    return Image.open(os.path.join(SRC, f'{name}_{kind}_1k.jpg')).convert(mode)


def save(img, name):
    img.save(os.path.join(OUT, name + '.png'))
    print('  ', name, img.size)


def tile_set(out, src, rotate=False, tint=(1, 1, 1), gain=1.0, rough_add=0.0):
    """512 px tile of a scanned wood: grain along the image's x axis (the
    props' length runs along u), colour tinted and scaled."""
    col, rough, nor = load(src, 'diff'), load(src, 'rough', 'L'), load(src, 'nor_gl')
    if rotate:
        col, rough, nor = (im.transpose(Image.Transpose.ROTATE_90) for im in (col, rough, nor))
        # a quarter turn swaps the normal map's tangent axes: x' = -y, y' = x
        n = np.asarray(nor).astype(np.float32) / 127.5 - 1
        n = np.stack([-n[..., 1], n[..., 0], n[..., 2]], -1)
        nor = Image.fromarray(((n + 1) * 127.5).clip(0, 255).astype(np.uint8))
    c = np.asarray(col).astype(np.float32) / 255
    c = (c * np.array(tint, np.float32) * gain).clip(0, 1)
    col = Image.fromarray((c * 255).astype(np.uint8))
    r = (np.asarray(rough).astype(np.float32) / 255 + rough_add).clip(0, 1)
    rough = Image.fromarray((r * 255).astype(np.uint8))
    size = (512, 512)
    save(col.resize(size, Image.LANCZOS), f'{out}_col')
    save(rough.resize(size, Image.LANCZOS), f'{out}_rough')
    save(nor.resize(size, Image.LANCZOS), f'{out}_nor')


def pegboard(w=2048, h=1024):
    """Tempered hardboard with 1/4" holes on a 1" grid. x runs across the
    board (viewer's right when it stands), y up the board from the hinge."""
    rng = np.random.default_rng(7)
    # fibre base: the fine-grained scan tiled at ~0.36 m, darkened to stained hardboard
    base = load('fine_grained_wood', 'diff').resize((512, 512), Image.LANCZOS)
    b = np.asarray(base).astype(np.float32) / 255
    reps_x, reps_y = int(np.ceil(w / 512)), int(np.ceil(h / 512))
    col = np.tile(b, (reps_y, reps_x, 1))[:h, :w]
    col = col * np.array([0.82, 0.74, 0.66], np.float32) * 0.95
    # broad mottling and a darker, handled band along the bottom edge
    blot = rng.random((h // 64 + 2, w // 64 + 2)).astype(np.float32)
    blot = np.asarray(Image.fromarray((blot * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    col *= (0.86 + 0.22 * blot)[..., None]
    ys = np.linspace(0, BOARD_L, h, dtype=np.float32)[:, None]
    xs = np.linspace(0, BOARD_W, w, dtype=np.float32)[None, :]
    col *= (0.85 + 0.15 * np.clip(ys / 0.12, 0, 1))[..., None]

    # holes: distance to the nearest grid centre (margins keep half a pitch clear)
    nx, ny = int((BOARD_W - PITCH) / PITCH) + 1, int((BOARD_L - PITCH) / PITCH) + 1
    x0 = (BOARD_W - (nx - 1) * PITCH) / 2
    y0 = (BOARD_L - (ny - 1) * PITCH) / 2
    gx = np.clip(np.round((xs - x0) / PITCH), 0, nx - 1) * PITCH + x0
    gy = np.clip(np.round((ys - y0) / PITCH), 0, ny - 1) * PITCH + y0
    d = np.sqrt((xs - gx) ** 2 + (ys - gy) ** 2)
    px = BOARD_W / w
    hole = np.clip((HOLE_R - d) / px + 0.5, 0, 1)             # anti-aliased disc
    rim = np.clip(1 - np.abs(d - HOLE_R - 0.0006) / 0.0009, 0, 1)  # the pressed chamfer around it
    col = col * (1 - hole[..., None]) + np.array([0.012, 0.009, 0.007], np.float32) * hole[..., None]
    col *= (1 - 0.18 * rim)[..., None]

    # height: flat face, a small chamfer into each hole, fibre noise
    fib = np.asarray(load('fine_grained_wood', 'rough', 'L').resize((512, 512), Image.LANCZOS)).astype(np.float32) / 255
    fib = np.tile(fib, (reps_y, reps_x))[:h, :w]
    height = -np.clip((HOLE_R + 0.0012 - d) / 0.0012, 0, 1) * 0.8 + fib * 0.06
    gyh, gxh = np.gradient(height)
    n = np.stack([-gxh * 6, -gyh * 6, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)

    # image rows run top-down; board y runs up from the hinge
    flip = lambda a: a[::-1]
    save(Image.fromarray((flip(col).clip(0, 1) * 255).astype(np.uint8)), 'pegboard_col')
    save(Image.fromarray((flip((n + 1) * 127.5)).clip(0, 255).astype(np.uint8)), 'pegboard_nor')
    # the hole centres, so the build can put hooks in real holes
    return x0, y0, nx, ny


def glyph(draw, cx, cy, h, rnd, width):
    """One invented rune on a shared baseline: a stem (mostly) with one or two
    marks hung on it. Not any real script."""
    top, bot = cy - h * 0.5, cy + h * 0.5
    mid = cy
    w = h * 0.5
    line = lambda *p: draw.line(list(p), fill=255, width=width, joint='curve')
    arc = lambda x, y, r, a0, a1: draw.arc([x - r, y - r, x + r, y + r], a0, a1, fill=255, width=width)
    if rnd.random() < 0.8:
        sx = cx + rnd.uniform(-0.15, 0.15) * w
        line((sx, top + h * rnd.choice((0.0, 0.2))), (sx, bot))
        marks = rnd.sample(['bar', 'hook', 'loop', 'slash', 'tick', 'dot', 'fork'], rnd.randint(1, 2))
        for m in marks:
            side = rnd.choice((-1, 1))
            if m == 'bar':
                y = rnd.choice((top + h * 0.1, mid))
                line((sx, y), (sx + side * w, y))
            elif m == 'hook':
                arc(sx + side * w * 0.45, bot - w * 0.45, w * 0.45, 0 if side > 0 else 180, 180 if side > 0 else 360)
            elif m == 'loop':
                arc(sx + side * w * 0.45, mid - h * 0.12, w * 0.42, 0, 360)
            elif m == 'slash':
                line((sx - w * 0.6, top + h * 0.15), (sx + w * 0.6, mid + h * 0.1))
            elif m == 'tick':
                line((sx, mid), (sx + side * w * 0.7, mid - h * 0.3))
            elif m == 'dot':
                x, y = sx + side * w * 0.7, top + h * 0.05
                draw.ellipse([x - width, y - width, x + width, y + width], fill=255)
            else:
                line((sx, top + h * 0.35), (sx - w * 0.6, top), )
                line((sx, top + h * 0.35), (sx + w * 0.6, top))
    else:
        # a stemless curl
        arc(cx, mid, w * 0.55, rnd.choice((0, 90, 180)), rnd.choice((270, 300, 330)) + 60)
        line((cx - w * 0.6, bot), (cx + w * 0.6, bot))


def ruby_blade(w=1024, h=256):
    """Ruby's knife: polished steel with frosted, etched lines. UVs are the
    blade's plan view: u = x / length, v spans the outline's y range (the
    Blender build maps them the same way, from tools/blender/blades.json)."""
    import random
    spec = json.load(open(os.path.join(ROOT, 'tools', 'blender', 'blades.json')))['ruby']
    L = spec['length']
    ys = [y for _, y in spec['spine'] + spec['edge']]
    y0, y1 = min(ys), max(ys)
    S = 4                                   # draw at 4x, then downsample
    to_px = lambda x, y: (x / L * w * S, (1 - (y - y0) / (y1 - y0)) * h * S)
    mask = Image.new('L', (w * S, h * S), 0)
    d = ImageDraw.Draw(mask)
    lw = 6
    # the bevel line: the scalloped edge's outline, 4 mm in, run up to the point
    edge = spec['edge']
    off = [(x, y + 0.0044) for x, y in edge if 0.012 <= x <= 0.182]
    d.line([to_px(*p) for p in off] + [to_px(L - 0.004, 0.0035)], fill=255, width=lw, joint='curve')
    # the line by the guard, bowed towards the point
    d.line([to_px(0.011 + 0.002 * math.sin(math.pi * t), -0.0138 + 0.0296 * t) for t in [i / 12 for i in range(13)]],
           fill=255, width=lw, joint='curve')
    # the script band: invented runes between the bevel line and the spine
    rnd = random.Random(1966)
    x, cy, gh = 0.022, 0.0068, 0.006
    while x < 0.126:
        cx, py = to_px(x, cy)
        glyph(d, cx, py, gh / (y1 - y0) * h * S, rnd, lw)
        x += gh * rnd.uniform(0.72, 0.95)
    mask = mask.resize((w, h), Image.LANCZOS)
    m = np.asarray(mask).astype(np.float32) / 255

    # brushed steel along the blade, the etch frosted, a touch darker and recessed
    rng = np.random.default_rng(3)
    streak = np.repeat(rng.normal(0, 1, (h, 1)), w, 1)
    streak = np.asarray(Image.fromarray(((streak * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255
    base = 0.8 + 0.035 * (streak - 0.5)
    col = base * (1 - 0.2 * m)
    rough = 0.13 + 0.05 * streak + 0.45 * m
    height = -np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    gy, gx = np.gradient(height)
    n = np.stack([-gx * 3, gy * 3, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    save(Image.fromarray((np.stack([col] * 3, -1).clip(0, 1) * 255).astype(np.uint8)), 'ruby_blade_col')
    save(Image.fromarray((rough.clip(0, 1) * 255).astype(np.uint8)), 'ruby_blade_rough')
    save(Image.fromarray(((n + 1) * 127.5).clip(0, 255).astype(np.uint8)), 'ruby_blade_nor')


def _wrap_noise(rng, w, h, cells):
    """Smooth, seamlessly tiling noise in 0..1."""
    g = rng.random((cells, cells)).astype(np.float32)
    big = np.tile(g, (3, 3))
    img = Image.fromarray((big * 255).astype(np.uint8)).resize((w * 3, h * 3), Image.BICUBIC)
    a = np.asarray(img).astype(np.float32)[h:2 * h, w:2 * w] / 255
    return a


def _normal(height, k):
    gy, gx = np.gradient(height)
    n = np.stack([-gx * k, gy * k, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return Image.fromarray(((n + 1) * 127.5).clip(0, 255).astype(np.uint8))


def _gray(a):
    return Image.fromarray((np.stack([a] * 3, -1).clip(0, 1) * 255).astype(np.uint8))


def antique(w, h, seed):
    """Antiqued silver like the Colt prop: grey metal, darker where grime
    sits, lighter where hands wear it, fine scratches. Returns col, rough."""
    rng = np.random.default_rng(seed)
    blot = _wrap_noise(rng, w, h, 10) * 0.6 + _wrap_noise(rng, w, h, 40) * 0.4
    col = 0.42 + 0.18 * (blot - 0.5) * 2
    rough = 0.4 + 0.18 * (1 - blot)
    scratch = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(scratch)
    for _ in range(420):
        x, y = rng.random() * w, rng.random() * h
        a = rng.normal(0, 0.5)
        l = rng.random() * 18 + 4
        d.line([(x, y), (x + math.cos(a) * l, y + math.sin(a) * l)], fill=int(rng.random() * 140 + 60), width=1)
    sc = np.asarray(scratch).astype(np.float32) / 255
    col = col + 0.12 * sc
    return col, rough


def scrolls(w, h, seed, spacing=15, width=1):
    """A seamless field of fine floral scrollwork: curling stems with leaves."""
    import random
    rnd = random.Random(seed)
    img = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(img)
    for gy in range(0, h, spacing):
        for gx in range(0, w, spacing):
            cx, cy = gx + rnd.uniform(-4, 4), gy + rnd.uniform(-4, 4)
            s = spacing * rnd.uniform(0.55, 0.75)
            rot, flip = rnd.uniform(0, 2 * math.pi), rnd.choice((1, -1))
            stem = []
            for i in range(30):
                t = i / 29 * 1.7 * math.pi
                r = s * (1 - 0.72 * t / (1.7 * math.pi))
                stem.append((cx + r * math.cos(flip * t + rot), cy + r * math.sin(flip * t + rot)))
            leaves = []
            for j in (4, 11, 18):
                (ax_, ay_), (bx_, by_) = stem[j], stem[j + 1]
                ang = math.atan2(by_ - ay_, bx_ - ax_) - flip * 1.1
                ln = s * 0.55
                mid = (ax_ + math.cos(ang) * ln * 0.5 + math.cos(ang + 1.57) * ln * 0.18,
                       ay_ + math.sin(ang) * ln * 0.5 + math.sin(ang + 1.57) * ln * 0.18)
                leaves.append([(ax_, ay_), mid, (ax_ + math.cos(ang) * ln, ay_ + math.sin(ang) * ln)])
            for ox in (-w, 0, w):
                for oy in (-h, 0, h):
                    d.line([(x + ox, y + oy) for x, y in stem], fill=230, width=width, joint='curve')
                    for lf in leaves:
                        d.line([(x + ox, y + oy) for x, y in lf], fill=200, width=width, joint='curve')
    return np.asarray(img.filter(ImageFilter.GaussianBlur(0.4))).astype(np.float32) / 255


def colt_textures():
    """The Colt: antiqued silver (plain and engraved), the barrel with its
    motto, the walnut grip with a pentagram, the numbered rounds, the case."""
    spec = json.load(open(os.path.join(ROOT, 'tools', 'blender', 'blades.json')))['colt']
    # plain and engraved silver tiles (box-mapped at 4 tiles a metre)
    col, rough = antique(512, 512, 11)
    save(_gray(col), 'colt_plain_col')
    save(Image.fromarray((rough.clip(0, 1) * 255).astype(np.uint8)), 'colt_plain_rough')
    save(_normal(np.zeros((8, 8), np.float32), 1), 'colt_plain_nor')
    e = scrolls(512, 512, 5)
    save(_gray(col * (1 - 0.5 * e)), 'colt_engraved_col')
    save(Image.fromarray(((rough + 0.3 * e).clip(0, 1) * 255).astype(np.uint8)), 'colt_engraved_rough')
    save(_normal(-e * 0.5, 1.0), 'colt_engraved_nor')

    # the barrel: u along it, the text on the band v 0.2..0.8 (the face towards the viewer)
    bw, bh = 1024, 128
    col, rough = antique(bw, bh, 12)
    x0, x1, R = spec['barrel']
    face = 2 * R * math.sin(math.pi / 8)             # width of one flat
    px_u, px_v = bw / (x1 - x0), bh * 0.6 / face        # pixels per metre, each way
    font = ImageFont.truetype(os.path.join(ROOT, 'assets-src', 'fonts', 'UnifrakturMaguntia-Book.ttf'), 120)
    probe = Image.new('L', (1400, 200), 0)
    ImageDraw.Draw(probe).text((20, 20), 'non timebo mala', font=font, fill=255)
    probe = probe.crop(probe.getbbox())
    letter_h = 0.0042                                   # metres, the x-height-ish height of the line
    th = int(letter_h * px_v)
    tw_m = (x1 - x0) * (spec['text_u'][1] - spec['text_u'][0])
    text = probe.resize((int(tw_m * px_u), th), Image.LANCZOS)
    m = Image.new('L', (bw, bh), 0)
    m.paste(text, (int(spec['text_u'][0] * bw), int(bh * 0.5 - th / 2)))
    t = np.asarray(m).astype(np.float32) / 255
    save(_gray(col * (1 - 0.7 * t)), 'colt_barrel_col')
    save(Image.fromarray(((rough + 0.3 * t).clip(0, 1) * 255).astype(np.uint8)), 'colt_barrel_rough')
    save(_normal(-t * 0.6, 1.5), 'colt_barrel_nor')

    # the grip: walnut with the grain along it, a pentagram burned in near the butt
    g = spec['grip']
    gx = [p[0] for p in g]
    gy = [p[1] for p in g]
    gw, gh_ = 512, int(512 * (max(gy) - min(gy)) / (max(gx) - min(gx)))
    wal = Image.open(os.path.join(OUT, 'walnut_col.png')).transpose(Image.Transpose.ROTATE_90)
    wal = np.asarray(wal.resize((512, 512))).astype(np.float32) / 255
    wal = np.tile(wal, (int(np.ceil(gh_ / 512)), 1, 1))[:gh_] * np.array([1.3, 1.16, 1.04], np.float32)
    pent = Image.new('L', (gw, gh_), 0)
    d = ImageDraw.Draw(pent)
    u, v, r = spec['pentagram']
    cx, cy, rp = u * gw, (1 - v) * gh_, r / (max(gx) - min(gx)) * gw
    d.ellipse([cx - rp, cy - rp, cx + rp, cy + rp], outline=255, width=4)
    star = [(cx + rp * 0.94 * math.sin(2 * math.pi * k * 2 / 5), cy - rp * 0.94 * math.cos(2 * math.pi * k * 2 / 5)) for k in range(6)]
    d.line(star, fill=255, width=4, joint='curve')
    pm = np.asarray(pent.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255
    gcol = wal * (1 - 0.55 * pm[..., None])
    save(Image.fromarray((gcol.clip(0, 1) * 255).astype(np.uint8)), 'colt_grip_col')
    save(Image.fromarray(((0.42 + 0.3 * pm) * 255).astype(np.uint8)), 'colt_grip_rough')
    save(_normal(-pm * 0.5, 1.5), 'colt_grip_nor')

    # the thirteen rounds: one cell each, u along the round (base to tip), the number on its side
    rs = spec['round']
    cw, ch = 128, 64
    col, rough = antique(cw * 13, ch, 13)
    nm = Image.new('L', (cw * 13, ch), 0)
    hand = ImageFont.truetype(os.path.join(ROOT, 'public', 'fonts', 'ReenieBeanie-Regular.ttf'), 96)
    a0, a1 = rs['digit_at']
    for i in range(13):
        glyph_img = Image.new('L', (160, 120), 0)
        ImageDraw.Draw(glyph_img).text((10, 0), str(i + 1), font=hand, fill=255, stroke_width=2, stroke_fill=255)
        glyph_img = glyph_img.crop(glyph_img.getbbox()).rotate(-90, expand=True)
        wpx = int((a1 - a0) / rs['length'] * cw)
        hpx = int(ch * (0.46 if i >= 9 else 0.34))
        glyph_img = glyph_img.resize((wpx, hpx), Image.LANCZOS)
        nm.paste(glyph_img, (int(i * cw + a0 / rs['length'] * cw), int(ch / 2 - hpx / 2)))
    n = np.asarray(nm).astype(np.float32) / 255
    save(_gray(col * (1 - 0.6 * n)), 'colt_rounds_col')
    save(Image.fromarray(((rough + 0.3 * n).clip(0, 1) * 255).astype(np.uint8)), 'colt_rounds_rough')
    save(_normal(-n * 0.6, 1.5), 'colt_rounds_nor')


def m1911_textures():
    """Dean's M1911A1: satin stainless (plain, and engraved with scrollwork
    like the reference), and pearl for the grips."""
    rng = np.random.default_rng(21)
    streak = np.repeat(rng.normal(0, 1, (512, 1)), 512, 1).astype(np.float32)
    streak = (streak - streak.min()) / (streak.max() - streak.min())
    blot = _wrap_noise(rng, 512, 512, 12)
    col = 0.74 + 0.04 * (streak - 0.5) + 0.05 * (blot - 0.5)
    rough = 0.24 + 0.06 * streak + 0.06 * (1 - blot)
    save(_gray(col), 'm1911_plain_col')
    save(Image.fromarray((rough.clip(0, 1) * 255).astype(np.uint8)), 'm1911_plain_rough')
    save(_normal(np.zeros((8, 8), np.float32), 1), 'm1911_plain_nor')
    e = scrolls(512, 512, 17, spacing=40, width=2)
    save(_gray(col * (1 - 0.62 * e)), 'm1911_engraved_col')
    save(Image.fromarray(((rough + 0.38 * e).clip(0, 1) * 255).astype(np.uint8)), 'm1911_engraved_rough')
    save(_normal(-e * 0.6, 1.2), 'm1911_engraved_nor')
    # pearl: a creamy white with soft, drifting swirls and a faint rainbow in them
    a = _wrap_noise(rng, 512, 512, 6)
    b = _wrap_noise(rng, 512, 512, 14)
    swirl = np.sin((a * 3.0 + b * 1.4) * 2 * math.pi) * 0.5 + 0.5
    base = np.array([0.97, 0.94, 0.88], np.float32)
    tint = np.stack([0.02 * np.sin(swirl * 6.28), 0.015 * np.sin(swirl * 6.28 + 2.1), 0.02 * np.sin(swirl * 6.28 + 4.2)], -1)
    pcol = base * (0.9 + 0.1 * swirl[..., None]) + tint
    save(Image.fromarray((pcol.clip(0, 1) * 255).astype(np.uint8)), 'pearl_col')
    save(Image.fromarray(((0.3 + 0.08 * (1 - swirl)) * 255).astype(np.uint8)), 'pearl_rough')
    save(_normal(swirl * 0.05, 1), 'pearl_nor')


def emf_textures():
    """The EMF meter the brothers carry for most of the show: a bare green
    perfboard (copper pads on a 0.1" grid) and an analogue meter face with a
    yellow-to-red scale and a red needle."""
    # perfboard, mapped over the whole board: 120 x 105 mm
    W, H = 0.12, 0.105
    w, h = 512, int(512 * H / W)
    img = Image.new('RGB', (w, h), (26, 66, 30))
    d = ImageDraw.Draw(img)
    px = w / W
    pitch = 0.00254 * px
    y = 0.005 * px
    while y < h - 0.005 * px:
        x = 0.005 * px
        while x < w - 0.005 * px:
            r = pitch * 0.34
            d.ellipse([x - r, y - r, x + r, y + r], fill=(176, 118, 58))
            r2 = pitch * 0.13
            d.ellipse([x - r2, y - r2, x + r2, y + r2], fill=(18, 14, 10))
            x += pitch
        y += pitch
    for cx, cy in ((0.004, 0.004), (W - 0.004, 0.004), (0.004, H - 0.004), (W - 0.004, H - 0.004)):
        r = 0.0018 * px
        d.ellipse([cx * px - r, cy * px - r, cx * px + r, cy * px + r], fill=(10, 10, 10))
    a = np.asarray(img).astype(np.float32) / 255
    rng = np.random.default_rng(31)
    a *= (0.9 + 0.2 * _wrap_noise(rng, w, h, 8))[..., None]
    save(Image.fromarray((a.clip(0, 1) * 255).astype(np.uint8)), 'emf_board_col')
    pads = (np.asarray(img).astype(np.float32)[..., 0] > 120).astype(np.float32)
    save(Image.fromarray(((0.55 - 0.3 * pads) * 255).astype(np.uint8)), 'emf_board_rough')
    save(_normal(pads * 0.4, 1.5), 'emf_board_nor')

    # meter face: 70 x 42 mm window, scale arcs around a pivot low in the middle
    fw, fh = 700, 420
    face = Image.new('RGB', (fw, fh), (22, 22, 22))
    d = ImageDraw.Draw(face)
    cx, cy = fw / 2, fh * 1.02
    font = ImageFont.truetype(os.path.join(ROOT, 'public', 'fonts', 'LeagueGothic.ttf'), 40)
    small = ImageFont.truetype(os.path.join(ROOT, 'public', 'fonts', 'LeagueGothic.ttf'), 30)
    for k, (r0, r1) in enumerate(((300, 340), (240, 272), (190, 212))):
        for (a0, a1, colr) in ((-148, -64, (236, 204, 36)), (-64, -36, (206, 40, 30))):
            d.pieslice([cx - r1, cy - r1, cx + r1, cy + r1], a0, a1, fill=colr)
        d.pieslice([cx - r0, cy - r0, cx + r0, cy + r0], -150, -30, fill=(22, 22, 22))
    d.text((fw / 2, 34), 'ELECTRO MAGNETIC', font=small, fill=(230, 230, 222), anchor='mm')
    la = math.radians(-138)
    d.text((cx + 320 * math.cos(la), cy + 320 * math.sin(la)), 'LOW', font=small, fill=(24, 24, 20), anchor='mm')
    d.text((fw * 0.78, fh * 0.2), 'DANGER', font=font, fill=(245, 235, 220), anchor='mm')
    ang = math.radians(-128)
    d.line([(cx, cy), (cx + 360 * math.cos(ang), cy + 360 * math.sin(ang))], fill=(214, 30, 22), width=6)
    f = np.asarray(face).astype(np.float32) / 255
    f *= (0.88 + 0.16 * _wrap_noise(rng, fw, fh, 10))[..., None]
    save(Image.fromarray((f.clip(0, 1) * 255).astype(np.uint8)), 'emf_face_col')
    save(Image.fromarray(np.full((8, 8), 90, np.uint8)), 'emf_face_rough')
    save(_normal(np.zeros((8, 8), np.float32), 1), 'emf_face_nor')


def blued():
    """Blued gun steel: blue-black, worn lighter in patches, fine scratches."""
    rng = np.random.default_rng(41)
    wear = _wrap_noise(rng, 512, 512, 18) * 0.6 + _wrap_noise(rng, 512, 512, 60) * 0.4
    wear = np.clip((wear - 0.7) / 0.25, 0, 1) * 0.7
    base = np.array([0.15, 0.16, 0.19], np.float32)
    worn = np.array([0.34, 0.34, 0.35], np.float32)
    col = base * (1 - wear[..., None]) + worn * wear[..., None]
    scratch = Image.new('L', (512, 512), 0)
    d = ImageDraw.Draw(scratch)
    for _ in range(500):
        x, y = rng.random() * 512, rng.random() * 512
        a = rng.normal(0, 0.35)
        l = rng.random() * 24 + 4
        d.line([(x, y), (x + math.cos(a) * l, y + math.sin(a) * l)], fill=int(rng.random() * 150 + 60), width=1)
    sc = np.asarray(scratch).astype(np.float32) / 255
    col = col + 0.18 * sc[..., None]
    rough = 0.3 + 0.12 * wear + 0.1 * _wrap_noise(rng, 512, 512, 30)
    save(Image.fromarray((col.clip(0, 1) * 255).astype(np.uint8)), 'blued_col')
    save(Image.fromarray((rough.clip(0, 1) * 255).astype(np.uint8)), 'blued_rough')
    save(_normal(-sc * 0.2, 1.0), 'blued_nor')


def cooler_textures():
    """The green cooler: green enamel with a fine flake and a few scuffs, and
    the diamond badge on its front (a pattern of triangles and a red plate;
    no maker's lettering)."""
    rng = np.random.default_rng(51)
    flake = rng.random((512, 512)).astype(np.float32)
    blot = _wrap_noise(rng, 512, 512, 9)
    base = np.array([0.2, 0.43, 0.3], np.float32)
    col = base * (0.93 + 0.1 * blot[..., None] + 0.05 * (flake[..., None] - 0.5))
    scuff = Image.new('L', (512, 512), 0)
    d = ImageDraw.Draw(scuff)
    for _ in range(60):
        x, y = rng.random() * 512, rng.random() * 512
        a = rng.random() * math.pi
        l = rng.random() * 30 + 6
        d.line([(x, y), (x + math.cos(a) * l, y + math.sin(a) * l)], fill=int(rng.random() * 120 + 80), width=1)
    sc = np.asarray(scuff).astype(np.float32) / 255
    col = col * (1 - 0.25 * sc[..., None]) + 0.25 * sc[..., None] * np.array([0.7, 0.72, 0.7], np.float32)
    save(Image.fromarray((col.clip(0, 1) * 255).astype(np.uint8)), 'cooler_green_col')
    save(Image.fromarray(((0.3 + 0.1 * flake + 0.25 * sc).clip(0, 1) * 255).astype(np.uint8)), 'cooler_green_rough')
    save(_normal(flake * 0.05 - sc * 0.3, 1.0), 'cooler_green_nor')
    # the badge: a diamond of light and grey triangles, the red Coleman plate in the middle
    w, h = 512, 288
    img = Image.new('RGB', (w, h), (232, 232, 226))
    d = ImageDraw.Draw(img)
    n = 8
    for i in range(n):
        for j in range(n // 2 + 1):
            x0, y0 = i * w / n, j * h / (n / 2)
            shade = (205, 208, 204) if (i + j) % 2 else (240, 240, 236)
            d.polygon([(x0, y0), (x0 + w / n, y0), (x0 + w / (2 * n), y0 + h / n)], fill=shade)
    d.rounded_rectangle([w * 0.33, h * 0.38, w * 0.67, h * 0.62], radius=6, fill=(196, 34, 30))
    script = ImageFont.truetype(os.path.join(ROOT, 'public', 'fonts', 'ReenieBeanie-Regular.ttf'), 64)
    d.text((w * 0.5, h * 0.5), 'Coleman', font=script, fill=(250, 244, 236), anchor='mm', stroke_width=2, stroke_fill=(250, 244, 236))
    b = np.asarray(img).astype(np.float32) / 255
    save(Image.fromarray((b * 255).astype(np.uint8)), 'cooler_badge_col')
    save(Image.fromarray(np.full((8, 8), 70, np.uint8)), 'cooler_badge_rough')
    save(_normal(np.zeros((8, 8), np.float32), 1), 'cooler_badge_nor')


def colt_medallion():
    """The gold medallion on Dean's pearl grips: a black enamel disc with a
    rampant colt in gold, and a gold rim."""
    S = 256
    img = Image.new('RGB', (S, S), (212, 170, 78))
    d = ImageDraw.Draw(img)
    r = S * 0.4
    d.ellipse([S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r], fill=(16, 14, 12))
    # a rearing colt facing left, on its hind legs (unit box, y down)
    horse = [(0.30, 0.13), (0.37, 0.08), (0.42, 0.12), (0.47, 0.22), (0.56, 0.30), (0.66, 0.36), (0.73, 0.46),
             (0.74, 0.58), (0.79, 0.74), (0.86, 0.9), (0.8, 0.91), (0.72, 0.78), (0.66, 0.68), (0.61, 0.72),
             (0.63, 0.9), (0.57, 0.91), (0.55, 0.74), (0.5, 0.62), (0.42, 0.53), (0.33, 0.47), (0.27, 0.42),
             (0.2, 0.47), (0.17, 0.43), (0.25, 0.36), (0.33, 0.39), (0.37, 0.35), (0.28, 0.3), (0.19, 0.3),
             (0.17, 0.25), (0.28, 0.24), (0.34, 0.24), (0.33, 0.19), (0.25, 0.2)]
    k, o = S * 0.56, S * 0.22
    d.polygon([(o + x * k, o + y * k) for x, y in horse], fill=(222, 182, 90))
    d.ellipse([S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r], outline=(236, 200, 110), width=4)
    save(img, 'colt_medallion_col')
    rough = np.where(np.asarray(img).astype(np.float32).mean(2) < 60, 0.45, 0.28)
    save(Image.fromarray((rough * 255).astype(np.uint8)), 'colt_medallion_rough')
    save(_normal(np.zeros((8, 8), np.float32), 1), 'colt_medallion_nor')


def duct_tape_textures():
    """Duct tape: the outside is silver cloth tape (a fine weave showing
    through, a few creases); each side shows the wound layers and the
    cardboard core. The side map is planar over the roll's diameter."""
    rng = np.random.default_rng(61)
    # outside: one tile is 1/6 of the way round (u) by the tape's width (v)
    w = h = 512
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    weft = 0.5 + 0.5 * np.sin(x / w * 2 * math.pi * 44)
    warp = 0.5 + 0.5 * np.sin(y / h * 2 * math.pi * 40)
    weave = (weft * warp) ** 0.6
    blot = _wrap_noise(rng, w, h, 8)
    crease = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(crease)
    for _ in range(9):
        x0, y0 = rng.random() * w, rng.random() * h
        a = rng.normal(math.pi / 2, 0.5)
        l = rng.random() * 160 + 40
        d.line([(x0, y0), (x0 + math.cos(a) * l, y0 + math.sin(a) * l)], fill=255, width=2)
    cr = np.asarray(crease.filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
    col = 0.5 + 0.07 * (weave - 0.5) + 0.06 * (blot - 0.5) - 0.12 * cr
    save(Image.fromarray((np.stack([col, col * 1.0, col * 1.03], -1).clip(0, 1) * 255).astype(np.uint8)), 'ducttape_outer_col')
    save(Image.fromarray(((0.42 + 0.14 * (1 - weave) + 0.1 * cr).clip(0, 1) * 255).astype(np.uint8)), 'ducttape_outer_rough')
    save(_normal(weave * 0.25 - cr * 0.8, 1.2), 'ducttape_outer_nor')
    # sides: centre at the middle of the image, the image spans the outer diameter
    S = 512
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rr = np.hypot(xx - S / 2 + 0.5, yy - S / 2 + 0.5) / (S / 2)       # 1.0 at the outer edge
    RI, RC = 0.038 / 0.055, 0.0412 / 0.055                            # core inside, core outside
    layers = rng.random(70).astype(np.float32)
    idx = np.clip(((rr - RC) / (1 - RC) * 69).astype(int), 0, 69)
    band = 0.5 + 0.08 * layers[idx]
    tape = np.stack([band, band, band * 1.02], -1)
    card = np.array([0.52, 0.39, 0.25], np.float32) * (0.9 + 0.12 * _wrap_noise(rng, S, S, 20))[..., None]
    col = np.where((rr >= RC)[..., None], tape, card)
    col = np.where((rr < RI)[..., None], card * 0.6, col)
    col *= np.clip(1.4 - 0.4 * rr, 0.8, 1.0)[..., None]
    save(Image.fromarray((col.clip(0, 1) * 255).astype(np.uint8)), 'ducttape_side_col')
    rough = np.where(rr >= RC, 0.5 + 0.1 * layers[idx], 0.85)
    save(Image.fromarray((rough.clip(0, 1) * 255).astype(np.uint8)), 'ducttape_side_rough')
    save(_normal(np.zeros((8, 8), np.float32), 1), 'ducttape_side_nor')
    # the inside of the core: plain kraft card
    k = np.array([0.46, 0.34, 0.21], np.float32) * (0.88 + 0.16 * _wrap_noise(rng, 256, 256, 24))[..., None]
    save(Image.fromarray((k.clip(0, 1) * 255).astype(np.uint8)), 'kraft_col')
    save(Image.fromarray(np.full((8, 8), 225, np.uint8)), 'kraft_rough')
    save(_normal(np.zeros((8, 8), np.float32), 1), 'kraft_nor')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    # whittled stakes: weathered wood, warmed and lifted towards fresh-cut
    tile_set('stake_wood', 'rough_wood', rotate=True, tint=(1.12, 0.98, 0.8), gain=1.05)
    # the lashed cross: the same weathered wood, greyer
    tile_set('cross_wood', 'rough_wood', rotate=True, tint=(1.0, 0.95, 0.86), gain=0.82)
    # knife grips: walnut, warmed (the scan is nearly grey)
    tile_set('walnut', 'american_walnut_veneer', tint=(1.05, 0.72, 0.5), gain=0.55, rough_add=-0.1)
    # the stag grip on Ruby's knife: dark willow bark, grain along the grip
    tile_set('stag', 'bark_willow', rotate=True, tint=(1.05, 0.9, 0.78), gain=0.95)
    ruby_blade()
    # the Colt's case: black-painted wood, the grain just showing
    tile_set('black_wood', 'american_walnut_veneer', tint=(1.0, 0.95, 0.9), gain=0.11, rough_add=-0.05)
    colt_textures()
    m1911_textures()
    emf_textures()
    blued()
    cooler_textures()
    colt_medallion()
    duct_tape_textures()
    print('pegboard grid', pegboard())
