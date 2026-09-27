"""Small procedural props for the trunk arsenal and the cabin.

Every builder creates its geometry around the origin, lying along +X
(length), with +Z up, and returns one joined object. Placement happens in
trunk.py / interior.py.
"""
import math
import random
import bmesh
from mathutils import Vector, Matrix
import lib as L
import phprops as PH


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


def _tex(o, kind, metal=0.0):
    """Give a finished part its scanned material and a world-scale UV map now
    (grain along the part's length, +X), so later joins keep it."""
    o.data.materials.clear()
    o.data.materials.append(PH.tex_material(kind, metal))
    PH.uv_unwrap(o)
    return o


def stake(name, length=0.3, seed=1):
    """A whittled stake: a rough seven-sided shaft cut down to a faceted
    point, the butt end knocked round, a slight bend in the wood."""
    rnd = random.Random(seed)
    sides = 7
    jitter = [1 + rnd.uniform(-0.12, 0.12) for _ in range(sides)]
    cuts = [1 + rnd.uniform(-0.3, 0.3) for _ in range(sides)]
    rows = []
    stations = [0.0, 0.004, 0.012] + [length * t for t in (0.08, 0.2, 0.35, 0.5, 0.6, 0.66, 0.72, 0.78, 0.84, 0.9, 0.95, 0.985, 1.0)]
    r0 = 0.0155
    for x in stations:
        t = x / length
        if x < 0.012:
            r = r0 * (0.8 + 0.2 * x / 0.012)
        elif t < 0.62:
            r = r0 * (1 - 0.08 * t)
        else:
            k = (t - 0.62) / 0.38
            r = r0 * 0.95 * max(0.04, (1 - k) ** 1.15)
        bend = 0.004 * math.sin(math.pi * t)
        ring = []
        for i in range(sides):
            a = 2 * math.pi * (i + 0.3) / sides
            f = jitter[i] * (cuts[i] if t > 0.62 else 1.0) if t < 0.995 else 1.0
            rr = r * min(f, 1.25)
            ring.append(Vector((x, rr * math.cos(a) + bend, rr * math.sin(a))))
        rows.append(ring)
    verts = [v for ring in rows for v in ring]
    faces = L.grid_faces(len(rows), sides, close_cols=True)
    faces.append(tuple(reversed(range(sides))))
    base = (len(rows) - 1) * sides
    faces.append(tuple(base + i for i in range(sides)))
    o = L.mesh_object(name, verts, faces, None, smooth=False)
    o.data.transform(Matrix.Translation((-length / 2, 0, 0)))
    return _tex(o, 'stake_wood')


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


def _slat(name, length, t, d, seed):
    """A sawn slat along +X with rough, slightly skewed ends."""
    rnd = random.Random(seed)
    o = L.box(name, (length, t, d), (0, 0, 0), None, bevel=0.0015)
    for v in o.data.vertices:
        if abs(v.co.x) > length / 2 - 0.004:
            v.co.x += rnd.uniform(-0.003, 0.003) + (v.co.y / t) * 0.004
    return o


