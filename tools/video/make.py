"""Cut the videos: clips from the capture mode (.work/video/clips), caption
layers drawn by cards.py, the site's own music and sound effects.

    .venv/bin/python tools/video/make.py demo|trunk|process [--draft]

Writes .work/video/out/<video>.mp4 (1920x1080, 60 fps, H.264 + AAC). An edit
is a list of segments laid end to end (a clip and an in point, or a scene
drawn frame by frame), caption layers that fade in and out over them, a music
bed and sound effects at set times.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import cards as C  # noqa: E402
import process as P  # noqa: E402

ROOT = C.ROOT
WORK = os.path.join(ROOT, '.work', 'video')
CLIPS = os.environ.get('VIDEO_CLIPS') or os.path.join(WORK, 'clips')
FPS = 60


def seg(clip, dur, start=0.0, fade=0.0):
    """`dur` seconds of a clip from `start`; `fade` crossfades in from the previous segment"""
    return dict(clip=clip, dur=dur, start=start, fade=fade)


def drawn(make, dur, fade=0.0):
    """a scene drawn frame by frame (scenes.py): make(dur) returns it"""
    return dict(scene=make, dur=dur, start=0.0, fade=fade)


def cap(t0, t1, draw, slide=16, fade=0.35, slide_x=0, slide_dur=None):
    """a caption layer: draw(layer) paints it; shown t0..t1, fading and sliding in
    (up by `slide` px, or in from the right by `slide_x` px)"""
    return dict(t0=t0, t1=t1, draw=draw, slide=slide, fade=fade, slide_x=slide_x, slide_dur=slide_dur or fade)


def sfx(t, name, gain=1.0):
    return dict(t=t, name=name, gain=gain)


# ------------------------------------------------------------------ captions
def note(text, x=110, y=C.H - 80, angle=-2.5, seed=1, size=104, anchor='lb'):
    def draw(L):
        C.put(L, C.scrap(text, size=size, seed=seed, angle=angle), x, y, anchor)
    return draw


def title_card(L):
    L.alpha_composite(C.gradient('top', 420, 0.55))
    t = C.scrap([('Baby', 'title', 150, C.INK), ("'67 Chevrolet Impala, four-door hardtop", 'hand', 50, C.INK)],
                pad=(60, 22), seed=3, angle=-2, line_gap=0.92)
    C.put(L, t, 70, 30)


def end_card(L):
    L.alpha_composite(C.vignette(0.85))
    e = C.scrap([('Baby', 'title', 190, C.INK), ('baby-impala.vercel.app', 'type', 50, C.INK),
                 ('built by Claude Opus 5.5, live in your browser', 'hand', 56, C.RED)],
                pad=(80, 36), seed=11, angle=1.5, line_gap=1.12)
    C.put(L, e, C.W / 2, C.H / 2, 'cc')


def process_title(L):
    L.alpha_composite(C.vignette(0.5))
    t = C.scrap([('How Baby was built', 'title', 150, C.INK), ('by Claude Opus 5.5, with Dan', 'hand', 66, C.INK)],
                pad=(80, 30), seed=31, angle=-2.5, line_gap=0.95)
    C.put(L, t, 110, 90)


def process_end(L):
    L.alpha_composite(C.vignette(0.85))
    e = C.scrap([('Baby', 'title', 190, C.INK), ('baby-impala.vercel.app', 'type', 50, C.INK),
                 ('the whole story is on the About page', 'hand', 56, C.RED)],
                pad=(80, 36), seed=32, angle=-1.5, line_gap=1.12)
    C.put(L, e, C.W / 2, C.H / 2, 'cc')


def page(title, body, refs=None, note=None, kicker=None, n=None, seed=0):
    """a journal page from the site, on the right of the frame"""
    def draw(L):
        img = C.journal_page(title, body, refs=refs, note=note, kicker=kicker, page=(n, 42) if n else None, seed=seed)
        k = min(1.0, 1000 / img.height, 900 / img.width)
        if k < 1:
            img = img.resize((int(img.width * k), int(img.height * k)), C.Image.LANCZOS)
        C.put(L, img, C.W - 50, C.H / 2 + 10, 'rc')
    return draw


def trunk_end(L):
    L.alpha_composite(C.vignette(0.85))
    e = C.scrap([('Baby', 'title', 190, C.INK), ('baby-impala.vercel.app', 'type', 50, C.INK),
                 ('42 pages of lore in the trunk', 'hand', 60, C.RED)],
                pad=(80, 36), seed=33, angle=1.2, line_gap=1.12)
    C.put(L, e, C.W / 2, C.H / 2, 'cc')


def pagecap(t0, t1, draw):
    return cap(t0, t1, draw, slide=0, slide_x=760, slide_dur=0.55, fade=0.3)


# one bar of Slow Burn (~85 bpm), for the trunk video; the music starts 0.332 s in
# so the first cut, at 6 s, lands on a bar line
TBAR = 2.833
T0 = 0.334


def tbar(k):
    return round(T0 + TBAR * k, 3)


# one bar of Cool Rock (~129 bpm), for the process video
PBAR = 1.8576
P0 = 0.511


def pbar(k):
    return round(P0 + PBAR * k, 3)


# one bar of Hot Rock (~128 bpm): the demo cuts on the bar lines
BAR = 1.881
B0 = 0.752


def bar(k):
    return round(B0 + BAR * k, 3)


VIDEOS = {
    'demo': dict(
        music=dict(file='hotrock.mp3', start=0.0, gain=0.85),
        segments=[
            seg('hero', bar(2)),
            seg('start', bar(4) - bar(2), start=0.3),
            seg('spots', bar(6) - bar(4), start=0.2),
            seg('sunrise', bar(10) - bar(6), start=0.2),
            seg('rain', bar(12) - bar(10), start=0.5),
            seg('exploded', bar(15) - bar(12), start=0.1),
            seg('trunk', bar(18) - bar(15), start=0.6),
            seg('interior', bar(20) - bar(18), start=0.4),
            seg('finale', 8.2, start=0.0),
        ],
        captions=[
            cap(0.5, bar(2) - 0.2, title_card, slide=0),
            cap(bar(2) + 0.5, bar(4) - 0.15, note('start her up', seed=5)),
            cap(bar(4) + 0.4, bar(6) - 0.15, note('A-pillar spotlights, seasons 1-3', seed=6, size=92)),
            cap(bar(6) + 0.6, bar(10) - 0.2, note('the moon sets, the sun comes up', seed=7, size=92)),
            cap(bar(10) + 0.3, bar(12) - 0.15, note('rain at the motel', seed=8)),
            cap(bar(12) + 0.5, bar(15) - 0.2, note('pull her apart', seed=9)),
            cap(bar(15) + 0.4, bar(18) - 0.2, note('pop the trunk', seed=10)),
            cap(bar(18) + 0.3, bar(20) - 0.15, note('climb inside', seed=12)),
            cap(bar(20) + 2.6, bar(20) + 8.2, end_card, slide=0, fade=0.6),
        ],
        sfx=[
            sfx(bar(2) + 0.0, 'engine_start.mp3', 0.9),
            sfx(bar(15) + 1.4, 'trunk_latch.mp3', 0.8),
            sfx(bar(15) + 1.6, 'trunk_creak.mp3', 0.6),
        ],
    ),
    'trunk': dict(
        music=dict(file='slow-burn.mp3', start=0.332, gain=0.9),
        segments=[
            seg('t_approach', tbar(2)),
            seg('t_open', tbar(5) - tbar(2)),
            seg('t_trap', tbar(7) - tbar(5), start=0.2),
            seg('t_board', tbar(9) - tbar(7), start=0.2),
            seg('t_ruby', tbar(11) - tbar(9), start=0.2),
            seg('t_pistol', tbar(13) - tbar(11), start=0.2),
            seg('t_colt', tbar(15) - tbar(13), start=0.2),
            seg('t_emf', tbar(17) - tbar(15), start=0.2),
            seg('t_out', 8.5),
        ],
        captions=[
            cap(0.8, tbar(2) - 0.2, note('pop the trunk', seed=51)),
            cap(tbar(2) + 4.0, tbar(5) - 0.2, note("the Winchesters' armory", seed=52)),
            pagecap(tbar(5) + 0.6, tbar(7) - 0.15, page(
                'The Devil’s Trap',
                ['A pentagram in a circle with sigils in the gaps, hand-painted in rough cream strokes on the black '
                 'underside of the trunk lid. Any demon that steps inside a Devil’s Trap is stuck there: it can’t leave, '
                 'can’t smoke out of its host, can’t use most of its powers.'],
                refs='The symbol: 1.22 “Devil’s Trap”', note='Not decoration.', kicker='Keep the lines unbroken.', n=1, seed=61)),
            cap(tbar(7) + 0.5, tbar(9) - 0.2, note('every piece has a page of lore', seed=53, size=96)),
            pagecap(tbar(9) + 0.7, tbar(11) - 0.15, page(
                'Ruby’s knife',
                ['A demon-killing blade taken from the demon Ruby. For years it is the only thing short of the Colt that '
                 'kills a demon outright.'], refs='Season 3 onward', n=10, seed=62)),
            pagecap(tbar(11) + 0.7, tbar(13) - 0.15, page(
                'Dean’s Colt M1911A1',
                ['Dean’s own gun and his firearm of choice: a nickel-plated Colt M1911A1, engraved, with ivory grips. '
                 'A .45 with seven rounds in the magazine and one in the chamber. He is rarely without it.',
                 'He loads it with silver rounds for monsters, devil’s trap bullets for demons and witch-killing bullets '
                 'for witches. It has been stolen from him more than once, and every time he has got it back.'],
                refs='All seasons. Sam fires it first, in “Something Wicked”.', n=16, seed=63)),
            pagecap(tbar(13) + 0.7, tbar(15) - 0.15, page(
                'The Colt',
                ['The gun that can kill almost anything. John tells the story: made by Samuel Colt in the 1830s, with '
                 'thirteen hand-made bullets. Only a handful of beings in creation are immune.',
                 'It is why the Devil’s Trap is painted on the lid: a demon reaching into the trunk for the Colt gets stuck.'],
                refs='1.20 “Dead Man’s Blood”, 1.22 “Devil’s Trap”', note='Non timebo mala.', n=32, seed=64)),
            pagecap(tbar(15) + 0.7, tbar(17) - 0.15, page(
                'EMF meter',
                ['“It’s an EMF meter. It reads electromagnetic frequencies.” Spirits give off an electromagnetic field, '
                 'so this is how a hunter tells whether a place is really haunted, and sometimes where the body is. '
                 'It makes noise when the reading climbs. Near power lines it is useless.',
                 'Dean’s first one was built out of an old tape player in “Phantom Traveler” and never seen again. This '
                 'one, a bare circuit board with a meter and a row of red lights, is the one they carry from then on.'],
                refs='Every season, from 1.04 “Phantom Traveler”', n=38, seed=65)),
            cap(tbar(17) + 2.2, tbar(17) + 8.5, trunk_end, slide=0, fade=0.6),
        ],
        sfx=[
            sfx(tbar(2) + 0.3, 'trunk_latch.mp3', 0.9),
            sfx(tbar(2) + 0.55, 'trunk_creak.mp3', 0.8),
        ],
    ),
    'process': dict(
        music=dict(file='cool-rock.mp3', start=0.0, gain=0.8),
        segments=[
            seg('sunrise', pbar(3), start=0.3),
            drawn(P.brief, pbar(7) - pbar(3)),
            drawn(P.review, pbar(10) - pbar(7)),
            drawn(P.round2, pbar(12) - pbar(10)),
            drawn(P.build, pbar(15) - pbar(12)),
            seg('exploded', pbar(18) - pbar(15), start=0.1),
            drawn(P.bugs, pbar(21) - pbar(18)),
            drawn(P.refs, pbar(25) - pbar(21)),
            seg('trunk', pbar(28) - pbar(25), start=0.6),
            drawn(P.tested, pbar(31) - pbar(28)),
            drawn(P.stats, pbar(36) - pbar(31)),
            seg('finale', 7.0, start=0.5),
        ],
        captions=[
            cap(0.5, pbar(3) - 0.2, process_title, slide=0),
            cap(pbar(15) + 0.4, pbar(18) - 0.2, note('every part is its own piece', seed=41)),
            cap(pbar(25) + 0.4, pbar(28) - 0.2, note('every piece of gear has a journal page', seed=42, size=92)),
            cap(pbar(36) + 1.0, pbar(36) + 7.0, process_end, slide=0, fade=0.6),
        ],
        sfx=[],
    ),
}


# ------------------------------------------------------------------ build
def build(name, draft=False):
    v = VIDEOS[name]
    build_dir = os.path.join(WORK, 'build', name)
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(os.path.join(WORK, 'out'), exist_ok=True)
    segs = v['segments']
    total = sum(s['dur'] for s in segs) - sum(s['fade'] for s in segs[1:])
    args = ['ffmpeg', '-y', '-loglevel', 'error', '-stats']
    fc = []
    n_in = 0

    def add_input(*a):
        nonlocal n_in
        args.extend(a)
        n_in += 1
        return n_in - 1

    # video segments, normalised and chained with cuts or crossfades
    labels = []
    for i, s in enumerate(segs):
        if 'scene' in s:
            path = os.path.join(build_dir, f'scene{i:02d}.mp4')
            if not (os.path.exists(path) and '--keep-scenes' in sys.argv):
                print('drawing', s['scene'].__name__, flush=True)
                s['scene'](s['dur']).render(path)
        else:
            path = os.path.join(CLIPS, s['clip'] + '.mp4')
        k = add_input('-ss', f'{s["start"]:.3f}', '-t', f'{s["dur"]:.3f}', '-i', path)
        fc.append(f'[{k}:v]fps={FPS},scale={C.W}:{C.H},format=yuv420p,setsar=1,settb=AVTB,setpts=PTS-STARTPTS[v{i}]')
        labels.append(f'v{i}')
    acc, acc_len = labels[0], segs[0]['dur']
    for i in range(1, len(segs)):
        s = segs[i]
        out = f'c{i}'
        if s['fade'] > 0:
            fc.append(f'[{acc}][{labels[i]}]xfade=transition=fade:duration={s["fade"]}:offset={acc_len - s["fade"]:.3f}[{out}]')
            acc_len += s['dur'] - s['fade']
        else:
            fc.append(f'[{acc}][{labels[i]}]concat=n=2:v=1:a=0[{out}]')
            acc_len += s['dur']
        acc = out
    # caption layers
    for j, c in enumerate(v['captions']):
        png = os.path.join(build_dir, f'cap{j:02d}.png')
        L = C.layer()
        c['draw'](L)
        L.save(png)
        dur = c['t1'] - c['t0']
        k = add_input('-loop', '1', '-framerate', str(FPS), '-t', f'{dur:.3f}', '-i', png)
        f = c['fade']
        fc.append(f'[{k}:v]format=rgba,fade=t=in:st=0:d={f}:alpha=1,fade=t=out:st={dur - f:.3f}:d={f}:alpha=1,'
                  f'setpts=PTS-STARTPTS+{c["t0"]:.3f}/TB[k{j}]')
        sd = c['slide_dur']
        # ease-out: 1 - (1 - p)^3 of the way in
        prog = f"pow(1-min(1,max(0,(t-{c['t0']:.3f})/{sd})),3)"
        y = f"'{c['slide']}*{prog}'" if c['slide'] else '0'
        x = f"'{c['slide_x']}*{prog}'" if c['slide_x'] else '0'
        fc.append(f'[{acc}][k{j}]overlay=x={x}:y={y}:eof_action=pass:eval=frame[o{j}]')
        acc = f'o{j}'
    fc.append(f'[{acc}]fade=t=in:st=0:d=0.5,fade=t=out:st={total - 1.0:.3f}:d=1.0[vout]')
    # sound: music bed plus effects
    m = v['music']
    k = add_input('-ss', str(m['start']), '-t', f'{total:.3f}', '-i', os.path.join(C.PUB, 'audio', m['file']))
    fc.append(f'[{k}:a]aresample=48000,volume={m["gain"]},afade=t=in:st=0:d=0.3,afade=t=out:st={total - 2.0:.3f}:d=2.0[mus]')
    mix = ['[mus]']
    for j, e in enumerate(v.get('sfx', [])):
        k = add_input('-i', os.path.join(C.PUB, 'audio', 'sfx', e['name']))
        ms = int(e['t'] * 1000)
        fc.append(f'[{k}:a]aresample=48000,volume={e["gain"]},adelay={ms}|{ms}[s{j}]')
        mix.append(f'[s{j}]')
    fc.append(f'{"".join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first,'
              f'loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[aout]')
    out = os.path.join(WORK, 'out', f'{name}{"_draft" if draft else ""}.mp4')
    graph = os.path.join(build_dir, 'graph.txt')
    with open(graph, 'w') as fh:
        fh.write(';\n'.join(fc))
    args += ['-/filter_complex', graph, '-map', '[vout]', '-map', '[aout]', '-t', f'{total:.3f}',
             '-c:v', 'libx264', '-preset', 'veryfast' if draft else 'slow', '-crf', '23' if draft else '17',
             '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-r', str(FPS),
             '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out]
    subprocess.run(args, check=True)
    print(f'{out}  {total:.1f}s')
    return out


if __name__ == '__main__':
    build(sys.argv[1], '--draft' in sys.argv)
