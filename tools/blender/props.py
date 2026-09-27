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
    """A pump shotgun (870 pattern), lying on its side: profile in XY, muzzle
    +X. Blued barrel over a magazine tube, a ribbed walnut forend, a receiver
    with its ejection port, a guard and trigger, a walnut stock with a
    slimmer wrist and a rubber pad."""
    B, W = 'blued', 'walnut'
    parts = []
    bar = L.lathe(name + '_bar', [(0.0, 0.0), (0.0, 0.0108), (0.51, 0.0098), (0.51, 0.0)], segments=18, axis='X', center=(0.17, 0.013, 0))
    parts.append(_tex(bar, B, 1.0))
    parts.append(_tex(L.cylinder(name + '_bead', 0.0016, 0.003, (0.674, 0.0232, 0), axis='Y', segments=8), 'brass', 1.0))
    mag = L.lathe(name + '_mag', [(0.0, 0.0), (0.0, 0.0094), (0.37, 0.0094), (0.378, 0.0085), (0.382, 0.0)], segments=16, axis='X',
                  center=(0.17, -0.0085, 0))
    parts.append(_tex(mag, B, 1.0))
    parts.append(_tex(L.box(name + '_band', (0.012, 0.036, 0.021), (0.53, 0.002, 0), None, bevel=0.003), B, 1.0))
    receiver = [(-0.03, 0.026), (0.17, 0.024), (0.17, -0.021), (0.12, -0.024), (0.02, -0.025), (-0.03, -0.02)][::-1]
    parts.append(_outline_part(name + '_rec', receiver, 0.03, B, 0.003))
    parts.append(L.box(name + '_port', (0.055, 0.016, 0.0012), (0.085, 0.009, 0.0152), 'black'))
    loop = L.catmull([Vector(p) for p in [(0.06, -0.024, 0), (0.058, -0.036, 0), (0.045, -0.05, 0), (0.02, -0.053, 0),
                                          (0.0, -0.047, 0), (-0.008, -0.035, 0), (-0.008, -0.022, 0)]], 5)
    parts.append(_tex(L.sweep(name + '_guard', loop, [(-0.006, -0.002), (0.006, -0.002), (0.006, 0.002), (-0.006, 0.002)], None,
                              fixed_side=Vector((0, 0, 1))), B, 1.0))
    parts.append(_outline_part(name + '_trig', [(0.022, -0.025), (0.026, -0.038), (0.022, -0.043), (0.017, -0.04), (0.017, -0.025)][::-1],
                               0.005, B, 0.0008))
    # forend: a ribbed wooden sleeve around the magazine tube
    prof = [(0.0, 0.0), (0.0, 0.0165)]
    for k in range(9):
        x = 0.012 + 0.019 * k
        prof += [(x, 0.0182), (x + 0.012, 0.0182), (x + 0.013, 0.0172), (x + 0.018, 0.0172)]
    prof += [(0.19, 0.0165), (0.19, 0.0)]
    fe = L.lathe(name + '_fore', prof, segments=18, axis='X', center=(0.24, -0.0085, 0))
    for v in fe.data.vertices:
        v.co.y = -0.0085 + (v.co.y + 0.0085) * 1.12
    parts.append(_tex(fe, W))
    # stock: the side profile, pinched at the wrist
    stock = [(-0.03, 0.022), (-0.075, 0.017), (-0.13, 0.014), (-0.3, 0.03), (-0.308, 0.026), (-0.308, -0.098), (-0.29, -0.104),
             (-0.13, -0.04), (-0.07, -0.038), (-0.045, -0.03), (-0.03, -0.02)][::-1]
    st = _outline_part(name + '_stock', stock, 0.04, W, 0.011, metal=0.0)
    for v in st.data.vertices:
        t = min(max((-v.co.x - 0.03) / 0.27, 0.0), 1.0)
        v.co.z *= 0.72 + 0.28 * t + 0.1 * math.exp(-((t - 0.0) / 0.12) ** 2)
    parts.append(st)
    pad = L.box(name + '_pad', (0.016, 0.132, 0.041), (-0.316, -0.034, 0), 'rubber', bevel=0.004)
    pad.data.transform(Matrix.Translation((0, 0, 0)))
    parts.append(pad)
    o = L.join(parts, name)
    o.data.transform(Matrix.Translation((-(0.68 - 0.324) / 2 + 0.0, 0, 0)))
    return o


