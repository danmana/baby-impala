"""Engine bay and the 327 small-block V8 ("327 four-barrel, 275 horses").

Grouped under the empty 'engine' so the exploded view can lift it out."""
import math
from mathutils import Vector, Matrix
import lib as L
import props as P

CRANK_Z = 0.44
X0, X1 = 1.30, 1.92      # block rear / front


def block():
    parts = []
    # lower block + oil pan
    parts.append(L.box('blk_lower', (X1 - X0, 0.36, 0.18), ((X0 + X1) / 2, 0, CRANK_Z), 'engine', bevel=0.02))
    parts.append(L.box('oil_pan', (X1 - X0 - 0.06, 0.30, 0.13), ((X0 + X1) / 2, 0, CRANK_Z - 0.14), 'engine_dark',
                       bevel=0.02))
    # the V: two cylinder banks at 45 degrees
    for side in (1, -1):
        bank = L.box('bank', (X1 - X0 - 0.02, 0.2, 0.22), (0, 0, 0), 'engine', bevel=0.015)
        bank.data.transform(Matrix.Rotation(side * math.radians(45), 4, 'X'))
        bank.location = ((X0 + X1) / 2, side * 0.12, CRANK_Z + 0.14)
        L.bake_transform(bank)
        parts.append(bank)
        head = L.box('head', (X1 - X0 - 0.03, 0.2, 0.08), (0, 0, 0), 'engine', bevel=0.012)
        head.data.transform(Matrix.Rotation(side * math.radians(45), 4, 'X'))
        head.location = ((X0 + X1) / 2, side * 0.23, CRANK_Z + 0.25)
        L.bake_transform(head)
        parts.append(head)
    return L.join(parts, 'engine_block')


def valve_covers():
    out = []
    for side in (1, -1):
        vc = L.box('valve_cover', (X1 - X0 - 0.06, 0.16, 0.07), (0, 0, 0), 'chrome', bevel=0.022)
        vc.data.transform(Matrix.Rotation(side * math.radians(45), 4, 'X'))
        vc.location = ((X0 + X1) / 2, side * 0.28, CRANK_Z + 0.30)
        L.bake_transform(vc)
        out.append(vc)
        # breather cap
        cap = L.cylinder('breather', 0.025, 0.04, (X1 - 0.12, side * 0.3, CRANK_Z + 0.36), axis='Z',
                         mat='chrome', bevel=0.004)
        out.append(cap)
    return L.join(out, 'engine_valve_covers')


def intake():
    parts = [L.box('intake', (0.34, 0.2, 0.08), ((X0 + X1) / 2, 0, CRANK_Z + 0.24), 'engine', bevel=0.02)]
    parts.append(L.box('carb', (0.13, 0.13, 0.08), ((X0 + X1) / 2, 0, CRANK_Z + 0.31), 'steel', bevel=0.01))
    # round chrome air cleaner with the black element band
    ac = L.lathe('air_cleaner', [(0.0, 0.0), (0.0, 0.18), (0.005, 0.185), (0.06, 0.185), (0.066, 0.17),
                                 (0.07, 0.03), (0.072, 0.0)], segments=48, mat='chrome', axis='Z',
                 center=((X0 + X1) / 2, 0, CRANK_Z + 0.34))
    band = L.lathe('air_filter', [(0.008, 0.176), (0.056, 0.176)], segments=48, mat='engine_dark', axis='Z',
                   center=((X0 + X1) / 2, 0, CRANK_Z + 0.34))
    nut = L.cylinder('ac_nut', 0.02, 0.02, ((X0 + X1) / 2, 0, CRANK_Z + 0.42), axis='Z', mat='chrome')
    parts += [ac, band, nut]
    return L.join(parts, 'engine_intake')


