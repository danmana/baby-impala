"""Texture sets for the trunk props, built from Poly Haven scans (CC0).

    .venv/bin/python tools/prop_textures.py

Writes 512 px tiles (col / rough / nor) into assets-src/props_tex for the
hand-made props, and the full-size pegboard for the underside of the false
floor (2048 x 1024, one texel per 0.7 mm, holes on a one-inch grid). The
Blender build bakes contact shadows into the pegboard colour afterwards.
"""
import os
import numpy as np
from PIL import Image, ImageFilter

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


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    # whittled stakes: weathered wood, warmed and lifted towards fresh-cut
    tile_set('stake_wood', 'rough_wood', rotate=True, tint=(1.12, 0.98, 0.8), gain=1.05)
    # the lashed cross: the same weathered wood, greyer
    tile_set('cross_wood', 'rough_wood', rotate=True, tint=(1.0, 0.95, 0.86), gain=0.82)
    # knife grips: walnut, warmed (the scan is nearly grey)
    tile_set('walnut', 'american_walnut_veneer', tint=(1.05, 0.72, 0.5), gain=0.55, rough_add=-0.1)
    print('pegboard grid', pegboard())
