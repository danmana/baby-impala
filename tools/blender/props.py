"""Small procedural props for the trunk arsenal and the cabin.

Every builder creates its geometry around the origin, lying along +X
(length), with +Z up, and returns one joined object. Placement happens in
trunk.py / interior.py.
"""
import math
from mathutils import Vector, Matrix
import lib as L


def _circle(r, n=12):
    return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rod(name, a, b, r, mat, n=10, taper=None):
    return L.sweep(name, [Vector(a), Vector(b)], _circle(r, n), mat,
                   scale=(lambda t: 1 - (1 - taper) * t) if taper else None)


def blade(name, length, width, thick, mat='steel', tip=0.25, curve=0.0, clip=False):
    """Flat blade along +X from 0 to length, edge down (-Y)."""
    pts = [(0, -width * 0.5), (length * (1 - tip), -width * 0.5 - curve * width)]
    pts.append((length, width * (0.1 if clip else -0.2)))
    if clip:
        pts.append((length * (1 - tip * 0.6), width * 0.5))
    pts.append((0, width * 0.5))
    o = L.extrude_outline(name, pts, thick, mat, bevel_w=thick * 0.3)
    o.data.transform(Matrix.Translation((0, 0, -thick / 2)))
    # stand the blade up: width along Z
    o.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    return o


def knife(name, length=0.3, blade_frac=0.6, width=0.035, handle_mat='wood', guard=True, blade_mat='steel'):
    bl = length * blade_frac
    parts = [blade(name + '_b', bl, width, 0.004, blade_mat)]
    parts[0].location = (0, 0, 0)
    hl = length - bl
    h = L.box(name + '_h', (hl, 0.022, 0.03), (-hl / 2, 0, 0), handle_mat, bevel=0.008)
    parts.append(h)
    if guard:
        parts.append(L.box(name + '_g', (0.01, 0.024, width * 1.9), (0, 0, 0), 'brass', bevel=0.002))
    parts.append(L.box(name + '_p', (0.012, 0.024, 0.034), (-hl, 0, 0), 'brass', bevel=0.003))
    o = L.join(parts, name)
    o.data.transform(Matrix.Translation((hl / 2 - bl / 2, 0, 0)))
    return o


def machete(name):
    parts = [blade(name + '_b', 0.46, 0.06, 0.004, 'steel_dark', tip=0.18, curve=-0.25)]
    parts.append(L.box(name + '_h', (0.13, 0.026, 0.032), (-0.065, 0, 0), 'rubber', bevel=0.008))
    o = L.join(parts, name)
    o.data.transform(Matrix.Translation((-0.16, 0, 0)))
    return o


def stake(name, length=0.3):
    o = L.lathe(name, [(0, 0.0), (0.07, 0.014), (length, 0.016), (length, 0.0)], segments=8,
                mat='wood', axis='X', close=False)
    o.data.transform(Matrix.Translation((-length / 2, 0, 0)))
    return o


def hatchet(name):
    handle = L.sweep(name + '_h', L.catmull([Vector((-0.2, 0, 0)), Vector((0.0, 0, 0.01)),
                                              Vector((0.17, 0, 0))], 6),
                     L.rounded_rect(0.024, 0.034, 0.008, 2), 'wood', fixed_side=Vector((0, 1, 0)))
    head = L.extrude_outline(name + '_x', [(0.13, -0.02), (0.2, -0.02), (0.22, 0.0), (0.21, 0.09),
                                           (0.16, 0.10), (0.14, 0.03)], 0.012, 'steel_dark', bevel_w=0.003)
    head.data.transform(Matrix.Translation((0, 0, -0.006)))
    head.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    return L.join([handle, head], name)


