"""The drawn scenes of the process video, told from the About page."""
import cards as C
from scenes import Item, Scene, Typed, photo

INK = C.INK


def sheet(w, h, seed=0):
    return C.shadowed(C.paper(w, h, 'paper_page.webp', seed, stains=0.12), offset=(10, 14), blur=16, opacity=0.6)


def brief(dur):
    lines = [
        '# Baby Impala',
        '',
        "I've been re-watching Supernatural lately",
        'and I want to make a nice/fun fan page',
        'centered on Dean\'s car "Baby". A 3d hyper',
        'realistic representation, with all the',
        'distinctive features from the show and the',
        'lore around it, classic rock music, and an',
        'exploded view animation.',
        '',
        'KAZ 2Y5: KAZ -> Kansas, 2Y5 -> 2005.',
        'Two spotlights by the A-pillars.',
        "Sam's green toy soldier in the ashtray.",
        'No flames, racing stripes or decals.',
    ]
    return Scene(dur, [
        Item(sheet(1060, 930, 4), 120, 75, t=0.0, anchor='lt'),
        Typed(lines, 245, 195, t=0.3, size=36, color=INK, cps=100, gap=1.55, pause=0.06, glow=False),
        Item(C.scrap([('The brief', 'title', 130, INK), ('researched with ChatGPT,', 'hand', 70, INK),
                      ('a long page of lore', 'hand', 70, INK)], seed=21, angle=3, line_gap=0.95, pad=(56, 26)),
             1470, 400, t=1.2),
        Item(C.scrap([('every detail on the car', 'hand', 68, C.RED)], seed=22, angle=-4, with_tape=False, pad=(36, 14)),
             1460, 760, t=3.6),
    ], focus=(0.3, 0.45))


def review(dur):
    quotes = [
        "Dan's review of round one:",
        '',
        'Too dark to see the details.',
        "The paper didn't look like paper.",
        'The spotlights: a paintbrush blob.',
        "You couldn't rotate the camera.",
    ]
    return Scene(dur, [
        Item(photo('v1_normal.webp', 700, -3, 1, caption='round one: black on black'), 430, 540, t=0.1),
        Typed(quotes, 870, 330, t=0.4, size=50, cps=70, gap=1.45, pause=0.12),
    ], focus=(0.55, 0.5))


def round2(dur):
    return Scene(dur, [
        Item(photo('v1_normal.webp', 760, -3, 1, caption='round one'), 500, 560, t=-1),
        Item(photo('v2_normal.webp', 820, 2.5, 2, caption='round two: now you can read her shape'), 1400, 520, t=0.15),
    ], push=(1.03, 1.07), focus=(0.6, 0.5))


def build(dur):
    lines = [
        'npm run model   ->   Blender 5.2, headless',
        'source_model  cleanup  panels  baby_parts',
        'trunk  engine  interior  bake',
        '~4,000 lines of Python. Same car, every run.',
    ]
    return Scene(dur, [
        Item(photo('base_vs_final.webp', 1500, -1, 3, caption='the CC BY base model, and Baby after the build', cap_size=54),
             C.W / 2, 400, t=0.1),
        Typed(lines, C.W / 2, 770, t=0.7, size=46, cps=80, gap=1.4, pause=0.12, anchor='ma'),
    ], focus=(0.5, 0.45))


def bugs(dur):
    return Scene(dur, [
        Item(photo('bug_chrome.webp', 800, -3, 4, caption='bug: the paint turned to chrome'), 500, 480, t=0.1),
        Item(photo('bug_glints.webp', 800, 2.5, 5, caption='bug: every glint a pinpoint'), 1420, 500, t=0.8),
        Item(C.scrap("and Dan's browser was showing a three-day-old model", size=62, seed=23, angle=-2),
             C.W / 2, 960, t=2.4),
    ], focus=(0.5, 0.5))


def refs(dur):
    return Scene(dur, [
        Item(photo('colt.webp', 430, -2.5, 6, caption='the Colt', cap_size=46), 255, 400, t=0.1),
        Item(photo('m1911.webp', 400, 2, 7, caption="Dean's M1911A1", cap_size=46), 715, 380, t=0.6),
        Item(photo('knives_ref.webp', 340, 1.5, 8, caption="Ruby's knife", cap_size=46), 1170, 410, t=1.1),
        Item(photo('emf.webp', 420, -2, 9, caption='the EMF meter', cap_size=46), 1640, 390, t=1.6),
        Item(C.scrap([('from reference photos', 'hand', 76, INK), ('engraving & etching drawn in Python', 'hand', 58, INK)],
                     seed=24, angle=-2.5, line_gap=1.0), C.W / 2, 850, t=2.6),
    ], focus=(0.5, 0.5), push=(1.0, 1.02))


def tested(dur):
    lines = [
        'Every change, checked in a real',
        'Chrome that Claude drove itself:',
        '',
        'real clicks, drags and hovers,',
        'screenshots it looked at,',
        'phones in emulation.',
    ]
    return Scene(dur, [
        Item(photo('mobile.webp', 280, -3, 10, tape=True), 250, 560, t=0.1),
        Item(photo('mobile_trunk.webp', 280, 2.5, 11, tape=True), 590, 540, t=0.4),
        Typed(lines, 820, 330, t=0.6, size=52, cps=65, gap=1.45, pause=0.12),
    ], focus=(0.5, 0.5))


def stats(dur):
    lines = [
        'Claude Opus 5.5, in Claude Code',
        '8 rounds of feedback, 4 days',
        '31 prompts, 1 session',
        '3 context compactions',
        '~7 hours of model time',
        '11,700+ lines of code',
        '$307 at API prices',
    ]
    return Scene(dur, [
        Item(sheet(1320, 900, 12), C.W / 2, C.H / 2 + 20, t=0.0),
        Item(C.scrap([('The numbers', 'title', 120, INK)], seed=25, angle=-2, pad=(50, 16)), C.W / 2, 150, t=0.2),
        Typed(lines, 430, 290, t=0.6, size=56, color=INK, cps=42, gap=1.42, pause=0.22, glow=False),
        Item(C.scrap([('nothing placed by hand', 'hand', 74, C.RED)], seed=26, angle=4, with_tape=False, pad=(36, 12)),
             1400, 930, t=6.6),
    ], focus=(0.5, 0.5), push=(1.0, 1.03))