def cross(name, h=0.36, w=0.2, t=0.026, d=0.016):
    """Two weathered slats lashed together with twine, the long one on the
    board, the arms on top of it (top towards +X)."""
    a = _tex(_slat(name + '_v', h, t, d, 3), 'cross_wood')
    a.data.transform(Matrix.Translation((0, 0, d / 2)))
    b = _tex(_slat(name + '_h', w, t, d, 5), 'cross_wood')
    b.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Z'))
    xa = h * 0.2
    b.data.transform(Matrix.Translation((xa, 0, d * 1.5)))
    parts = [a, b]
    # diagonal lashing: loops round the joint in both diagonals
    for k, diag in enumerate((Vector((1, 1, 0)).normalized(), Vector((1, -1, 0)).normalized())):
        for j in range(3):
            off = (j - 1) * 0.0035
            side = Vector((-diag.y, diag.x, 0))
            hw = t * 0.78
            z0, z1 = -0.0006, 2 * d + 0.0008
            c = Vector((xa, 0, 0)) + side * off
            ring = [c + diag * hw + Vector((0, 0, z0)), c + diag * hw + Vector((0, 0, z1)),
                    c - diag * hw + Vector((0, 0, z1)), c - diag * hw + Vector((0, 0, z0))]
            path = L.catmull(ring, 4, closed=True)
            path.append(path[0])
            lp = L.sweep(name + f'_tw{k}{j}', path, _circle(0.0011, 5), None, closed_profile=True, cap=False)
            parts.append(_tex(lp, 'twine'))
    o = L.join(parts, name)
    return o


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
    """Brass knuckles lying flat: four finger rings over a curved palm bar,
    cut from one plate (rings towards +Y)."""
    xs = [-0.0375 + 0.025 * i for i in range(4)]
    top = []
    for x in xs:
        for k in range(7):
            a = math.pi * (1 - k / 6)
            top.append((x + 0.0142 * math.cos(a), 0.012 + 0.0142 * math.sin(a) * 0.95))
    outline = top + [(0.052, 0.0), (0.05, -0.016), (0.03, -0.029), (0.0, -0.033), (-0.03, -0.029), (-0.05, -0.016),
                     (-0.052, 0.0)]
    plate = L.extrude_outline(name, outline, 0.0085, 'brass', bevel_w=0.0, smooth=False)
    for x in xs:
        cut = L.cylinder(name + '_c', 0.0098, 0.03, (x, 0.012, 0.004), axis='Z', segments=20)
        L.boolean(plate, cut)
    # the open slot between the rings and the palm bar
    slot = L.box(name + '_s', (0.074, 0.0105, 0.03), (0, -0.0142, 0.004), None, bevel=0.005, segments=3)
    L.boolean(plate, slot)
    L.bevel(plate, 0.0016, segments=2, angle=40)
    plate.data.shade_smooth()
    L.auto_smooth(plate, 40)
    plate.data.transform(Matrix.Translation((0, 0.004, 0)))
    return plate


def _feather(name, top, length, seed):
    """A hanging feather in the XZ plane: a long vane, ragged where the barbs
    split, pale at the quill end and banded dark towards the tip."""
    rnd = random.Random(seed)
    w = length * 0.11
    split = 0.62

    def half(t):
        return w * max(0.0, 1 - ((t - 0.6) / 0.62) ** 2) ** 0.5

    def vane(t0, t1, mat, n):
        right, left = [], []
        for i in range(n + 1):
            t = t0 + (t1 - t0) * i / n
            rag = 0.8 if i % 2 else 1.0
            right.append((half(t) * rag * (1 + rnd.uniform(-0.06, 0.06)), -length * t))
            left.append((-half(t) * 0.9 * (1.0 if i % 2 else 0.84), -length * t))
        if t1 >= 1.0:
            right[-1] = (0.0, -length * 1.02)
            left = left[:-1]
        if t0 <= 0.0:
            left = left[1:]
        o = L.extrude_outline(name + mat, right + list(reversed(left)), 0.0008, mat)
        o.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
        o.data.transform(Matrix.Translation(top))
        return o

    parts = [vane(0.0, split, 'feather', 8), vane(split - 0.004, 1.0, 'feather_dark', 6)]
    parts.append(rod(name + '_q', (top[0], top[1] + 0.0006, top[2] + 0.008), (top[0], top[1] + 0.0006, top[2] - length * 0.92),
                     0.0007, 'ivory', 4, taper=0.4))
    return parts


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
        parts.append(rod(name + f'_s{k}', (dx, 0, -r), (dx * 1.2, 0, -r - 0.05), 0.0012, 'leather', 4))
        parts += _feather(name + f'_fe{k}', (dx * 1.2, 0, -r - 0.048), 0.085 - 0.008 * abs(k - 1), k)
    o = L.join(parts, name)
    # lie flat in the XY plane (faces +Z like everything else mounted on the board)
    o.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'X'))
    return o


def pump_shotgun(name, length=0.98):
    parts = []
    parts.append(rod(name + '_bar', (0.0, 0, 0.012), (length * 0.55, 0, 0.012), 0.011, 'gunmetal', 12))
    parts.append(rod(name + '_mag', (0.0, 0, -0.012), (length * 0.48, 0, -0.012), 0.010, 'gunmetal', 12))
    parts.append(L.box(name + '_pump', (0.2, 0.034, 0.03), (length * 0.3, 0, -0.012), 'wood_dark', bevel=0.006))
    parts.append(L.box(name + '_recv', (0.2, 0.034, 0.06), (-0.08, 0, 0.0), 'gunmetal', bevel=0.004))
    stock = L.extrude_outline(name + '_st', [(-0.17, 0.02), (-0.17, -0.03), (-0.26, -0.05), (-0.45, -0.1),
                                             (-0.46, 0.03), (-0.2, 0.03)], 0.036, 'wood_dark', bevel_w=0.008)
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
    parts.append(L.box(name + '_fe', (0.16, 0.034, 0.024), (0.1, 0, -0.018), 'wood_dark', bevel=0.005))
    parts.append(L.box(name + '_rc', (0.12, 0.04, 0.05), (-0.06, 0, -0.006), 'gunmetal', bevel=0.004))
    grip = L.extrude_outline(name + '_gr', [(-0.11, 0.02), (-0.12, -0.02), (-0.24, -0.08), (-0.28, -0.05),
                                            (-0.16, 0.02)], 0.034, 'wood_dark', bevel_w=0.006)
    grip.data.transform(Matrix.Translation((0, 0, -0.017)))
    grip.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    parts.append(grip)
    return L.join(parts, name)


