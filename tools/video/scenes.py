"""Scenes drawn frame by frame for the process video: photos pinned to a dark
desk, notes on paper scraps, lines that type themselves out, and a slow push
in over the whole thing. Each scene renders straight into an mp4."""
import math
import multiprocessing as mp
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter

import cards as C

FPS = 60


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def desk(seed=0):
    """dark manila paper, like the site's journal cover, under a vignette"""
    img = C.tiled('paper_manila.webp', C.W, C.H, seed).convert('RGB')
    img = Image.eval(img, lambda v: int(v * 0.22))
    img = img.convert('RGBA')
    img.alpha_composite(C.vignette(0.8))
    return img


def photo(path, width, angle=0.0, seed=0, border=16, tape=True, caption=None, cap_size=58):
    """a print with a white border, a strip of tape and an optional handwritten caption under it"""
    src = Image.open(os.path.join(C.PUB, 'about', path) if not os.path.isabs(path) else path).convert('RGB')
    h = int(width * src.height / src.width)
    src = src.resize((width, h), Image.LANCZOS)
    extra = int(cap_size * 1.25) if caption else 0
    card = Image.new('RGBA', (width + border * 2, h + border * 2 + extra), (240, 236, 226, 255))
    card.paste(src, (border, border))
    if caption:
        d = ImageDraw.Draw(card)
        f = C.font('hand', cap_size)
        d.text((card.width / 2, h + border * 2 + extra * 0.42), caption, font=f, fill=C.INK, anchor='mm')
    card = card.rotate(angle, resample=Image.BICUBIC, expand=True)
    if tape:
        t = C.tape(int(min(230, width * 0.35)), angle + 4 * math.sin(seed * 7.1))
        canvas = Image.new('RGBA', (card.width, card.height + t.height // 2), (0, 0, 0, 0))
        canvas.alpha_composite(card, (0, t.height // 2))
        canvas.alpha_composite(t, ((card.width - t.width) // 2, 0))
        card = canvas
    return C.shadowed(card, offset=(10, 14), blur=14, opacity=0.6)


class Item:
    """an image that drops onto the desk at time t: fades in while settling from slightly larger"""

    def __init__(self, img, x, y, t=0.0, anchor='cc', drop=0.3):
        self.img, self.x, self.y, self.t, self.anchor, self.drop = img, x, y, t, anchor, drop

    def draw(self, frame, now):
        k = ease((now - self.t) / self.drop)
        if k <= 0:
            return
        img = self.img
        s = 1.0 + 0.05 * (1 - k)
        if s != 1.0:
            img = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR)
        if k < 1:
            a = img.split()[3].point(lambda v: int(v * k))
            img = img.copy()
            img.putalpha(a)
        C.put(frame, img, self.x, self.y, self.anchor)


class Typed:
    """lines of text typed out one character at a time from t, `cps` characters a second"""

    def __init__(self, lines, x, y, t=0.0, kind='type', size=44, color=C.CREAM, cps=38, gap=1.45,
                 pause=0.25, glow=True, anchor='la'):
        self.lines, self.x, self.y, self.t = lines, x, y, t
        self.f = C.font(kind, size)
        self.size, self.color, self.cps, self.gap, self.pause, self.glow, self.anchor = size, color, cps, gap, pause, glow, anchor

    def draw(self, frame, now):
        el = now - self.t
        if el <= 0:
            return
        lay = C.layer()
        d = ImageDraw.Draw(lay)
        y = self.y
        for ln in self.lines:
            n = int(el * self.cps)
            if n <= 0:
                break
            d.text((self.x, y), ln[:n], font=self.f, fill=self.color + (255,), anchor=self.anchor)
            el -= len(ln) / self.cps + self.pause
            y += self.size * self.gap
        if self.glow:
            sh = lay.split()[3].filter(ImageFilter.GaussianBlur(7)).point(lambda v: min(255, int(v * 1.2)))
            dark = Image.new('RGBA', lay.size, (0, 0, 0, 255))
            dark.putalpha(sh)
            frame.alpha_composite(dark)
        frame.alpha_composite(lay)


class Scene:
    def __init__(self, dur, items, push=(1.0, 1.045), focus=(0.5, 0.5), bg=None, seed=0):
        self.dur, self.items, self.push, self.focus = dur, items, push, focus
        self.bg = bg if bg is not None else desk(seed)

    def frame(self, now):
        f = self.bg.copy()
        for it in self.items:
            it.draw(f, now)
        # the slow push in: scale about the focus point, sub-pixel smooth
        s = self.push[0] + (self.push[1] - self.push[0]) * ease(now / self.dur)
        fx, fy = self.focus[0] * C.W, self.focus[1] * C.H
        # output pixel (x, y) samples input ((x - fx) / s + fx, ...)
        a, e = 1 / s, 1 / s
        c, g = fx - fx / s, fy - fy / s
        return f.convert('RGB').transform((C.W, C.H), Image.AFFINE, (a, 0, c, 0, e, g), resample=Image.BICUBIC)

    def render(self, path):
        """frames are drawn in parallel (forked workers share the scene) and piped to ffmpeg in order"""
        global _scene
        _scene = self
        n = int(round(self.dur * FPS))
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                              '-s', f'{C.W}x{C.H}', '-framerate', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', path],
                             stdin=subprocess.PIPE)
        with mp.get_context('fork').Pool(max(2, os.cpu_count() - 1)) as pool:
            for buf in pool.imap(_frame, range(n), chunksize=4):
                p.stdin.write(buf)
        p.stdin.close()
        p.wait()
        return path


_scene = None


def _frame(i):
    return _scene.frame(i / FPS).tobytes()