def sawed_off(name):
    """Dean's sawed-off: a side-by-side double with the barrels cut short and
    the stock cut down to a pistol grip. Lying on its side (the barrels one
    over the other in Z), muzzle +X, blued steel and walnut."""
    B, W = 'blued', 'walnut'
    parts = []
    for zs in (1, -1):
        b = L.lathe(name + f'_b{zs}', [(0.0, 0.0), (0.0, 0.0108), (0.265, 0.0104), (0.265, 0.0)], segments=18, axis='X',
                    center=(0.07, 0.01, zs * 0.0106))
        parts.append(_tex(b, B, 1.0))
    parts.append(_tex(L.box(name + '_rib', (0.265, 0.004, 0.008), (0.2025, 0.0215, 0), None, bevel=0.001), B, 1.0))
    parts.append(_tex(L.box(name + '_rib2', (0.2, 0.004, 0.008), (0.17, -0.0015, 0), None, bevel=0.001), B, 1.0))
    fore = L.box(name + '_fore', (0.13, 0.02, 0.036), (0.14, -0.009, 0), None, bevel=0.007)
    parts.append(_tex(fore, W))
    action = [(0.0, 0.021), (0.072, 0.021), (0.072, -0.004), (0.045, -0.02), (0.0, -0.022), (-0.022, -0.012), (-0.022, 0.018)][::-1]
    parts.append(_outline_part(name + '_act', action, 0.042, B, 0.004))
    parts.append(_outline_part(name + '_lever', [(-0.004, 0.02), (-0.03, 0.025), (-0.034, 0.022), (-0.008, 0.017)][::-1], 0.012, B, 0.001))
    loop = L.catmull([Vector(p) for p in [(0.03, -0.021, 0), (0.028, -0.034, 0), (0.014, -0.045, 0), (-0.006, -0.045, 0),
                                          (-0.017, -0.034, 0), (-0.018, -0.02, 0)]], 5)
    parts.append(_tex(L.sweep(name + '_guard', loop, [(-0.006, -0.002), (0.006, -0.002), (0.006, 0.002), (-0.006, 0.002)], None,
                              fixed_side=Vector((0, 0, 1))), B, 1.0))
    for k, x in enumerate((0.013, 0.0)):
        parts.append(_outline_part(name + f'_trig{k}', [(x, -0.02), (x + 0.003, -0.032), (x, -0.036), (x - 0.004, -0.033), (x - 0.004, -0.02)][::-1],
                                   0.004, B, 0.0007))
    grip = [(-0.02, 0.017), (-0.06, 0.011), (-0.095, 0.0), (-0.125, -0.028), (-0.145, -0.07), (-0.126, -0.086), (-0.1, -0.062),
            (-0.075, -0.036), (-0.045, -0.026), (-0.022, -0.012)][::-1]
    parts.append(_outline_part(name + '_grip', grip, 0.036, W, 0.01, metal=0.0))
    return L.join(parts, name)


def _colt_spec():
    import json
    import os
    return json.load(open(os.path.join(os.path.dirname(__file__), 'blades.json')))['colt']


def _outline_part(name, pts, thick, kind, bevel=0.0015, metal=1.0):
    """A flat part of a gun's profile (XY), `thick` deep centred on Z."""
    o = L.extrude_outline(name, pts, thick, None, bevel_w=bevel)
    o.data.transform(Matrix.Translation((0, 0, -thick / 2)))
    return _tex(o, kind, metal)


def _helix(name, start, axis, r, pitch, turns, wire, mat):
    """A coil of wire wound along `axis` from `start`."""
    axis = Vector(axis).normalized()
    side = axis.orthogonal().normalized()
    up = axis.cross(side)
    n = int(turns * 12)
    pts = [Vector(start) + axis * (pitch * i / 12) + side * (r * math.cos(2 * math.pi * i / 12)) +
           up * (r * math.sin(2 * math.pi * i / 12)) for i in range(n + 1)]
    return L.sweep(name, pts, _circle(wire, 5), mat)


