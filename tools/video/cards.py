"""Paper scraps, titles and caption layers for the videos, drawn with PIL in
the site's own look: its paper textures, masking tape and fonts (League
Gothic for titles, Reenie Beanie for handwriting, Special Elite for type)."""
import math
import os
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PUB = os.path.join(ROOT, 'public')
W, H = 1920, 1080

INK = (38, 33, 29)
RED = (170, 34, 28)
CREAM = (239, 230, 210)

FONTS = {
    'title': os.path.join(PUB, 'fonts', 'LeagueGothic.ttf'),
    'hand': os.path.join(PUB, 'fonts', 'ReenieBeanie-Regular.ttf'),
    'type': os.path.join(PUB, 'fonts', 'SpecialElite-Regular.ttf'),
}
_tex = {}


def font(kind, size):
    return ImageFont.truetype(FONTS[kind], size)


def texture(name):
    if name not in _tex:
        _tex[name] = Image.open(os.path.join(PUB, 'ui', name)).convert('RGBA')
    return _tex[name]


def tiled(name, w, h, seed=0):
    """the texture tiled to w x h, starting at a random offset"""
    t = texture(name)
    rnd = random.Random(seed)
    ox, oy = rnd.randrange(t.width), rnd.randrange(t.height)
    out = Image.new('RGBA', (w, h))
    for y in range(-oy, h, t.height):
        for x in range(-ox, w, t.width):
            out.paste(t, (x, y))
    return out