def colt(name):
    """The Colt: a Paterson-style revolver like the show's prop: long dark
    octagonal barrel, engraved nickel frame, dark cylinder, bone grip."""
    parts = []
    # octagonal barrel with two bands at the muzzle
    bar = L.lathe(name + '_barrel', [(0.0, 0.0), (0.0, 0.0115), (0.215, 0.0105), (0.215, 0.0)], segments=8,
                  mat='gunmetal', axis='X', center=(0.045, 0, 0.014))
    parts.append(bar)
    for k, x in enumerate((0.236, 0.247)):
        parts.append(L.cylinder(name + f'_band{k}', 0.0118, 0.004, (x, 0, 0.014), axis='X', segments=16, mat='nickel'))
    parts.append(L.box(name + '_sight', (0.006, 0.002, 0.005), (0.252, 0, 0.0265), 'nickel'))
    # engraved barrel lug joining barrel and frame
    lug = L.extrude_outline(name + '_lug', [(0.03, -0.006), (0.085, -0.006), (0.085, 0.026), (0.045, 0.026),
                                            (0.03, 0.02)], 0.02, 'nickel', bevel_w=0.002)
    lug.data.transform(Matrix.Translation((0, 0, -0.01)))
    lug.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    parts.append(lug)
    # smooth dark cylinder with chamber mouths
    parts.append(L.cylinder(name + '_cyl', 0.0195, 0.046, (0.004, 0, 0.006), axis='X', segments=24, mat='gunmetal',
                            bevel=0.002))
    for i in range(5):
        a = 2 * math.pi * i / 5
        parts.append(L.cylinder(name + f'_ch{i}', 0.0045, 0.002, (0.0275, 0.0115 * math.cos(a), 0.006 + 0.0115 * math.sin(a)),
                                axis='X', segments=8, mat='black'))
    # nickel frame: recoil shield and the sloping top strap back to the hammer
    frame = L.extrude_outline(name + '_frame', [(-0.02, -0.018), (-0.022, 0.018), (-0.045, 0.03), (-0.06, 0.026),
                                                (-0.05, 0.004), (-0.035, -0.02)], 0.022, 'nickel', bevel_w=0.003)
    frame.data.transform(Matrix.Translation((0, 0, -0.011)))
    frame.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    parts.append(frame)
    parts.append(L.cylinder(name + '_shield', 0.021, 0.006, (-0.021, 0, 0.006), axis='X', segments=24, mat='nickel',
                            bevel=0.001))
    # hammer spur
    ham = L.extrude_outline(name + '_hammer', [(-0.045, 0.02), (-0.052, 0.036), (-0.066, 0.045), (-0.064, 0.038),
                                               (-0.055, 0.03), (-0.05, 0.016)], 0.007, 'gunmetal', bevel_w=0.001)
    ham.data.transform(Matrix.Translation((0, 0, -0.0035)))
    ham.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    parts.append(ham)
    # folding trigger (the Paterson hides it in the frame)
    parts.append(L.box(name + '_trig', (0.004, 0.004, 0.012), (-0.03, 0, -0.022), 'nickel'))
    # curved bone grip
    grip = L.extrude_outline(name + '_grip', [(-0.035, -0.012), (-0.06, -0.012), (-0.085, -0.05), (-0.098, -0.095),
                                              (-0.09, -0.112), (-0.066, -0.112), (-0.058, -0.09), (-0.05, -0.05),
                                              (-0.032, -0.022)], 0.026, 'ivory', bevel_w=0.006)
    grip.data.transform(Matrix.Translation((0, 0, -0.013)))
    grip.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    parts.append(grip)
    parts.append(L.box(name + '_butt', (0.034, 0.028, 0.006), (-0.078, 0, -0.114), 'nickel', bevel=0.002))
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


