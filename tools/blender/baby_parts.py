"""Baby-specific exterior parts added to the base model: her polished dished
wheels with the ring of holes, the two A-pillar spotlights, and the anchor
empties the web app uses for plates, lamps and lights."""
import math
import bpy
from mathutils import Vector, Matrix
import lib as L
import wheels as W

RIM_LIP_R = 0.236      # visible chrome radius on the source tyres
WHEEL_Y = 0.843        # tyre centre plane
RIM_OUT = 0.945        # outer lip plane


def rims(fa, ra):
    proto = W.rim('rim_proto')
    s = RIM_LIP_R / 0.206
    proto.data.transform(Matrix.Diagonal((s, 1.0, s, 1.0)))
    # move so the outer lip sits at RIM_OUT - WHEEL_Y from the tyre centre
    proto.data.transform(Matrix.Translation((0, (RIM_OUT - WHEEL_Y) - 0.108, 0)))
    drum = W.drum('drum_proto')
    drum.data.transform(Matrix.Diagonal((1.25, 1.0, 1.25, 1.0)))
    out = {}
    for key, ax, side in (('fl', fa, 1), ('fr', fa, -1), ('rl', ra, 1), ('rr', ra, -1)):
        r = L.duplicate(proto, f'rim_{key}')
        d = L.duplicate(drum, f'drum_{key}')
        for o in (r, d):
            if side < 0:
                o.data.transform(Matrix.Scale(-1, 4, (0, 1, 0)))
                o.data.flip_normals()
            o.location = (ax.x, side * WHEEL_Y, ax.z)
        out[key] = r
    L.delete(proto)
    L.delete(drum)
    return out


def spotlight(side, pivot, mount):
    sfx = 'l' if side > 0 else 'r'
    housing = L.lathe('spot_housing', [(-0.085, 0.0), (-0.082, 0.025), (-0.07, 0.045), (-0.045, 0.058),
                                       (-0.01, 0.062), (0.02, 0.063), (0.026, 0.060), (0.024, 0.056)],
                      segments=40, mat='chrome', axis='X')
    ring = L.lathe('spot_ring', [(0.018, 0.064), (0.028, 0.064), (0.030, 0.058)], segments=40, mat='chrome',
                   axis='X')
    lens = L.lathe('spot_lens', [(0.024, 0.056), (0.030, 0.035), (0.032, 0.0)], segments=40,
                   mat='spot_lens', axis='X')
    o = L.join([housing, ring, lens], f'spotlight_{sfx}')
    L.auto_smooth(o, 45)
    o.location = pivot
    # stalk through the pillar and a small yoke
    stalk = L.sweep(f'spot_stalk_{sfx}', [Vector(pivot) + Vector((-0.02, 0, -0.045)), Vector(mount)],
                    [(0.009 * math.cos(a), 0.009 * math.sin(a)) for a in
                     [2 * math.pi * i / 10 for i in range(10)]], 'chrome')
    yoke = L.cylinder(f'spot_yoke_{sfx}', 0.012, 0.05, Vector(pivot) + Vector((-0.02, 0, -0.035)), axis='Z',
                      mat='chrome')
    L.join([stalk, yoke], f'spot_mount_{sfx}')
    a = L.empty(f'anchor_spot_{sfx}', (0.035, 0, 0))
    a.parent = o
    # the handle inside the cabin that Dean uses to aim it
    h = L.sweep(f'spot_handle_{sfx}', [Vector(mount) + Vector((-0.01, -side * 0.02, 0.0)),
                                        Vector(mount) + Vector((-0.07, -side * 0.10, -0.03))],
                [(0.006 * math.cos(a), 0.006 * math.sin(a)) for a in
                 [2 * math.pi * i / 8 for i in range(8)]], 'chrome')
    return o


def build(fa, ra):
    L.set_collection('Baby')
    rims(fa, ra)
    for side in (1, -1):
        pivot = (0.93, side * 0.965, 1.10)
        mount = (0.95, side * 0.83, 1.07)
        spotlight(side, pivot, mount)
    # anchors used by the web app
    for side, sfx in ((1, 'l'), (-1, 'r')):
        L.empty(f'anchor_headlamp_{sfx}0', (2.585, side * 0.594, 0.599))
        L.empty(f'anchor_headlamp_{sfx}1', (2.585, side * 0.753, 0.599))
        L.empty(f'anchor_tail_{sfx}', (-2.66, side * 0.64, 0.757))