def colt(name):
    """The Colt, after the show's prop: a Paterson revolver in antiqued
    silver. A long octagonal barrel with three bands at the muzzle and "non
    timebo mala" along it, an engraved lug and frame, a banded cylinder, the
    hammer spur, the folding trigger, a walnut grip with a pentagram.
    Built with the muzzle towards +X and the profile in XY, then turned over
    (muzzle towards -X), so the side with the motto faces up (+Z)."""
    sp = _colt_spec()
    x0, x1, R = sp['barrel']
    ax = 0.012                              # barrel axis height
    parts = []
    # the barrel: an octagon, flats up, down and to the sides; the motto goes on
    # the -Z flat, mapped so it reads from the muzzle once the gun is turned over
    bar = L.lathe(name + '_bar', [(0.0, 0.0), (0.0, R), (x1 - x0, R), (x1 - x0, 0.0)], segments=8, axis='X', center=(x0, 0, 0))
    bar.data.transform(Matrix.Rotation(math.pi / 8, 4, 'X'))
    bar.data.transform(Matrix.Translation((0, ax, 0)))
    hw = R * math.sin(math.pi / 8)
    me = bar.data
    uv = me.uv_layers.active or me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        # the flat on the -Z side, found by where it is (lathe winding varies)
        motto = poly.center.z < -R * 0.85 and abs(poly.center.y - ax) < hw
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            u = (x1 - co.x) / (x1 - x0)
            v = 0.2 + 0.6 * (co.y - (ax - hw)) / (2 * hw) if motto else 0.05
            uv.data[li].uv = (u, v)
    me.materials.append(PH.tex_material('colt_barrel', 1.0))
    L.auto_smooth(bar, 30)
    parts.append(bar)
    for k, x in enumerate((x1 - 0.013, x1 - 0.0085, x1 - 0.004)):
        band = L.lathe(name + f'_band{k}', [(-0.0009, R), (-0.0009, R + 0.0007), (0.0009, R + 0.0007), (0.0009, R)],
                       segments=8, axis='X', center=(x, 0, 0), close=True)
        band.data.transform(Matrix.Rotation(math.pi / 8, 4, 'X'))
        band.data.transform(Matrix.Translation((0, ax, 0)))
        parts.append(_tex(band, 'colt_plain', 1.0))
    parts.append(_tex(L.box(name + '_sight', (0.006, 0.0035, 0.0016), (x1 - 0.005, ax + R * 0.92 + 0.0015, 0), None), 'colt_plain', 1.0))
    # the engraved lug under the barrel, with the wedge screw
    parts.append(_outline_part(name + '_lug', [(0.087, 0.003), (0.088, 0.0), (0.082, -0.006), (0.07, -0.012), (0.05, -0.015),
                                                (0.035, -0.012), (0.035, 0.003)][::-1], 0.017, 'colt_engraved'))
    for zz in (0.0085, -0.0085):
        parts.append(_tex(L.cylinder(name + '_pin', 0.0028, 0.0016, (0.062, -0.004, zz), axis='Z', segments=12, bevel=0.0004),
                          'colt_plain', 1.0))
    # the cylinder: two raised bands, chambers at the front
    cyl = L.lathe(name + '_cyl', [(-0.015, 0.0), (-0.015, 0.0175), (-0.013, 0.0195), (-0.0055, 0.0195), (-0.0055, 0.0207),
                                   (-0.0015, 0.0207), (-0.0015, 0.0195), (0.0195, 0.0195), (0.0195, 0.0207), (0.0235, 0.0207),
                                   (0.0235, 0.0195), (0.032, 0.0195), (0.034, 0.0178), (0.034, 0.0)], segments=28, axis='X',
                  center=(0, 0.006, 0))
    L.auto_smooth(cyl, 40)
    parts.append(_tex(cyl, 'colt_plain', 1.0))
    # recoil shield and frame, the hammer spur, the folding trigger
    shield = L.cylinder(name + '_shield', 0.0205, 0.006, (-0.018, 0.006, 0), axis='X', segments=28, bevel=0.0012)
    parts.append(_tex(shield, 'colt_engraved', 1.0))
    parts.append(_outline_part(name + '_frame', [(-0.017, 0.022), (-0.03, 0.026), (-0.041, 0.024), (-0.052, 0.018), (-0.06, 0.01),
                                                  (-0.058, 0.0), (-0.05, -0.012), (-0.042, -0.02), (-0.03, -0.022), (-0.017, -0.018)],
                               0.022, 'colt_engraved'))
    parts.append(_outline_part(name + '_hammer', [(-0.036, 0.024), (-0.04, 0.036), (-0.046, 0.046), (-0.054, 0.052), (-0.06, 0.052),
                                                   (-0.056, 0.046), (-0.05, 0.038), (-0.046, 0.024)], 0.007, 'colt_plain', 0.001))
    parts.append(_outline_part(name + '_trigger', [(-0.032, -0.021), (-0.029, -0.03), (-0.031, -0.038), (-0.035, -0.036), (-0.034, -0.029),
                                                    (-0.036, -0.021)][::-1], 0.004, 'colt_plain', 0.0008))
    # the walnut grip, its pentagram mapped from the grip's own plan
    g = [tuple(p) for p in sp['grip']]
    grip = L.extrude_outline(name + '_grip', g, 0.026, None, bevel_w=0.0065)
    grip.data.transform(Matrix.Translation((0, 0, -0.013)))
    gx = [p[0] for p in g]
    gy = [p[1] for p in g]
    me = grip.data
    uv = me.uv_layers.active or me.uv_layers.new(name='UVMap')
    for lp in me.loops:
        co = me.vertices[lp.vertex_index].co
        uv.data[lp.index].uv = ((co.x - min(gx)) / (max(gx) - min(gx)), (co.y - min(gy)) / (max(gy) - min(gy)))
    me.materials.append(PH.tex_material('colt_grip', 0.0))
    parts.append(grip)
    o = L.join(parts, name)
    o.data.transform(Matrix.Rotation(math.pi, 4, 'Y'))
    return o