def arrow(name, length=0.75):
    shaft = rod(name + '_s', (-length / 2, 0, 0), (length / 2 - 0.05, 0, 0), 0.0045, 'wood', 8)
    tip = L.lathe(name + '_t', [(0, 0.012), (0.06, 0.0)], segments=4, mat='steel', axis='X',
                  center=(length / 2 - 0.06, 0, 0))
    parts = [shaft, tip]
    for k in range(3):
        a = 2 * math.pi * k / 3
        f = L.extrude_outline(name + f'_f{k}', [(0, 0), (0.1, 0), (0.08, 0.018), (0.01, 0.02)], 0.001,
                              'feather')
        f.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
        f.data.transform(Matrix.Rotation(a, 4, 'X'))
        f.data.transform(Matrix.Translation((-length / 2 + 0.01, 0, 0)))
        parts.append(f)
    return L.join(parts, name)


def cross(name, h=0.36, w=0.2, t=0.025, mat='wood'):
    a = L.box(name + '_v', (h, t, t * 1.4), (0, 0, 0), mat, bevel=0.004)
    b = L.box(name + '_h', (t * 1.4, w, t * 1.2), (h * 0.22, 0, 0.004), mat, bevel=0.004)
    twine = L.lathe(name + '_tw', [(-0.02, 0.022), (0.02, 0.022)], segments=10, mat='twine', axis='X',
                    center=(h * 0.22, 0, 0.0))
    return L.join([a, b, twine], name)


def sage(name):
    parts = []
    for i in range(9):
        a = 2 * math.pi * i / 9
        r = 0.012 if i else 0.0
        parts.append(rod(name + f'_{i}', (-0.12, r * math.cos(a), r * math.sin(a)),
                         (0.12, r * math.cos(a) * 1.3, r * math.sin(a) * 1.3), 0.009, 'sage', 6))
    for k in range(4):
        parts.append(L.lathe(name + f'_t{k}', [(-0.004, 0.025), (0.004, 0.025)], segments=12, mat='twine', axis='X',
                             center=(-0.09 + 0.06 * k, 0, 0)))
    return L.join(parts, name)


def knuckles(name):
    parts = [L.box(name + '_bar', (0.1, 0.012, 0.02), (0, 0, -0.022), 'brass', bevel=0.005)]
    for i in range(4):
        t = L.lathe(name + f'_r{i}', [(-0.006, 0.011), (-0.006, 0.016), (0.006, 0.016), (0.006, 0.011)],
                    segments=16, mat='brass', axis='Y', center=(-0.036 + 0.024 * i, 0, 0), close=True)
        parts.append(t)
    return L.join(parts, name)


def dreamcatcher(name, r=0.08):
    ring = L.lathe(name + '_ring', [(-0.003, r - 0.004), (-0.003, r + 0.004), (0.003, r + 0.004),
                                    (0.003, r - 0.004)], segments=32, mat='leather', axis='Y', close=True)
    parts = [ring]
    for i in range(8):
        a = 2 * math.pi * i / 8
        b = a + 2 * math.pi * 3 / 8
        parts.append(rod(name + f'_w{i}', (r * math.cos(a), 0, r * math.sin(a)),
                         (r * 0.35 * math.cos(b), 0, r * 0.35 * math.sin(b)), 0.0009, 'twine', 4))
    for k, dx in enumerate((-0.03, 0.0, 0.03)):
        parts.append(rod(name + f'_s{k}', (dx, 0, -r), (dx * 1.2, 0, -r - 0.09), 0.0012, 'leather', 4))
        fe = L.extrude_outline(name + f'_fe{k}', [(-0.006, 0), (0.006, 0), (0.004, -0.06), (0, -0.07),
                                                  (-0.004, -0.06)], 0.001, 'feather')
        fe.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
        fe.data.transform(Matrix.Translation((dx * 1.2, 0, -r - 0.08)))
        parts.append(fe)
    o = L.join(parts, name)
    # lie flat in the XY plane (faces +Z like everything else mounted on the board)
    o.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'X'))
    return o