def front_accessories():
    parts = []
    x = X1 + 0.02
    parts.append(L.cylinder('water_pump', 0.06, 0.1, (x + 0.04, 0, CRANK_Z + 0.05), axis='X', mat='engine'))
    parts.append(L.cylinder('pulley_crank', 0.08, 0.03, (x + 0.02, 0, CRANK_Z - 0.06), axis='X', mat='gunmetal'))
    parts.append(L.cylinder('pulley_pump', 0.07, 0.025, (x + 0.1, 0, CRANK_Z + 0.05), axis='X', mat='gunmetal'))
    parts.append(L.cylinder('alternator', 0.065, 0.13, (x - 0.02, -0.24, CRANK_Z + 0.18), axis='X', mat='steel'))
    # fan
    hub = L.cylinder('fan_hub', 0.04, 0.03, (x + 0.15, 0, CRANK_Z + 0.05), axis='X', mat='gunmetal')
    parts.append(hub)
    for i in range(5):
        b = L.box('fan_blade', (0.004, 0.06, 0.2), (0, 0, 0.12), 'gunmetal')
        b.data.transform(Matrix.Rotation(math.radians(25), 4, 'Z'))
        b.data.transform(Matrix.Rotation(2 * math.pi * i / 5, 4, 'X'))
        b.location = (x + 0.15, 0, CRANK_Z + 0.05)
        L.bake_transform(b)
        parts.append(b)
    # distributor with plug wires to both banks
    dist = L.cylinder('distributor', 0.04, 0.1, (X0 + 0.02, 0, CRANK_Z + 0.3), axis='Z', mat='engine_dark')
    parts.append(dist)
    for side in (1, -1):
        for k in range(4):
            xp = X0 + 0.08 + k * 0.13
            a = Vector((X0 + 0.02, side * 0.02, CRANK_Z + 0.35))
            b = Vector((xp, side * 0.35, CRANK_Z + 0.2))
            m = (a + b) / 2 + Vector((0, 0, 0.08))
            parts.append(L.sweep('plug_wire', L.catmull([a, m, b], 6), [(0.004 * math.cos(t), 0.004 * math.sin(t))
                                                                      for t in [2 * math.pi * j / 6 for j in range(6)]],
                                 'wire_red'))
    return L.join(parts, 'engine_front')


def exhaust_manifolds():
    out = []
    for side in (1, -1):
        for k in range(4):
            xp = X0 + 0.08 + k * 0.14
            a = Vector((xp, side * 0.30, CRANK_Z + 0.16))
            b = Vector((xp, side * 0.36, CRANK_Z + 0.02))
            c = Vector((X0 + 0.1, side * 0.36, CRANK_Z - 0.06))
            out.append(L.sweep('hdr', L.catmull([a, b, c], 6), [(0.018 * math.cos(t), 0.018 * math.sin(t))
                                                             for t in [2 * math.pi * j / 10 for j in range(10)]],
                               'exhaust'))
    return L.join(out, 'engine_exhaust')


def transmission():
    bell = L.lathe('bellhousing', [(0.0, 0.16), (0.12, 0.13), (0.34, 0.09), (0.5, 0.06), (0.5, 0.0)], segments=24,
                   mat='steel_dark', axis='X', center=(X0 - 0.5, 0, CRANK_Z - 0.02))
    return L.join([bell], 'transmission')


def bay():
    parts = []
    for side in (1, -1):
        parts.append(L.box('inner_fender', (1.2, 0.02, 0.42), (1.78, side * 0.80, 0.52), 'underbody'))
    parts.append(L.box('radiator_support', (0.04, 1.6, 0.36), (2.44, 0, 0.52), 'underbody'))
    parts.append(L.box('radiator', (0.06, 1.1, 0.36), (2.38, 0, 0.52), 'radiator', bevel=0.004))
    parts.append(L.box('radiator_tank', (0.08, 1.14, 0.05), (2.38, 0, 0.72), 'engine_dark', bevel=0.01))
    parts.append(L.box('battery', (0.25, 0.17, 0.18), (2.12, 0.60, 0.44), 'plastic_black', bevel=0.01))
    for dy, m in ((-0.05, 'red_plastic'), (0.05, 'plastic_black')):
        parts.append(L.cylinder('terminal', 0.012, 0.02, (2.12 + 0.08, 0.60 + dy, 0.54), axis='Z', mat=m))
    parts.append(L.box('bay_floor', (1.3, 1.56, 0.02), (1.78, 0, 0.27), 'underbody'))
    # brake booster and master cylinder on the firewall (driver side)
    parts.append(L.cylinder('booster', 0.13, 0.12, (1.2, 0.45, 0.66), axis='X', mat='engine_dark'))
    parts.append(L.box('master_cyl', (0.16, 0.06, 0.07), (1.32, 0.45, 0.68), 'steel', bevel=0.01))
    return L.join(parts, 'engine_bay')


def build(fa=None, ra=None):
    L.set_collection('Baby')
    bay()
    e = L.empty('engine', ((X0 + X1) / 2, 0, CRANK_Z))
    for o in (block(), valve_covers(), intake(), front_accessories(), exhaust_manifolds(), transmission()):
        o.parent = e
        o.matrix_parent_inverse = Matrix.Translation(e.location).inverted()
    return e