def m1911(name):
    """Dean's gun: a nickel-plated Colt M1911A1, engraved all over, with ivory
    grips, gold medallions and polished screws (after the reference photo).
    Profile in XY with the muzzle towards +X, the controls on the +Z side.
    Sets obj['hang_du']: where a peg through the trigger guard goes, from the
    middle of its bounding box along X."""
    E, Pn = 'm1911_engraved', 'm1911_plain'
    sw, fw = 0.0235, 0.021                  # slide and frame widths
    parts = []
    slide = [(-0.084, 0.0), (0.127, 0.0), (0.128, 0.026), (0.1255, 0.0302), (-0.0805, 0.0302), (-0.084, 0.026)]
    parts.append(_outline_part(name + '_slide', slide, sw, E, 0.0016))
    # rear serrations on both sides, the sights
    for i in range(12):
        for zs in (1, -1):
            parts.append(_tex(L.box(name + '_ser', (0.0011, 0.023, 0.0007), (-0.0812 + 0.0024 * i, 0.0145, zs * (sw / 2 + 0.0002)), None),
                              Pn, 1.0))
    parts.append(_tex(L.box(name + '_fs', (0.0045, 0.0045, 0.003), (0.1195, 0.032, 0), None, bevel=0.0006), Pn, 1.0))
    parts.append(_tex(L.box(name + '_rs', (0.0065, 0.004, 0.012), (-0.075, 0.032, 0), None, bevel=0.0006), Pn, 1.0))
    # the frame: dust cover, grip frame raked back, the grip-safety tang
    frame = [(0.085, 0.0), (-0.084, 0.0), (-0.084, 0.001), (-0.096, 0.003), (-0.1, -0.002), (-0.086, -0.004), (-0.078, -0.012),
             (-0.075, -0.03), (-0.078, -0.06), (-0.084, -0.09), (-0.086, -0.108), (-0.058, -0.103), (-0.055, -0.095), (-0.045, -0.06),
             (-0.035, -0.03), (-0.028, -0.013), (0.036, -0.012), (0.06, -0.011), (0.082, -0.009), (0.085, -0.004)]
    parts.append(_outline_part(name + '_frame', frame[::-1], fw, E, 0.0014))
    # trigger guard: a swept loop hanging from the frame, and the trigger
    loop = L.catmull([Vector(p) for p in [(0.036, -0.011, 0), (0.037, -0.02, 0), (0.031, -0.031, 0), (0.016, -0.036, 0),
                                          (-0.004, -0.035, 0), (-0.017, -0.03, 0), (-0.024, -0.02, 0), (-0.026, -0.011, 0)]], 5)
    guard = L.sweep(name + '_guard', loop, [(-0.0055, -0.0018), (0.0055, -0.0018), (0.0055, 0.0018), (-0.0055, 0.0018)], None,
                    fixed_side=Vector((0, 0, 1)))
    parts.append(_tex(guard, E, 1.0))
    parts.append(_outline_part(name + '_trig', [(-0.006, -0.012), (-0.004, -0.024), (-0.006, -0.027), (-0.0105, -0.025),
                                                  (-0.011, -0.012)][::-1], 0.005, Pn, 0.0008))
    # hammer, thumb safety, slide stop, magazine catch (on the +Z side)
    parts.append(_outline_part(name + '_ham', [(-0.084, 0.019), (-0.086, 0.025), (-0.094, 0.029), (-0.0995, 0.026), (-0.095, 0.02),
                                                 (-0.09, 0.012), (-0.085, 0.01)][::-1], 0.008, Pn, 0.001))
    side = fw / 2 + 0.0014
    for nm, outline in (('_safety', [(-0.071, -0.003), (-0.056, 0.0005), (-0.058, 0.004), (-0.071, 0.002)]),
                        ('_stop', [(-0.022, -0.004), (0.014, -0.0005), (0.0125, 0.0035), (-0.022, 0.003)])):
        o = _outline_part(name + nm, outline, 0.0028, Pn, 0.0006)
        o.data.transform(Matrix.Translation((0, 0, side)))
        parts.append(o)
    catch = L.cylinder(name + '_catch', 0.0042, 0.0026, (-0.031, -0.019, fw / 2 + 0.0008), axis='Z', segments=16, bevel=0.0006)
    parts.append(_tex(catch, 'm1911_engraved', 1.0))
    # ivory grips with a gold medallion and two screws, both sides; the lanyard loop
    panel = [(-0.034, -0.016), (-0.044, -0.05), (-0.052, -0.08), (-0.056, -0.098), (-0.082, -0.1), (-0.08, -0.08), (-0.075, -0.05),
             (-0.072, -0.02), (-0.074, -0.014)][::-1]
    for zs in (1, -1):
        g = _outline_part(name + '_ivory', panel, 0.0048, 'ivory', 0.0018, metal=0.0)
        g.data.transform(Matrix.Translation((0, 0, zs * (fw / 2 + 0.0022))))
        parts.append(g)
        zf = zs * (fw / 2 + 0.0046)
        med = L.cylinder(name + '_med', 0.0056, 0.0012, (-0.058, -0.047, zf), axis='Z', segments=18, bevel=0.0003)
        # the rampant colt, the right way round from either side
        muv = med.data.uv_layers.active or med.data.uv_layers.new(name='UVMap')
        for lp in med.data.loops:
            co = med.data.vertices[lp.vertex_index].co
            muv.data[lp.index].uv = (0.5 + zs * (co.x + 0.058) / 0.0112, 0.5 + (co.y + 0.047) / 0.0112)
        med.data.materials.append(PH.tex_material('colt_medallion', 1.0))
        parts.append(med)
        for (sx, sy) in ((-0.051, -0.024), (-0.07, -0.091)):
            parts.append(_tex(L.cylinder(name + '_scr', 0.0031, 0.0014, (sx, sy, zf), axis='Z', segments=12, bevel=0.0005), Pn, 1.0))
    ring = L.lathe(name + '_lan', [(-0.0012, 0.0028), (0.0012, 0.0028), (0.0012, 0.0045), (-0.0012, 0.0045)], segments=14, axis='Y',
                   center=(-0.083, -0.112, 0), close=True)
    parts.append(_tex(ring, Pn, 1.0))
    o = L.join(parts, name)
    xs = [v.co.x for v in o.data.vertices]
    o['hang_du'] = 0.006 - (min(xs) + max(xs)) / 2
    return o