def pump_shotgun(name, length=0.98):
    parts = []
    parts.append(rod(name + '_bar', (0.0, 0, 0.012), (length * 0.55, 0, 0.012), 0.011, 'gunmetal', 12))
    parts.append(rod(name + '_mag', (0.0, 0, -0.012), (length * 0.48, 0, -0.012), 0.010, 'gunmetal', 12))
    parts.append(L.box(name + '_pump', (0.2, 0.034, 0.03), (length * 0.3, 0, -0.012), 'wood', bevel=0.006))
    parts.append(L.box(name + '_recv', (0.2, 0.034, 0.06), (-0.08, 0, 0.0), 'gunmetal', bevel=0.004))
    stock = L.extrude_outline(name + '_st', [(-0.17, 0.02), (-0.17, -0.03), (-0.26, -0.05), (-0.45, -0.1),
                                             (-0.46, 0.03), (-0.2, 0.03)], 0.036, 'wood', bevel_w=0.008)
    stock.data.transform(Matrix.Translation((0, 0, -0.018)))
    stock.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    parts.append(stock)
    parts.append(L.box(name + '_tg', (0.05, 0.01, 0.025), (-0.1, 0, -0.04), 'gunmetal'))
    o = L.join(parts, name)
    o.data.transform(Matrix.Translation((-length * 0.05, 0, 0)))
    return o


def sawed_off(name):
    parts = []
    for dy in (-0.012, 0.012):
        parts.append(rod(name + f'_b{dy}', (0.0, dy, 0.0), (0.33, dy, 0.0), 0.012, 'gunmetal', 12))
    parts.append(L.box(name + '_fe', (0.16, 0.034, 0.024), (0.1, 0, -0.018), 'wood', bevel=0.005))
    parts.append(L.box(name + '_rc', (0.12, 0.04, 0.05), (-0.06, 0, -0.006), 'gunmetal', bevel=0.004))
    grip = L.extrude_outline(name + '_gr', [(-0.11, 0.02), (-0.12, -0.02), (-0.24, -0.08), (-0.28, -0.05),
                                            (-0.16, 0.02)], 0.034, 'wood', bevel_w=0.006)
    grip.data.transform(Matrix.Translation((0, 0, -0.017)))
    grip.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    parts.append(grip)
    return L.join(parts, name)


def colt(name):
    """The Colt: long octagonal barrel, fluted cylinder, engraved frame, ivory grip."""
    parts = []
    bar = L.lathe(name + '_barrel', [(0.0, 0.0), (0.0, 0.009), (0.2, 0.0085), (0.2, 0.0)], segments=8,
                  mat='gunmetal', axis='X', center=(0.03, 0, 0.012))
    parts.append(bar)
    parts.append(L.cylinder(name + '_cyl', 0.02, 0.05, (0.0, 0, 0.004), axis='X', segments=12, mat='gunmetal',
                            bevel=0.003))
    parts.append(L.box(name + '_frame', (0.06, 0.018, 0.035), (-0.02, 0, 0.0), 'nickel', bevel=0.004))
    grip = L.extrude_outline(name + '_grip', [(-0.03, 0.0), (-0.05, -0.02), (-0.075, -0.1), (-0.05, -0.11),
                                              (-0.02, -0.03), (-0.01, -0.01)], 0.026, 'ivory', bevel_w=0.006)
    grip.data.transform(Matrix.Translation((0, 0, -0.013)))
    grip.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    parts.append(grip)
    parts.append(L.box(name + '_ham', (0.02, 0.008, 0.02), (-0.045, 0, 0.022), 'gunmetal'))
    return L.join(parts, name)


def box_prop(name, size, mat, lid_mat=None, bevel=0.004):
    b = L.box(name, size, (0, 0, size[2] / 2), mat, bevel=bevel)
    if lid_mat:
        lid = L.box(name + '_lid', (size[0] * 1.01, size[1] * 1.01, size[2] * 0.12),
                    (0, 0, size[2] * 0.95), lid_mat, bevel=bevel)
        b = L.join([b, lid], name)
    return b