def torn_mask(w, h, seed=0, rough=5.0, torn_edges='lrtb'):
    """alpha mask for a paper scrap: straight-ish cut edges, torn ones wander"""
    rnd = np.random.default_rng(seed)
    m = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(m)
    pts = []

    def edge(n, torn):
        if not torn:
            return np.zeros(n)
        walk = np.cumsum(rnd.normal(0, rough * 0.35, n))
        walk -= np.linspace(walk[0], walk[-1], n)
        return np.abs(walk) + np.abs(rnd.normal(0, rough * 0.25, n))

    step = 6
    top = edge(w // step + 1, 't' in torn_edges)
    right = edge(h // step + 1, 'r' in torn_edges)
    bottom = edge(w // step + 1, 'b' in torn_edges)
    left = edge(h // step + 1, 'l' in torn_edges)
    for i, v in enumerate(top):
        pts.append((i * step, v))
    for i, v in enumerate(right):
        pts.append((w - 1 - v, i * step))
    for i, v in enumerate(bottom[::-1]):
        pts.append((w - 1 - i * step, h - 1 - v))
    for i, v in enumerate(left[::-1]):
        pts.append((v, h - 1 - i * step))
    d.polygon(pts, fill=255)
    return m.filter(ImageFilter.GaussianBlur(0.6))


def paper(w, h, kind='paper_page.webp', seed=0, stains=0.0, torn='lrtb'):
    img = tiled(kind, w, h, seed)
    if stains:
        s = tiled('paper_stains.webp', w, h, seed + 7).convert('RGB')
        base = img.convert('RGB')
        mixed = ImageChops.multiply(base, s)
        img = Image.blend(base, mixed, stains).convert('RGBA')
    # a faint darkening towards the edges, like handled paper
    vg = Image.new('L', (w, h), 0)
    ImageDraw.Draw(vg).rectangle([0, 0, w, h], outline=60, width=max(3, min(w, h) // 40))
    vg = vg.filter(ImageFilter.GaussianBlur(min(w, h) / 25))
    dark = Image.new('RGBA', (w, h), (90, 70, 45, 255))
    img = Image.composite(dark, img, vg.point(lambda v: int(v * 0.6)))
    img.putalpha(torn_mask(w, h, seed, torn_edges=torn))
    return img


def tape(length=220, angle=0.0, seed=0):
    t = texture('tape.webp').resize((length, int(length * 128 / 512)))
    return t.rotate(angle, resample=Image.BICUBIC, expand=True)


def shadowed(img, offset=(7, 10), blur=10, opacity=0.5):
    """img with a soft drop shadow, on a canvas padded to fit it"""
    pad = blur * 3 + max(abs(offset[0]), abs(offset[1]))
    out = Image.new('RGBA', (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    a = img.split()[3].point(lambda v: int(v * opacity))
    sh = Image.new('RGBA', img.size, (0, 0, 0, 255))
    sh.putalpha(a)
    layer = Image.new('RGBA', out.size, (0, 0, 0, 0))
    layer.paste(sh, (pad + offset[0], pad + offset[1]), sh)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    out = Image.alpha_composite(out, layer)
    out.alpha_composite(img, (pad, pad))
    return out


def text_size(txt, f):
    box = f.getbbox(txt)
    return box[2] - box[0], box[3] - box[1], box


def scrap(lines, kind='hand', size=96, color=INK, pad=(46, 26), seed=0, angle=-2.0,
          paper_kind='paper_page.webp', with_tape=True, stains=0.15, line_gap=0.95, min_w=0):
    """a torn scrap of paper with a few lines of text on it, rotated, taped, shadowed"""
    if isinstance(lines, str):
        lines = [lines]
    specs = []
    for ln in lines:
        if isinstance(ln, str):
            ln = (ln, kind, size, color)
        specs.append(ln)
    measured = []
    for txt, k, s, c in specs:
        f = font(k, s)
        tw, th, box = text_size(txt, f)
        measured.append((txt, f, c, tw, box, s))
    w = max(min_w, max(m[3] for m in measured) + pad[0] * 2)
    heights = [int(m[5] * line_gap) for m in measured]
    h = sum(heights) + pad[1] * 2 + int(measured[-1][5] * 0.25)
    img = paper(w, h, paper_kind, seed, stains)
    d = ImageDraw.Draw(img)
    y = pad[1]
    for (txt, f, c, tw, box, s), lh in zip(measured, heights):
        d.text(((w - tw) / 2 - box[0], y - box[1] * 0.35), txt, font=f, fill=c)
        y += lh
    img = img.rotate(angle, resample=Image.BICUBIC, expand=True)
    if with_tape:
        rnd = random.Random(seed)
        t = tape(int(min(240, w * 0.45)), angle + rnd.uniform(-8, 8))
        canvas = Image.new('RGBA', (img.width, img.height + t.height // 2), (0, 0, 0, 0))
        canvas.alpha_composite(img, (0, t.height // 2))
        canvas.alpha_composite(t, ((img.width - t.width) // 2 + rnd.randint(-20, 20), 0))
        img = canvas
    return shadowed(img)


def layer():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))


def put(base, img, x, y, anchor='lt'):
    """paste img onto base; anchor l/c/r + t/c/b picks which point of img lands on (x, y)"""
    ax = {'l': 0, 'c': img.width / 2, 'r': img.width}[anchor[0]]
    ay = {'t': 0, 'c': img.height / 2, 'b': img.height}[anchor[1]]
    base.alpha_composite(img, (int(x - ax), int(y - ay)))
    return base


def vignette(strength=0.65):
    """a dark frame edge to sit text on"""
    y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    a = np.clip((r - 0.55) / 0.8, 0, 1) ** 1.5 * strength
    img = np.zeros((H, W, 4), np.uint8)
    img[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(img, 'RGBA')


def gradient(side='bottom', height=420, strength=0.75):
    """a soft dark band along one edge, under captions"""
    a = np.zeros((H, W), np.float32)
    ramp = np.linspace(1, 0, height) ** 1.6 * strength
    if side == 'bottom':
        a[H - height:] = ramp[::-1][:, None]
    elif side == 'top':
        a[:height] = ramp[:, None]
    elif side == 'left':
        a[:, :height] = ramp[None, :]
    img = np.zeros((H, W, 4), np.uint8)
    img[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(img, 'RGBA')


def glow_text(base, txt, kind, size, x, y, color=CREAM, anchor='la', shadow=0.7, blur=8, spacing=0):
    """text straight on the footage, lifted off it by a soft dark glow"""
    f = font(kind, size)
    lay = layer()
    d = ImageDraw.Draw(lay)
    if spacing:
        # letter-spaced: draw glyph by glyph
        tw = sum(f.getlength(ch) for ch in txt) + spacing * (len(txt) - 1)
        ox = {'l': 0, 'm': tw / 2, 'r': tw}[anchor[0]]
        cx = x - ox
        for ch in txt:
            d.text((cx, y), ch, font=f, fill=color + (255,), anchor='l' + anchor[1])
            cx += f.getlength(ch) + spacing
    else:
        d.text((x, y), txt, font=f, fill=color + (255,), anchor=anchor)
    sh = lay.split()[3].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(min(255, v * shadow * 1.6)))
    dark = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    dark.putalpha(sh)
    base.alpha_composite(dark)
    base.alpha_composite(lay)
    return base


def rotate_pts(cx, cy, pts, ang):
    a = math.radians(ang)
    return [(cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a), cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in pts]


PENCIL = (91, 82, 71)


def wrap(txt, f, width):
    words, lines, cur = txt.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if f.getlength(t) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def journal_page(title, body, refs=None, note=None, kicker=None, page=None, width=860, seed=0, angle=0.6):
    """the site's journal page (.lore.sheet) drawn at 2x: a torn page with a red margin
    rule, League Gothic title, typewriter body, handwritten margin note, refs under a
    dashed rule, the page count between two chevrons, two strips of tape"""
    s = 2
    pad_l, pad_r, pad_t = 40 * s, 34 * s, 40 * s
    tw = width - pad_l - pad_r
    ft = font('title', 52 * s)
    fb = font('type', int(15.5 * s))
    fh = font('hand', 25 * s)
    fr = font('type', 12 * s)
    ops, y = [], pad_t
    if kicker:
        ops.append(('t', (pad_l, y), kicker, fh, RED))
        y += 27 * s
    for ln in wrap(title, ft, tw):
        ops.append(('t', (pad_l, y), ln, ft, INK))
        y += int(52 * s * 0.95)
    y += 14 * s
    lh = int(15.5 * s * 1.62)
    for para in body:
        for ln in wrap(para, fb, tw):
            ops.append(('t', (pad_l, y), ln, fb, INK))
            y += lh
        y += 13 * s
    if note:
        y += 6 * s
        ops.append(('bar', (pad_l + 12 * s, y, pad_l + 12 * s, y + 30 * s)))
        ops.append(('t', (pad_l + 24 * s, y - 2 * s), note, fh, INK))
        y += 40 * s
    if refs:
        y += 12 * s
        ops.append(('dash', (pad_l, y, width - pad_r, y)))
        y += 8 * s
        for ln in wrap(refs, fr, tw):
            ops.append(('t', (pad_l, y), ln, fr, PENCIL))
            y += int(12 * s * 1.5)
    if page:
        y += 22 * s
        ops.append(('pager', (width / 2, y + 14 * s), f'{page[0]} / {page[1]}'))
        y += 40 * s
    h = int(y + 30 * s)
    img = paper(width, h, 'paper_page.webp', seed, stains=0.35)
    # the sheet's own shading: darker towards the edges, lighter top-left
    shade = Image.new('L', (width, h), 0)
    ImageDraw.Draw(shade).ellipse([-width * 0.25, -h * 0.2, width * 1.1, h * 0.95], fill=255)
    shade = shade.filter(ImageFilter.GaussianBlur(width / 5))
    dark = Image.new('RGBA', (width, h), (112, 76, 32, 255))
    a = img.split()[3]
    img = Image.composite(img, dark, shade.point(lambda v: int(170 + v / 255 * 85)))
    img.putalpha(a)
    d = ImageDraw.Draw(img)
    d.line([(24 * s, 0), (24 * s, h)], fill=(143, 42, 29, 110), width=3)
    for op in ops:
        if op[0] == 't':
            d.text(op[1], op[2], font=op[3], fill=op[4])
        elif op[0] == 'bar':
            d.line([op[1][:2], op[1][2:]], fill=(143, 42, 29, 150), width=4)
        elif op[0] == 'dash':
            x0, yy, x1, _ = op[1]
            x = x0
            while x < x1:
                d.line([(x, yy), (min(x + 8, x1), yy)], fill=(42, 33, 24, 95), width=2)
                x += 14
        elif op[0] == 'pager':
            cx, cy = op[1]
            d.text((cx, cy), op[2], font=fr, fill=PENCIL, anchor='mm')
            for sgn in (-1, 1):
                x = cx + sgn * 120
                d.line([(x - sgn * 10, cy - 16), (x + sgn * 8, cy), (x - sgn * 10, cy + 16)], fill=INK, width=5, joint='curve')
    img = img.rotate(-angle, resample=Image.BICUBIC, expand=True)
    rnd = random.Random(seed)
    canvas = Image.new('RGBA', (img.width + 40, img.height + 40), (0, 0, 0, 0))
    canvas.alpha_composite(img, (20, 30))
    canvas.alpha_composite(tape(190, -8 + rnd.uniform(-2, 2)), (48, 0))
    canvas.alpha_composite(tape(140, 6 + rnd.uniform(-2, 2)), (canvas.width - 190, 4))
    return shadowed(canvas, offset=(0, 18), blur=16, opacity=0.55)
