"""Baby's wheels: 15" polished chrome dished wheels with a ring of small round
holes and a chrome centre cap, on chunky black tyres. Plus drums and wheel wells."""
import math
from mathutils import Vector, Matrix
import lib as L
import dims as D

HOLES = 12
HOLE_R = 0.0115
HOLE_RING = 0.118


def tire(name):
    w = D.TIRE_W / 2
    R = D.TIRE_R
    prof = [(-w + 0.012, D.RIM_R - 0.004), (-w + 0.004, D.RIM_R + 0.03), (-w - 0.002, 0.25),
            (-w + 0.001, 0.285), (-w + 0.008, 0.303), (-w + 0.020, 0.313), (-w + 0.035, R)]
    # tread with circumferential grooves
    grooves = [-0.055, -0.018, 0.018, 0.055]
    x = -w + 0.035
    tread = []
    for g in grooves:
        tread += [(g - 0.006, R), (g - 0.004, R - 0.009), (g + 0.004, R - 0.009), (g + 0.006, R)]
    prof += tread
    prof += [(w - 0.035, R), (w - 0.020, 0.313), (w - 0.008, 0.303), (w - 0.001, 0.285), (w + 0.002, 0.25),
             (w - 0.004, D.RIM_R + 0.03), (w - 0.012, D.RIM_R - 0.004)]
    # close on the inside
    prof += [(0.0, D.RIM_R - 0.012)]
    t = L.lathe(name, prof, segments=72, mat='tire', axis='Y', center=(0, 0, 0), close=True)
    L.auto_smooth(t, 50)
    return t


def rim(name):
    """Outboard face at +Y. Closed lathe profile so it can take booleans."""
    prof = [
        (-0.095, 0.188), (0.080, 0.188),            # barrel
        (0.092, 0.196), (0.104, 0.206), (0.108, 0.203),   # outer polished lip
        (0.102, 0.192), (0.090, 0.178),              # into the dish
        (0.072, 0.160), (0.062, 0.140), (0.058, 0.110),  # dish wall -> face
        (0.058, 0.075), (0.064, 0.062), (0.070, 0.058),  # hub step
        (0.072, 0.045),                               # lug face
        (0.070, 0.0), (0.050, 0.0),                   # centre (welded on the axis)
        (0.050, 0.055), (0.046, 0.10), (0.052, 0.15),
        (0.070, 0.170), (0.078, 0.178), (-0.087, 0.180),
    ]
    r = L.lathe(name, prof, segments=72, mat='chrome', axis='Y', center=(0, 0, 0), close=True)
    L.fix_normals(r)
    # ring of small round holes through the dished face
    for i in range(HOLES):
        a = 2 * math.pi * i / HOLES
        c = L.cylinder('hole', HOLE_R, 0.12, (HOLE_RING * math.cos(a), 0.04, HOLE_RING * math.sin(a)),
                       axis='Y', segments=16)
        L.boolean(r, c, 'DIFFERENCE')
    L.auto_smooth(r, 45)
    # centre cap and lug nuts
    cap = L.lathe(name + '_cap', [(0.070, 0.042), (0.082, 0.040), (0.090, 0.030), (0.094, 0.012),
                                  (0.095, 0.0)], segments=40, mat='chrome', axis='Y')
    lugs = []
    for i in range(5):
        a = 2 * math.pi * i / 5 + 0.3
        lugs.append(L.cylinder('lug', 0.009, 0.022, (0.050 * math.cos(a), 0.078, 0.050 * math.sin(a)),
                               axis='Y', segments=6, mat='chrome'))
    hub = L.join([r, cap] + lugs, name)
    return hub


def drum(name):
    d = L.lathe(name, [(-0.06, 0.0), (-0.06, 0.14), (0.03, 0.15), (0.045, 0.12), (0.05, 0.0)],
                segments=40, mat='drum', axis='Y')
    return d


def build():
    L.set_collection('Baby')
    base_tire = tire('tire_proto')
    base_rim = rim('rim_proto')
    base_drum = drum('drum_proto')
    wheels = {}
    for key, x, side in (('fl', D.X_FA, 1), ('fr', D.X_FA, -1), ('rl', D.X_RA, 1), ('rr', D.X_RA, -1)):
        y = side * D.Y_WHEEL
        t = L.duplicate(base_tire, f'tire_{key}')
        r = L.duplicate(base_rim, f'rim_{key}')
        d = L.duplicate(base_drum, f'drum_{key}')
        for o in (t, r, d):
            if side < 0:
                o.data.transform(Matrix.Scale(-1, 4, (0, 1, 0)))
                o.data.flip_normals()
            o.location = (x, y, D.WHEEL_Z)
        wheels[key] = (t, r, d)
    for o in (base_tire, base_rim, base_drum):
        L.delete(o)

    # wheel wells: dark liners inside each arch
    for cx in (D.X_FA, D.X_RA):
        for side in (1, -1):
            pts = L.superellipse(cx, D.WHEEL_Z, D.ARCH_A - 0.005, D.ARCH_B - 0.005, D.ARCH_N,
                                 steps=40, start=0.0, end=math.pi)
            y0, y1 = (0.58, 0.985) if side > 0 else (-0.985, -0.58)
            sec = [[Vector((x, y, z)) for (x, z) in pts] for y in (y0, y1)]
            liner = L.loft(f'wheelwell_{"f" if cx > 0 else "r"}{"l" if side > 0 else "r"}', sec,
                           mat='underbody', flip=side > 0)
            # inner wall
            L.auto_smooth(liner, 60)
    return wheels