def hanging_chain(name, links=13, span=0.23, pitch=0.022):
    """A chain hanging in a curve between two pegs (end links at x = +-span/2),
    links alternating flat on the board and up on edge."""
    arc = (links - 1) * pitch
    sag = math.sqrt(max(3 * span * (arc - span) / 8, 1e-6))
    xs = [(-0.5 + i / 400) * span for i in range(401)]
    ys = [sag * (4 * (x / span) ** 2 - 1) for x in xs]
    acc = [0.0]
    for i in range(1, len(xs)):
        acc.append(acc[-1] + math.hypot(xs[i] - xs[i - 1], ys[i] - ys[i - 1]))
    wire, hl, hw = 0.0028, 0.011, 0.006
    ring = []
    for k in range(16):
        a = 2 * math.pi * k / 16
        cx = (hl - hw) * (1 if math.cos(a) >= 0 else -1)
        ring.append(Vector((cx + hw * math.cos(a), hw * math.sin(a), 0)))
    ring.append(ring[0])
    parts = []
    for i in range(links):
        s_i = acc[-1] * i / (links - 1)
        j = min(range(len(acc)), key=lambda q: abs(acc[q] - s_i))
        j2 = min(j + 1, len(xs) - 1)
        j1 = max(j2 - 1, 0)
        ang = math.atan2(ys[j2] - ys[j1], xs[j2] - xs[j1])
        lk = L.sweep(name + f'_{i}', ring, _circle(wire, 6), 'iron', cap=False)
        if i % 2:
            lk.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
            lk.data.transform(Matrix.Translation((0, 0, hw + wire)))
        else:
            lk.data.transform(Matrix.Translation((0, 0, wire)))
        lk.data.transform(Matrix.Translation((xs[j], ys[j], 0)) @ Matrix.Rotation(ang, 4, 'Z'))
        parts.append(lk)
    return L.join(parts, name)


def duct_tape(name):
    return L.lathe(name, [(0, 0.03), (0, 0.055), (0.048, 0.055), (0.048, 0.03)], segments=24, mat='tape',
                   axis='Z', close=True)


def hex_bag(name):
    """A hex bag: a small, lumpy cloth pouch lying flat (neck towards +X),
    cinched with twine, the gathered cloth fanned out above the tie."""
    rnd = random.Random(9)
    body = L.box(name, (0.056, 0.05, 0.026), (0, 0, 0.013), None, bevel=0.012, segments=4)
    for v in body.data.vertices:
        t = min(max((v.co.x + 0.028) / 0.056, 0.0), 1.0)
        k = 1 - 0.7 * max(0.0, t - 0.45) / 0.55
        v.co.y = v.co.y * k * (1 + rnd.uniform(-0.05, 0.05))
        v.co.z = 0.013 + (v.co.z - 0.013) * (0.6 + 0.4 * k) + rnd.uniform(-0.0012, 0.0012)
    _tex(body, 'canvas_olive')
    ruffle = L.lathe(name + '_r', [(0.0, 0.0072), (0.004, 0.009), (0.01, 0.0135), (0.015, 0.0165), (0.0165, 0.0)],
                     segments=12, axis='X', center=(0.03, 0, 0.013))
    for v in ruffle.data.vertices:
        v.co.z = 0.013 + (v.co.z - 0.013) * 0.55
        v.co.y *= 1 + rnd.uniform(-0.12, 0.12)
    _tex(ruffle, 'canvas_olive')
    tie = L.lathe(name + '_tie', [(-0.0018, 0.0068), (0.0018, 0.0068), (0.0018, 0.0086), (-0.0018, 0.0086)], segments=14,
                  axis='X', center=(0.0305, 0, 0.013), close=True)
    tie.data.transform(Matrix.Translation((0, 0, 0)) @ Matrix.Diagonal((1, 1, 0.75, 1)))
    _tex(tie, 'twine')
    o = L.join([body, ruffle, tie], name)
    o.data.transform(Matrix.Translation((-0.008, 0, 0)))
    return o