def colt_case(name):
    """The Colt's case, open: black-painted wood, a black insert with the gun
    lying in it, and the thirteen numbered rounds in a slotted rack below."""
    sp = _colt_spec()
    Lc, Wc, Hc, t = 0.40, 0.21, 0.05, 0.012
    walls = [L.box(name + '_bot', (Lc, Wc, 0.01), (0, 0, 0.005), None, bevel=0.003)]
    for sx in (-1, 1):
        walls.append(L.box(name + '_e', (t, Wc, Hc), (sx * (Lc - t) / 2, 0, Hc / 2), None, bevel=0.003))
    for sy in (-1, 1):
        walls.append(L.box(name + '_s', (Lc - 2 * t, t, Hc), (0, sy * (Wc - t) / 2, Hc / 2), None, bevel=0.003))
    box = _tex(L.join(walls, name + '_box'), 'black_wood')
    floor = 0.022
    insert = _tex(L.box(name + '_ins', (Lc - 2 * t, Wc - 2 * t, floor - 0.01), (0, 0, 0.01 + (floor - 0.01) / 2), None), 'felt_black')
    rack = _tex(L.box(name + '_rack', (0.258, 0.052, 0.006), (-0.05, -0.057, floor + 0.003), None, bevel=0.002), 'felt_black')
    parts = [box, insert, rack]
    # the rounds: tips towards the gun (+Y), each with its number on the side facing up
    rs = sp['round']
    rl, rr = rs['length'], rs['radius']
    prof = [(0.0, 0.0), (0.0, rr + 0.0004), (0.0018, rr + 0.0004), (0.0026, rr), (0.028, rr), (0.031, rr * 0.97),
            (0.035, rr * 0.84), (0.039, rr * 0.6), (0.0415, rr * 0.3), (rl, 0.0)]
    for i in range(13):
        cx, by, cz = -0.164 + 0.019 * i, -0.08, floor + 0.006 + rr - 0.0025
        rd = L.lathe(name + f'_r{i}', prof, segments=14, axis='Y', center=(cx, by, cz))
        me = rd.data
        uv = me.uv_layers.active or me.uv_layers.new(name='UVMap')
        for lp in me.loops:
            co = me.vertices[lp.vertex_index].co
            u = (i + min(max((co.y - by) / rl, 0.0), 1.0)) / 13
            v = min(max((rr - (co.x - cx)) / (2 * rr), 0.0), 1.0)
            uv.data[lp.index].uv = (u, v)
        me.materials.append(PH.tex_material('colt_rounds', 1.0))
        parts.append(rd)
    gun = colt(name + '_gun')
    vs = [v.co for v in gun.data.vertices]
    xmin, xmax = min(v.x for v in vs), max(v.x for v in vs)
    zmin = min(v.z for v in vs)
    gun.data.transform(Matrix.Translation((-(xmin + xmax) / 2, 0.028, floor + 0.0005 - zmin)))
    parts.append(gun)
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
    """The EMF meter from most of the show: a bare green perfboard with an
    analogue meter, five red LEDs along the top edge, a telescopic aerial
    down the left side wound with a red coil, a copper spring on the right,
    wires round the edge, trimmers, capacitors, resistors and a toggle.
    Lies flat: the board in XY, LEDs towards +Y."""
    W, H, T = 0.12, 0.105, 0.0016
    parts = []
    board = L.box(name + '_pcb', (W, H, T), (0, 0, T / 2), None)
    me = board.data
    uv = me.uv_layers.active or me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co.x + W / 2) / W, (co.y + H / 2) / H) if poly.normal.z > 0.5 else (0.01, 0.5)
    me.materials.append(PH.tex_material('emf_board', 0.0))
    parts.append(board)
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(L.cylinder(name + '_leg', 0.0022, 0.003, (sx * (W / 2 - 0.004), sy * (H / 2 - 0.004), -0.0015), axis='Z',
                                    segments=10, mat='nickel'))
    top = T
    # the meter: black body, the printed face, a brushed plate and a knob below it
    parts.append(L.box(name + '_meter', (0.074, 0.07, 0.011), (0.003, -0.003, top + 0.0055), 'plastic_black', bevel=0.002))
    fz = top + 0.0112
    face = L.mesh_object(name + '_face', [(-0.032, 0.0, fz), (0.038, 0.0, fz), (0.038, 0.03, fz), (-0.032, 0.03, fz)], [(0, 1, 2, 3)],
                         None, smooth=False)
    uvf = face.data.uv_layers.new(name='UVMap')
    for lp in face.data.loops:
        co = face.data.vertices[lp.vertex_index].co
        uvf.data[lp.index].uv = ((co.x + 0.032) / 0.07, co.y / 0.03)
    face.data.materials.append(PH.tex_material('emf_face', 0.0))
    parts.append(face)
    parts.append(L.box(name + '_plate', (0.066, 0.026, 0.0012), (0.003, -0.018, fz + 0.0002), 'tape', bevel=0.0005))
    parts.append(L.cylinder(name + '_knob', 0.0055, 0.004, (0.003, -0.026, fz + 0.002), axis='Z', segments=16, mat='black', bevel=0.0008))
    for sx in (-0.024, 0.03):
        parts.append(L.cylinder(name + '_scr', 0.0022, 0.0012, (sx, -0.022, fz + 0.001), axis='Z', segments=10, mat='nickel'))
    # five red LEDs along the top edge, pointing out
    for i in range(5):
        x = -0.034 + 0.021 * i
        parts.append(L.cylinder(name + '_ledb', 0.0026, 0.004, (x, H / 2 - 0.004, top + 0.003), axis='Y', segments=10, mat='nickel'))
        # one material per LED, so the site can light them one by one (left to right)
        led = L.lathe(name + '_led', [(0.0, 0.0), (0.0, 0.0026), (0.005, 0.0026), (0.0065, 0.0019), (0.0075, 0.0)], segments=12,
                      axis='Y', center=(x, H / 2 - 0.002, top + 0.003), mat=f'emf_led_{i}')
        parts.append(led)
    # resistors and capacitors along the top
    for i, (x, m) in enumerate(((-0.028, 'plastic_olive'), (-0.01, 'paper'), (0.012, 'paper'), (0.032, 'plastic_olive'))):
        parts.append(L.box(name + '_res', (0.0045, 0.008, 0.0035), (x, 0.037, top + 0.00175), m, bevel=0.0006))
    for (x, y) in ((-0.042, 0.036), (-0.046, 0.024)):
        parts.append(L.cylinder(name + '_cap', 0.0031, 0.0085, (x, y, top + 0.00425), axis='Z', segments=12, mat='nickel', bevel=0.0006))
    # the aerial down the left side: telescopic, the base wound with red wire
    ax_x, az = -W / 2 + 0.0045, top + 0.0045
    y0 = -0.046
    for k, (ln, r) in enumerate(((0.05, 0.0024), (0.04, 0.0018), (0.035, 0.0013), (0.03, 0.0009))):
        parts.append(L.cylinder(name + f'_ant{k}', r, ln, (ax_x, y0 + ln / 2, az), axis='Y', segments=10, mat='nickel'))
        y0 += ln - 0.004
    parts.append(L.cylinder(name + '_tip', 0.0016, 0.003, (ax_x, y0 + 0.004, az), axis='Y', segments=10, mat='nickel'))
    parts.append(L.cylinder(name + '_core', 0.0036, 0.05, (ax_x, -0.012, az), axis='Y', segments=12, mat='black'))
    parts.append(_helix(name + '_coil', (ax_x, -0.036, az), (0, 1, 0), 0.0042, 0.0013, 36, 0.00062, 'wire_red'))
    # the copper spring down the right side
    parts.append(_helix(name + '_spring', (W / 2 - 0.007, -0.03, top + 0.004), (0, 1, 0), 0.0034, 0.0022, 24, 0.00062, 'brass'))
    # wires looping round the edge
    for k, (m, off) in enumerate((('wire_red', 0.0), ('bead_blue', 0.0022), ('army_green', 0.0044), ('lego_yellow', 0.0066))):
        e = 0.0085 + off
        pts = [(-W / 2 + e + 0.006, H / 2 - e, 0), (W / 2 - e, H / 2 - e - 0.002, 0), (W / 2 - e - 0.004, -H / 2 + e, 0),
               (-W / 2 + e + 0.01, -H / 2 + e + 0.002, 0), (-W / 2 + e + 0.008, 0.0, 0)]
        path = L.catmull([Vector((x, y, top + 0.0012 + 0.0004 * k)) for x, y, _ in pts], 8)
        parts.append(L.sweep(name + f'_wire{k}', path, _circle(0.00065, 5), m))
    for (x, y) in ((-0.046, -0.036), (0.046, -0.043)):
        parts.append(L.box(name + '_pot', (0.0065, 0.0065, 0.0055), (x, y, top + 0.00275), 'bead_blue', bevel=0.0006))
    parts.append(L.box(name + '_sw', (0.008, 0.009, 0.007), (0.024, -0.046, top + 0.0035), 'red_plastic', bevel=0.0008))
    parts.append(L.cylinder(name + '_lev', 0.0012, 0.01, (0.024, -0.054, top + 0.0045), axis='Y', segments=8, mat='nickel'))
    for o in parts:
        PH.texturize(o)
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
    """A roll of duct tape lying on its side: a plain 24-sided ring on a 3"
    cardboard core. The look is all texture: woven silver tape round the
    outside, the wound layers and the core on the sides, cardboard inside."""
    ri, ro, W = 0.038, 0.055, 0.048
    o = L.lathe(name, [(0, ri), (0, ro), (W, ro), (W, ri)], segments=24, mat=None, axis='Z', close=True)
    me = o.data
    for kind, metal in (('ducttape_outer', 0.35), ('ducttape_side', 0.15), ('kraft', 0.0)):
        me.materials.append(PH.tex_material(kind, metal))
    uv = me.uv_layers.active or me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        c = poly.center
        if abs(poly.normal.z) > 0.6:          # the flat sides: planar over the diameter
            poly.material_index = 1
            for li in poly.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                uv.data[li].uv = (0.5 + co.x / (2 * ro), 0.5 + co.y / (2 * ro))
            continue
        outer = math.hypot(c.x, c.y) > (ri + ro) / 2
        poly.material_index = 0 if outer else 2
        us = []
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            us.append((math.atan2(co.y, co.x) / (2 * math.pi)) % 1.0)
        if max(us) - min(us) > 0.5:           # the face across the seam
            us = [u + 1.0 if u < 0.5 else u for u in us]
        for li, u in zip(poly.loop_indices, us):
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (u * 6, co.z / W) if outer else (u * 4, co.z / W * 0.3)
    return o


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