def ammo_can(name, size=(0.28, 0.14, 0.18)):
    b = L.box(name + '_b', size, (0, 0, size[2] / 2), 'ammo_green', bevel=0.008)
    lid = L.box(name + '_l', (size[0] * 1.02, size[1] * 1.04, 0.02), (0, 0, size[2]), 'ammo_green', bevel=0.004)
    handle = L.box(name + '_h', (0.1, 0.012, 0.01), (0, 0, size[2] + 0.02), 'gunmetal', bevel=0.003)
    return L.join([b, lid, handle], name)


def bottle(name, h=0.2, r=0.04, neck=0.012, mat='bottle_glass', cap='gunmetal', flat=False):
    prof = [(0, 0), (0, r * 0.9), (0.01, r), (h * 0.65, r), (h * 0.8, neck * 1.4), (h * 0.9, neck),
            (h * 0.98, neck)]
    o = L.lathe(name + '_g', [(a, rr) for (a, rr) in prof] + [(h * 0.98, 0.0)], segments=16, mat=mat, axis='Z')
    c = L.cylinder(name + '_c', neck * 1.2, 0.02, (0, 0, h), axis='Z', segments=12, mat=cap)
    o = L.join([o, c], name)
    if flat:
        o.data.transform(Matrix.Diagonal((1.0, 0.45, 1.0, 1.0)))
    return o


def jar(name, h=0.12, r=0.05, mat='bottle_glass', lid='brass'):
    o = L.lathe(name + '_g', [(0, 0), (0, r), (h * 0.85, r), (h * 0.9, r * 0.85), (h, r * 0.85), (h, 0.0)],
                segments=18, mat=mat, axis='Z')
    c = L.cylinder(name + '_c', r * 0.9, 0.02, (0, 0, h + 0.005), axis='Z', segments=16, mat=lid)
    return L.join([o, c], name)


def can(name, h=0.14, r=0.045, mat='salt_blue', top='steel'):
    o = L.cylinder(name + '_b', r, h, (0, 0, h / 2), axis='Z', segments=20, mat=mat)
    t = L.cylinder(name + '_t', r * 0.98, 0.006, (0, 0, h + 0.003), axis='Z', segments=20, mat=top)
    return L.join([o, t], name)


def flashlight(name, length=0.3, r=0.022):
    o = L.lathe(name, [(0, 0.0), (0, r * 0.9), (length * 0.7, r * 0.9), (length * 0.78, r * 1.35),
                       (length, r * 1.35), (length, 0.0)], segments=16, mat='gunmetal', axis='X')
    lens = L.cylinder(name + '_l', r * 1.2, 0.004, (length + 0.001, 0, 0), axis='X', segments=16, mat='lens_clear')
    o = L.join([o, lens], name)
    o.data.transform(Matrix.Translation((-length / 2, 0, 0)))
    return o


def shells_box(name, n=(5, 4), shell='shell_red', size=(0.14, 0.1, 0.07)):
    b = L.box(name + '_box', size, (0, 0, size[2] / 2), 'cardboard', bevel=0.003)
    parts = [b]
    nx, ny = n
    for i in range(nx):
        for j in range(ny):
            x = -size[0] / 2 + size[0] * (i + 0.5) / nx
            y = -size[1] / 2 + size[1] * (j + 0.5) / ny
            parts.append(L.cylinder(name + f'_s{i}{j}', 0.0095, 0.03, (x, y, size[2] + 0.004), axis='Z',
                                    segments=10, mat=shell))
    return L.join(parts, name)


def bullets_box(name):
    b = L.box(name + '_box', (0.1, 0.07, 0.03), (0, 0, 0.015), 'wood', bevel=0.003)
    parts = [b]
    for i in range(5):
        for j in range(4):
            parts.append(L.cylinder(name + f'_b{i}{j}', 0.0045, 0.03,
                                    (-0.04 + 0.02 * i, -0.027 + 0.018 * j, 0.04), axis='Z', segments=8,
                                    mat='silver'))
    return L.join(parts, name)