def ruby_knife(name):
    parts = [blade(name + '_b', 0.2, 0.034, 0.004, 'steel', tip=0.35, curve=0.15)]
    h = L.box(name + '_h', (0.11, 0.02, 0.026), (-0.055, 0, 0), 'wood_dark', bevel=0.006)
    parts.append(h)
    for k in range(4):
        parts.append(L.box(name + f'_r{k}', (0.004, 0.022, 0.028), (-0.015 - 0.025 * k, 0, 0), 'brass'))
    parts.append(L.box(name + '_g', (0.008, 0.024, 0.05), (0, 0, 0), 'brass', bevel=0.002))
    return L.join(parts, name)


def _flat_blade(name, pts, thick, mat):
    """A blade lying flat: outline in XY (x along the blade, y across it),
    thickness centred on Z, with softened edges."""
    b = L.extrude_outline(name, pts, thick, mat, bevel_w=thick * 0.38)
    b.data.transform(Matrix.Translation((0, 0, -thick / 2)))
    return b


def angel_blade(name):
    """Angel blade: a long, slender three-sided silver blade (one face on the
    board, a ridge towards the viewer) on a grooved silver grip."""
    L_b = 0.285
    rows = []
    stations = [0.0, 0.03, 0.12, 0.2, 0.24, 0.265, 0.28, L_b]
    for x in stations:
        t = x / L_b
        s = 0.0135 * (1 - 0.25 * t) if t < 0.84 else 0.0135 * 0.79 * max(0.02, (1 - t) / 0.16)
        rows.append([Vector((x, -s / 2, 0.0)), Vector((x, s / 2, 0.0)), Vector((x, 0.0, s * 0.72))])
    verts = [v for r in rows for v in r]
    faces = L.grid_faces(len(rows), 3, close_cols=True)
    faces.append((2, 1, 0))
    base = (len(rows) - 1) * 3
    faces.append((base, base + 1, base + 2))
    bl = L.mesh_object(name + '_b', verts, faces, None, smooth=False)
    L.weld(bl, 1e-5)
    _tex(bl, 'silver', 1.0)
    grip = L.lathe(name + '_h', [(-0.108, 0.0), (-0.108, 0.0082), (-0.1, 0.0092), (0.0, 0.0088), (0.0, 0.0)], segments=14,
                   axis='X', center=(0, 0, 0.0092))
    rings = [grip]
    for k in range(7):
        x = -0.012 - 0.013 * k
        rings.append(L.cylinder(name + f'_r{k}', 0.0099, 0.0032, (x, 0, 0.0092), axis='X', segments=14))
    rings.append(L.cylinder(name + '_col', 0.0112, 0.006, (0.002, 0, 0.0092), axis='X', segments=14, bevel=0.001))
    g = _tex(L.join(rings, name + '_g'), 'silver', 1.0)
    o = L.join([bl, g], name)
    o.data.transform(Matrix.Translation((-0.09, 0, 0)))
    return o


def bowie(name):
    """A proper Bowie: a wide, flat blade with a clip point and a straight
    spine, brass crossguard, stag handle and brass pommel."""
    pts = [(0.0, -0.021), (0.07, -0.0235), (0.13, -0.0232), (0.168, -0.0188), (0.196, -0.0098), (0.215, 0.0),
           (0.197, 0.0072), (0.174, 0.0122), (0.152, 0.0205), (0.14, 0.0215), (0.0, 0.0215)]
    parts = [_flat_blade(name + '_b', pts, 0.0052, 'steel')]
    parts.append(L.box(name + '_g', (0.009, 0.084, 0.013), (-0.0045, 0, 0), 'brass', bevel=0.003))
    grip = L.extrude_outline(name + '_h', [(-0.009, -0.0135), (-0.06, -0.0158), (-0.108, -0.0145), (-0.126, -0.011),
                                            (-0.126, 0.0125), (-0.108, 0.0152), (-0.06, 0.0165), (-0.009, 0.014)],
                             0.02, 'antler', bevel_w=0.006)
    grip.data.transform(Matrix.Translation((0, 0, -0.01)))
    parts.append(grip)
    parts.append(L.box(name + '_p', (0.011, 0.031, 0.022), (-0.131, 0, 0), 'brass', bevel=0.004))
    o = L.join(parts, name)
    o.data.transform(Matrix.Translation((-0.04, 0, 0)))
    return o