def _flat_blade(name, pts, thick, mat):
    """A blade lying flat: outline in XY (x along the blade, y across it),
    thickness centred on Z, with softened edges."""
    b = L.extrude_outline(name, pts, thick, mat, bevel_w=thick * 0.38)
    b.data.transform(Matrix.Translation((0, 0, -thick / 2)))
    return b


def angel_blade(name):
    """Angel blade, after the show's prop: a long three-sided blade tapering
    straight to the point, a fuller down each face for the first half, a
    polished collar that flares into a plain tube grip, and a cone pommel.
    Lies on one face; the tip is towards +X."""
    L_b, s0 = 0.262, 0.03
    axis_z = 0.0168                        # the collar's lip rests on the board
    stations = [0.0, 0.006, 0.02, 0.05, 0.09, 0.12, 0.14, 0.152, 0.17, 0.2, 0.225, 0.245, 0.256, L_b]
    rows = []
    for x in stations:
        t = x / L_b
        s = s0 * (1 - t) ** 0.92 + 0.0006
        R = s / math.sqrt(3)
        # fuller: full depth to 0.12, closing in a V by 0.152
        f = 0.0 if x < 0.004 else min(1.0, max(0.0, (0.152 - x) / 0.032)) if x > 0.12 else 1.0
        depth = 0.0013 * f * (s / s0)
        ring = []
        for k in range(3):
            a0 = math.radians(90 + 120 * k)
            a1 = math.radians(90 + 120 * (k + 1))
            c0 = Vector((0, R * math.cos(a0), R * math.sin(a0)))
            c1 = Vector((0, R * math.cos(a1), R * math.sin(a1)))
            inward = -((c0 + c1) / 2).normalized()
            ring.append(c0)
            for q, dd in ((0.3, 0.0), (0.5, depth), (0.7, 0.0)):
                ring.append(c0.lerp(c1, q) + inward * dd)
        rows.append([Vector((x, v.y, v.z + axis_z)) for v in ring])
    cols = len(rows[0])
    verts = [v for r in rows for v in r]
    faces = L.grid_faces(len(rows), cols, close_cols=True)
    faces.append(tuple(reversed(range(cols))))
    base = (len(rows) - 1) * cols
    faces.append(tuple(base + i for i in range(cols)))
    bl = L.mesh_object(name + '_b', verts, faces, None, smooth=True)
    L.auto_smooth(bl, 28)
    _tex(bl, 'silver', 1.0)
    # the handle, one lathe from the collar at the blade to the pommel's tip
    prof = [(0.0, 0.0), (0.0, 0.0118), (-0.003, 0.0132), (-0.0045, 0.0166), (-0.0085, 0.0168), (-0.0105, 0.0152),
            (-0.014, 0.0136), (-0.02, 0.0124), (-0.03, 0.0116), (-0.036, 0.0113), (-0.126, 0.0117), (-0.1275, 0.0127),
            (-0.1315, 0.0128), (-0.133, 0.0122), (-0.158, 0.0079), (-0.159, 0.0)]
    grip = L.lathe(name + '_h', prof, segments=24, mat='chrome', axis='X', center=(0, 0, axis_z))
    L.auto_smooth(grip, 35)
    o = L.join([bl, grip], name)
    o.data.transform(Matrix.Translation((-(L_b - 0.159) / 2, 0, 0)))
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