def bandolier(name, n=16):
    parts = [L.box(name + '_belt', (0.6, 0.05, 0.006), (0, 0, 0.003), 'leather', bevel=0.002)]
    for i in range(n):
        x = -0.28 + 0.56 * i / (n - 1)
        s = L.cylinder(name + f'_s{i}', 0.0095, 0.05, (x, 0, 0.014), axis='Y', segments=10, mat='shell_red')
        parts.append(s)
    o = L.join(parts, name)
    return o


def badge_wallet(name):
    w = L.box(name + '_w', (0.11, 0.075, 0.012), (0, 0, 0.006), 'leather', bevel=0.003)
    b = L.box(name + '_b', (0.05, 0.05, 0.002), (0.022, 0.0, 0.013), 'brass', bevel=0.001)
    card = L.box(name + '_c', (0.045, 0.06, 0.001), (-0.025, 0, 0.0125), 'paper')
    return L.join([w, b, card], name)


def journal(name):
    cover = L.box(name + '_c', (0.24, 0.17, 0.04), (0, 0, 0.02), 'leather_dark', bevel=0.005)
    pages = L.box(name + '_p', (0.232, 0.162, 0.032), (0.003, 0, 0.02), 'paper')
    strap = L.box(name + '_s', (0.012, 0.172, 0.043), (0.07, 0, 0.02), 'leather', bevel=0.002)
    return L.join([cover, pages, strap], name)


def emf(name):
    b = L.box(name + '_b', (0.11, 0.08, 0.03), (0, 0, 0.015), 'plastic_black', bevel=0.004)
    parts = [b]
    for i in range(5):
        parts.append(L.box(name + f'_led{i}', (0.008, 0.008, 0.004), (-0.03 + 0.015 * i, -0.025, 0.031),
                           'led_red' if i > 2 else 'led_green'))
    parts.append(rod(name + '_ant', (0.05, 0.03, 0.03), (0.2, 0.03, 0.03), 0.0025, 'steel', 6))
    parts.append(L.box(name + '_ph', (0.03, 0.02, 0.01), (-0.035, 0.02, 0.031), 'steel'))
    return L.join(parts, name)


def lighter_fluid(name):
    b = L.box(name + '_b', (0.075, 0.035, 0.16), (0, 0, 0.08), 'zippo_blue', bevel=0.006)
    n = L.cylinder(name + '_n', 0.006, 0.03, (0.02, 0, 0.175), axis='Z', segments=8, mat='red_plastic')
    return L.join([b, n], name)


def crowbar(name):
    pts = [Vector((-0.4, 0, 0)), Vector((0.32, 0, 0)), Vector((0.37, 0, 0.02)), Vector((0.38, 0, 0.05))]
    return L.sweep(name, L.catmull(pts, 5), L.rounded_rect(0.02, 0.014, 0.004, 2), 'iron',
                   fixed_side=Vector((0, 1, 0)))


def rope(name, r=0.09, turns=6):
    parts = []
    for k in range(turns):
        rr = r - k * 0.006
        parts.append(L.lathe(name + f'_{k}', [(-0.008 + k * 0.001, rr - 0.007), (0.008, rr - 0.007),
                                               (0.008, rr + 0.007), (-0.008, rr + 0.007)],
                             segments=24, mat='twine', axis='Z', center=(0, 0, 0.012 + k * 0.004), close=True))
    return L.join(parts, name)


def chain(name, links=12):
    parts = []
    for i in range(links):
        lk = L.lathe(name + f'_{i}', [(-0.003, 0.012), (-0.003, 0.018), (0.003, 0.018), (0.003, 0.012)],
                     segments=10, mat='iron', axis='Y' if i % 2 else 'X', center=(i * 0.026, 0, 0.018), close=True)
        lk.data.transform(Matrix.Diagonal((1.4, 1, 1, 1)))
        parts.append(lk)
    o = L.join(parts, name)
    o.data.transform(Matrix.Translation((-links * 0.013, 0, 0)))
    return o