def ruby_knife(name):
    """Ruby's knife, after the show's prop: a broad blade with a gently
    upswept tip, a small iron guard and a dark grip bound with iron rings."""
    pts = [(0.0, -0.0152), (0.06, -0.0188), (0.11, -0.0208), (0.15, -0.0192), (0.178, -0.0122), (0.196, 0.0022),
           (0.19, 0.0082), (0.16, 0.0106), (0.1, 0.0136), (0.04, 0.0146), (0.0, 0.0152)]
    parts = [_flat_blade(name + '_b', pts, 0.0046, 'steel')]
    parts.append(L.box(name + '_g', (0.008, 0.048, 0.013), (-0.004, 0, 0), 'iron', bevel=0.003))
    grip = L.extrude_outline(name + '_h', [(-0.008, -0.012), (-0.05, -0.0138), (-0.094, -0.0122), (-0.106, -0.009),
                                            (-0.106, 0.009), (-0.094, 0.0122), (-0.05, 0.0138), (-0.008, 0.012)],
                             0.02, 'wood_dark', bevel_w=0.006)
    grip.data.transform(Matrix.Translation((0, 0, -0.01)))
    parts.append(grip)
    for k, x in enumerate((-0.03, -0.058, -0.084)):
        parts.append(L.box(name + f'_r{k}', (0.004, 0.03, 0.022), (x, 0, 0), 'iron', bevel=0.0015))
    parts.append(L.box(name + '_p', (0.012, 0.025, 0.021), (-0.11, 0, 0), 'iron', bevel=0.005))
    o = L.join(parts, name)
    o.data.transform(Matrix.Translation((-0.045, 0, 0)))
    return o


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


def _bead(name, p, r, segs=8):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs // 2 + 1, radius=r)
    bmesh.ops.translate(bm, vec=Vector(p), verts=bm.verts)
    me = bpy_mesh(name, bm)
    return me


def bpy_mesh(name, bm):
    import bpy
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    L.link(o)
    o.data.shade_smooth()
    return o


def rosary(name, n=44):
    """A rosary lying in a loop (top towards +X) with a short tail of beads
    down to a small metal crucifix."""
    parts = []
    rb = 0.0036
    # loop: a rounded teardrop, widest near the top
    loop = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x = 0.034 * math.cos(a) + 0.006 * math.cos(2 * a)
        y = 0.03 * math.sin(a) * (0.75 + 0.25 * math.cos(a))
        loop.append((x + 0.02, y))
    for i, (x, y) in enumerate(loop):
        parts.append(_bead(name + f'_{i}', (x, y, rb), rb))
    # the centre medal and the tail
    parts.append(L.cylinder(name + '_m', 0.0058, 0.0022, (-0.02, 0, 0.0011), axis='Z', segments=12))
    for k in range(5):
        parts.append(_bead(name + f'_t{k}', (-0.03 - 0.0085 * k, 0, rb), rb))
    beads = L.join(parts, name + '_b')
    _tex(beads, 'walnut')
    xa = -0.083
    c1 = L.box(name + '_x1', (0.034, 0.0045, 0.003), (xa - 0.012, 0, 0.0015), None, bevel=0.0006)
    c2 = L.box(name + '_x2', (0.0045, 0.022, 0.003), (xa - 0.004, 0, 0.0015), None, bevel=0.0006)
    cx = _tex(L.join([c1, c2], name + '_x'), 'silver', 1.0)
    o = L.join([beads, cx], name)
    o.data.transform(Matrix.Translation((0.025, 0, 0)))
    return o


def flare(name, pair=True):
    """Road flares: red waxed-paper tubes with a black striker cap and a
    printed band, two strapped side by side."""
    parts = []
    for k, dy in enumerate((-0.0145, 0.0145) if pair else (0.0,)):
        tube = _tex(L.cylinder(name + f'_t{k}', 0.0132, 0.19, (0.0, dy, 0.0132), axis='X', segments=16), 'shell')
        cap = L.cylinder(name + f'_c{k}', 0.0148, 0.048, (0.107, dy, 0.0132), axis='X', segments=16, mat='plastic_black',
                         bevel=0.002)
        band = L.cylinder(name + f'_b{k}', 0.01345, 0.055, (-0.02, dy, 0.0132), axis='X', segments=16, mat='paper')
        parts += [tube, cap, band]
    return L.join(parts, name)


def lockpicks(name):
    case = L.box(name + '_c', (0.12, 0.05, 0.012), (0, 0, 0.006), 'leather_dark', bevel=0.003)
    parts = [case]
    for i in range(5):
        parts.append(L.box(name + f'_p{i}', (0.1, 0.003, 0.002), (0.005, -0.018 + 0.009 * i, 0.013), 'steel'))
    return L.join(parts, name)