def _value_noise(rnd, nx, ny):
    g = [[rnd.uniform(-1, 1) for _ in range(ny + 1)] for _ in range(nx + 2)]

    def f(u, v):
        i, j = int(u), int(v) % ny
        fu, fv = u - i, v - int(v)
        j2 = (j + 1) % ny
        a = g[i][j] * (1 - fu) + g[i + 1][j] * fu
        b = g[i][j2] * (1 - fu) + g[i + 1][j2] * fu
        return a * (1 - fv) + b * fv
    return f


def _stag_grip(name, length, axis_z, seed=3):
    """A stag-antler grip along -X from the guard: oval, thickening towards a
    flared butt, a slight drop, and knobbly all over."""
    rnd = random.Random(seed)
    noise = _value_noise(rnd, 26, 12)
    rows = []
    n_rows, sides = 28, 14
    for i in range(n_rows + 1):
        t = i / n_rows
        x = -length * t
        ry = 0.0112 + 0.0032 * t + 0.0045 * max(0.0, (t - 0.82) / 0.18) ** 2
        rz = ry * 0.8
        drop = -0.005 * t * t
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            knob = 1 + 0.11 * noise(t * 24, k * 12 / sides) * (0.4 if t < 0.04 else 1.0)
            ring.append(Vector((x, drop + ry * math.cos(a) * knob, axis_z + rz * math.sin(a) * knob)))
        rows.append(ring)
    verts = [v for r in rows for v in r]
    faces = L.grid_faces(len(rows), sides, close_cols=True)
    faces.append(tuple(reversed(range(sides))))
    base = n_rows * sides
    faces.append(tuple(base + i for i in range(sides)))
    o = L.mesh_object(name, verts, faces, None, smooth=True)
    return _tex(o, 'stag')


