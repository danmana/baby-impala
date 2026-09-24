"""Overlay a Blender preview render on a reference photo, aligned by wheel centres.

usage: .venv/bin/python tools/overlay.py <render.png> <reference> <out.png> \
        fx fy rx ry   (reference pixel coords of the front and rear wheel centres)
The render's wheel centres come from .work/preview_info.json ("side").
"""
import json
import sys
from PIL import Image, ImageChops, ImageOps

render_p, ref_p, out_p = sys.argv[1:4]
fx, fy, rx, ry = map(float, sys.argv[4:8])
info = json.load(open('.work/preview_info.json'))
(pfx, pfy), (prx, pry) = info['side']

ren = Image.open(render_p).convert('RGB')
ref = Image.open(ref_p).convert('RGB')
s = (pfx - prx) / (fx - rx) if abs(fx - rx) > 1 else 1
# (the ref may be mirrored relative to the render)
if s < 0:
    ref = ImageOps.mirror(ref)
    fx = ref.width - fx
    rx = ref.width - rx
    s = (pfx - prx) / (fx - rx)
ref = ref.resize((int(ref.width * s), int(ref.height * s)), Image.LANCZOS)
ox = pfx - fx * s
oy = pfy - fy * s
canvas = Image.new('RGB', ren.size, (0, 0, 0))
canvas.paste(ref, (int(round(ox)), int(round(oy))))
edges = ren.convert('L').point(lambda v: 255 if v < 40 else 0)
blend = Image.blend(canvas, ren, 0.45)
red = Image.new('RGB', ren.size, (255, 40, 40))
blend.paste(red, mask=ImageChops.subtract(edges, edges.filter(__import__('PIL.ImageFilter', fromlist=['x']).MinFilter(3))))
blend.save(out_p)
print('saved', out_p, 'scale', s)