def duct_tape(name):
    return L.lathe(name, [(0, 0.03), (0, 0.055), (0.048, 0.055), (0.048, 0.03)], segments=24, mat='tape',
                   axis='Z', close=True)


def hex_bag(name):
    o = L.lathe(name, [(0, 0.0), (0.005, 0.03), (0.04, 0.034), (0.06, 0.02), (0.07, 0.008), (0.09, 0.012),
                       (0.095, 0.0)], segments=12, mat='burlap', axis='Z')
    return o


def ruby_knife(name):
    parts = [blade(name + '_b', 0.2, 0.034, 0.004, 'steel', tip=0.35, curve=0.15)]
    h = L.box(name + '_h', (0.11, 0.02, 0.026), (-0.055, 0, 0), 'wood_dark', bevel=0.006)
    parts.append(h)
    for k in range(4):
        parts.append(L.box(name + f'_r{k}', (0.004, 0.022, 0.028), (-0.015 - 0.025 * k, 0, 0), 'brass'))
    parts.append(L.box(name + '_g', (0.008, 0.024, 0.05), (0, 0, 0), 'brass', bevel=0.002))
    return L.join(parts, name)


def angel_blade(name):
    """Triangular-section silver blade on a short grip."""
    parts = []
    parts.append(L.lathe(name + '_b', [(0.0, 0.012), (0.3, 0.0)], segments=3, mat='silver', axis='X'))
    parts.append(L.lathe(name + '_h', [(-0.1, 0.0), (-0.1, 0.012), (0.0, 0.012), (0.0, 0.0)], segments=8,
                         mat='silver', axis='X'))
    return L.join(parts, name)


def sheath_knife(name):
    """Bowie knife in a leather sheath, like on the pegboard."""
    sh = L.extrude_outline(name + '_sh', [(0, -0.03), (0.2, -0.028), (0.26, 0.0), (0.2, 0.028), (0, 0.03)],
                           0.012, 'leather', bevel_w=0.004)
    k = knife(name + '_k', 0.33, 0.6, 0.04, 'antler')
    k.data.transform(Matrix.Translation((0.02, 0, 0.016)))
    return L.join([sh, k], name)


def holster(name):
    h = L.extrude_outline(name + '_h', [(0, -0.05), (0.16, -0.04), (0.2, 0.0), (0.16, 0.045), (0.0, 0.06),
                                        (-0.03, 0.02)], 0.03, 'leather', bevel_w=0.008)
    return h


def pouch(name, size=(0.14, 0.11, 0.05)):
    b = L.box(name + '_b', size, (0, 0, size[2] / 2), 'canvas_olive', bevel=0.012)
    f = L.box(name + '_f', (size[0] * 0.5, size[1] * 1.02, size[2] * 0.3), (size[0] * 0.25, 0, size[2] * 0.9),
              'canvas_olive', bevel=0.006)
    return L.join([b, f], name)


def rosary(name, n=30, r=0.07):
    parts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        parts.append(L.cylinder(name + f'_{i}', 0.004, 0.006, (r * math.cos(a) * 0.5, r * math.sin(a), 0.004),
                                axis='Z', segments=6, mat='bead_blue'))
    parts.append(cross(name + '_x', 0.05, 0.03, 0.004, 'silver'))
    parts[-1].data.transform(Matrix.Translation((-0.06, 0, 0.004)))
    return L.join(parts, name)


def flare(name):
    o = L.cylinder(name, 0.014, 0.22, (0, 0, 0), axis='X', segments=10, mat='red_plastic')
    return o


def lockpicks(name):
    case = L.box(name + '_c', (0.12, 0.05, 0.012), (0, 0, 0.006), 'leather_dark', bevel=0.003)
    parts = [case]
    for i in range(5):
        parts.append(L.box(name + f'_p{i}', (0.1, 0.003, 0.002), (0.005, -0.018 + 0.009 * i, 0.013), 'steel'))
    return L.join(parts, name)