def ruby_knife(name):
    """Ruby's knife, after the show's prop: a polished blade with a clip
    point that sweeps up, five scallops cut into the edge, etched lines and a
    row of runes; a thin oval guard; a knobbly stag grip. Lies flat, tip +X."""
    import json
    import os
    spec = json.load(open(os.path.join(os.path.dirname(__file__), 'blades.json')))['ruby']
    Lb = spec['length']
    axis_z = 0.0102                        # the guard's rim rests on the board
    # counter-clockwise: out along the scalloped edge to the tip, back along the spine
    pts = [tuple(p) for p in spec['edge']] + [tuple(p) for p in reversed(spec['spine'])]
    blade_o = L.extrude_outline(name + '_b', pts, 0.0042, None, bevel_w=0.0014)
    blade_o.data.transform(Matrix.Translation((0, 0, axis_z - 0.0021)))
    ys = [y for _, y in pts]
    y0, y1 = min(ys), max(ys)
    uv = blade_o.data.uv_layers.active or blade_o.data.uv_layers.new(name='UVMap')
    for lp in blade_o.data.loops:
        co = blade_o.data.vertices[lp.vertex_index].co
        uv.data[lp.index].uv = (co.x / Lb, (co.y - y0) / (y1 - y0))
    blade_o.data.materials.append(PH.tex_material('ruby_blade', 1.0))
    guard = L.cylinder(name + '_g', 0.029, 0.0048, (-0.0024, 0, 0), axis='X', segments=28, mat='chrome', bevel=0.0012)
    guard.data.transform(Matrix.Diagonal((1.0, 1.0, 0.35, 1.0)))
    guard.data.transform(Matrix.Translation((0, 0, axis_z)))
    grip = _stag_grip(name + '_h', 0.118, axis_z)
    grip.data.transform(Matrix.Translation((-0.0048, 0, 0)))
    o = L.join([blade_o, guard, grip], name)
    o.data.transform(Matrix.Translation(((0.118 - Lb) / 2, 0, 0)))
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
