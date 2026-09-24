"""Make the source model into Baby: remove what she doesn't have (mag rims,
the script on the trunk lid, the passenger mirror, stock plates), add what
she does (the second exhaust), and split the tyres per corner."""
import math
import bpy
from mathutils import Vector, Matrix
import lib as L


def islands(obj):
    """Split an object into loose parts; returns [(part, centre, radius_from_axis_fn)]."""
    return L.split_loose(obj)


def centre(o):
    vs = [v.co for v in o.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return (mn + mx) / 2, mn, mx


def keep_islands(name, keep, new_name=None):
    o = bpy.data.objects.get(name)
    if o is None:
        return None
    parts = L.split_loose(o)
    kept = []
    for p in parts:
        c, mn, mx = centre(p)
        if keep(c, mn, mx):
            kept.append(p)
        else:
            L.delete(p)
    if not kept:
        return None
    return L.join(kept, new_name or name)


def plate_anchor(src, name):
    """Empty at the stock plate's face centre. The plate plane comes from a
    PCA of its vertices; the outward normal is stored as a custom property
    (exported as glTF extras) for the web app to orient the new plate."""
    o = bpy.data.objects.get(src)
    if o is None:
        return
    vs = [v.co.copy() for v in o.data.vertices]
    c = sum(vs, Vector()) / len(vs)
    # covariance in the x/z plane (plates only tilt about the car's width axis)
    sxx = sum((v.x - c.x) ** 2 for v in vs)
    szz = sum((v.z - c.z) ** 2 for v in vs)
    sxz = sum((v.x - c.x) * (v.z - c.z) for v in vs)
    # direction of largest spread in x/z = the plate's vertical edge
    ang = 0.5 * math.atan2(2 * sxz, sxx - szz)
    edge = Vector((math.cos(ang), 0, math.sin(ang)))
    if abs(edge.z) < abs(edge.x):
        edge = Vector((-edge.z, 0, edge.x))
    n = Vector((edge.z, 0, -edge.x))
    if (n.x > 0) != (c.x > 0):
        n = -n
    front = max(vs, key=lambda v: v.dot(n))
    face = c + n * ((front - c).dot(n) + 0.003)
    e = L.empty(name, face)
    e['normal'] = [n.x, n.y, n.z]
    print('plate', name, [round(v, 3) for v in face], [round(v, 3) for v in n])


def run(fa, ra):
    plate_anchor('ID_FrontChromes', 'anchor_plate_front')
    plate_anchor('IDBack_FrontChromes', 'anchor_plate_rear')
    for n in ('CWheel_wheel', 'Bolt_wheel', 'ID_FrontChromes', 'IDBack_FrontChromes'):
        o = bpy.data.objects.get(n)
        if o:
            L.delete(o)

    # rear "Chevrolet" script: Baby has no badges on the back except the bowtie
    keep_islands('chevroletLogo_FrontChromes', lambda c, mn, mx: c.x > 0, 'script_front')
    # Baby has only the driver's side mirror
    keep_islands('Mirror_Indoor', lambda c, mn, mx: c.y > 0, 'mirror_driver_head')
    keep_islands('MirrorBracket_Indoor', lambda c, mn, mx: c.y > 0, 'mirror_driver_bracket')

    # tyres: keep the textured rubber, drop the 5-slot mag rims
    wheel = bpy.data.objects['Wheel_wheel']
    parts = L.split_loose(wheel)
    tyres = {'fl': [], 'fr': [], 'rl': [], 'rr': []}
    for p in parts:
        c, mn, mx = centre(p)
        ax = fa if c.x > 0 else ra
        r = max(math.hypot(v.co.x - ax.x, v.co.z - ax.z) for v in p.data.vertices)
        if r < 0.26:
            L.delete(p)
            continue
        key = ('f' if c.x > 0 else 'r') + ('l' if c.y > 0 else 'r')
        tyres[key].append(p)
    for k, ps in tyres.items():
        t = L.join(ps, f'tire_{k}')
        ax = fa if k[0] == 'f' else ra
        L.set_origin(t, (ax.x, math.copysign(0.843, 1 if k[1] == 'l' else -1), ax.z))

    # dual exhaust: mirror the single pipe to the passenger side
    ex = bpy.data.objects.get('Exhaust_FrontChromes')
    if ex:
        ex2 = L.duplicate(ex, 'exhaust_r')
        ex2.data.transform(Matrix.Scale(-1, 4, (0, 1, 0)))
        ex2.data.flip_normals()
        L.join([ex, ex2], 'exhaust')
