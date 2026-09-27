"""Baby's lived-in details inside the cabin:
- the aftermarket slot-loading cassette deck in the dash
- Lego bricks Dean pushed into the defroster vent
- the green army man Sam crammed into the rear door ashtray
- the "D.W." / "S.W." initials carved into the trim under the package tray
"""
import math
import bpy
from mathutils import Vector, Matrix
import lib as L
import props as P
import phprops as PH


def tape_deck():
    """The aftermarket slot-loader in the dash, after photos of Baby's own:
    a wide dial window across the top, square grey buttons either side, and
    the cassette door across the bottom with the model block at its right.
    Face points -X (towards the cabin); the dial and the door are UV-mapped
    quads the site paints (tape_deck_dial, tape_deck_door)."""
    parts = []
    w, h, d = 0.18, 0.052, 0.06
    parts.append(L.box('deck_body', (d, w, h), (0, 0, 0), 'plastic_black', bevel=0.003))
    x = -d / 2
    # a raised bezel round the dial and a lip over the door
    parts.append(L.box('deck_bezel', (0.004, 0.128, 0.026), (x - 0.0015, -0.004, 0.012), 'black', bevel=0.001))
    parts.append(L.box('deck_lip', (0.003, 0.137, 0.025), (x - 0.001, -0.0035, -0.0135), 'black', bevel=0.001))
    # grey square buttons: one each side of the dial, a pair stacked at the lower left
    for (y, z, bw, bh) in ((0.074, 0.013, 0.012, 0.013), (-0.078, 0.011, 0.012, 0.017),
                           (0.074, -0.006, 0.012, 0.008), (0.074, -0.019, 0.012, 0.013)):
        parts.append(L.box('deck_btn', (0.01, bw, bh), (x - 0.004, y, z), 'tape', bevel=0.0012))
    o = L.join(parts, 'tape_deck')
    xq = x - 0.0036
    dial = L.mesh_object('tape_deck_dial', [(xq, 0.061, 0.002), (xq, -0.069, 0.002), (xq, -0.069, 0.022),
                                            (xq, 0.061, 0.022)], [(0, 1, 2, 3)], 'dial', smooth=False)
    door = L.mesh_object('tape_deck_door', [(x - 0.0026, 0.064, -0.0245), (x - 0.0026, -0.071, -0.0245),
                                            (x - 0.0026, -0.071, -0.0025), (x - 0.0026, 0.064, -0.0025)], [(0, 1, 2, 3)],
                         'black', smooth=False)
    for q in (dial, door):
        uv = q.data.uv_layers.new(name='UVMap')
        for li, (u, v) in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
            uv.data[li].uv = (u, v)
    return o, dial, door


def lego(name, mat, studs=(2, 4)):
    nx, ny = studs
    u = 0.008
    b = L.box(name + '_b', (nx * u, ny * u, 0.0096), (0, 0, 0.0048), mat, bevel=0.0006)
    parts = [b]
    for i in range(nx):
        for j in range(ny):
            parts.append(L.cylinder(name + '_s', 0.0024, 0.0017, ((i - (nx - 1) / 2) * u, (j - (ny - 1) / 2) * u,
                                                                  0.0105), axis='Z', segments=10, mat=mat))
    return L.join(parts, name)


def army_man(name):
    g = 'army_green'
    parts = [
        L.box(name + '_base', (0.018, 0.02, 0.003), (0, 0, 0.0015), g),
        L.box(name + '_legL', (0.005, 0.005, 0.02), (0.002, 0.004, 0.013), g),
        L.box(name + '_legR', (0.005, 0.005, 0.02), (-0.003, -0.004, 0.012), g),
        L.box(name + '_body', (0.008, 0.012, 0.018), (0, 0, 0.031), g, bevel=0.001),
        L.cylinder(name + '_head', 0.0045, 0.008, (0, 0, 0.045), axis='Z', segments=10, mat=g),
        L.cylinder(name + '_helmet', 0.006, 0.003, (0, 0, 0.049), axis='Z', segments=10, mat=g),
        P.rod(name + '_rifle', (0.012, -0.004, 0.034), (-0.006, 0.01, 0.042), 0.0015, g, 6),
        P.rod(name + '_arm', (0.0, -0.007, 0.036), (0.008, -0.006, 0.038), 0.0022, g, 6),
    ]
    return L.join(parts, name)


def clear_centre_stack():
    """The passenger half of the base model's dash starts in a diagonal right
    beside the centre, and from the driver's seat that raised edge covers the
    deck's right-hand end. Slide the diagonal 5.5 cm towards the passenger
    side: its lower end is the vertex column at y = -0.031, its upper end the
    one at y = -0.206 below the top of the dash."""
    o = bpy.data.objects.get('Desktop_Indoor')
    if o is None:
        return
    mw = o.matrix_world
    inv = mw.inverted()
    moved = 0
    for v in o.data.vertices:
        p = mw @ v.co
        if abs(p.y + 0.031) < 0.004 or (abs(p.y + 0.206) < 0.004 and p.z < 0.93):
            p.y -= 0.055
            v.co = inv @ p
            moved += 1
    o.data.update()
    print('dash diagonal moved', moved, 'verts')


def green_cooler(name='cooler'):
    """The green cooler from the back seat: a steel-belted cooler in green
    enamel with a cream band at the lid, a chrome latch at the front, chrome
    handles at the ends and a diamond badge. Built standing on z = 0, its
    front (latch) towards +X, its length along Y."""
    D, Lc, H = 0.28, 0.44, 0.33
    hb, band, lid = 0.255, 0.018, 0.055
    parts = []
    body = L.box(name + '_body', (D, Lc, hb), (0, 0, hb / 2), None, bevel=0.012, segments=3)
    parts.append(P._tex(body, 'cooler_green', 0.25))
    parts.append(L.box(name + '_band', (D + 0.004, Lc + 0.004, band), (0, 0, hb + band / 2), 'ivory', bevel=0.004))
    top = L.box(name + '_lid', (D + 0.006, Lc + 0.006, lid), (0, 0, hb + band + lid / 2), None, bevel=0.01, segments=3)
    parts.append(P._tex(top, 'cooler_green', 0.25))
    xf = D / 2 + 0.003
    # the latch across the band, front and centre
    parts.append(L.box(name + '_latch', (0.006, 0.046, 0.075), (xf + 0.003, 0, hb + band / 2 + 0.006), 'chrome', bevel=0.003))
    parts.append(L.box(name + '_clasp', (0.012, 0.03, 0.022), (xf + 0.008, 0, hb + band + 0.028), 'chrome', bevel=0.004))
    # folding handles at both ends: plates and a bail
    for ys in (1, -1):
        yf = ys * (Lc / 2 + 0.003)
        for dx in (-0.045, 0.045):
            parts.append(L.box(name + '_plate', (0.03, 0.006, 0.05), (dx, yf + ys * 0.002, hb - 0.035), 'chrome', bevel=0.002))
        bail = [Vector((-0.045, yf + ys * 0.006, hb - 0.03)), Vector((-0.045, yf + ys * 0.012, hb - 0.075)),
                Vector((0.045, yf + ys * 0.012, hb - 0.075)), Vector((0.045, yf + ys * 0.006, hb - 0.03))]
        parts.append(L.sweep(name + '_bail', L.catmull(bail, 6), P._circle(0.0035, 8), 'chrome'))
    # hinges at the back
    for dy in (-0.13, 0.13):
        parts.append(L.cylinder(name + '_hinge', 0.006, 0.04, (-D / 2 - 0.004, dy, hb + band), axis='Y', segments=12, mat='chrome'))
    # the diamond badge, low on the front towards the left
    bx, bz = xf + 0.0012, 0.075
    by = 0.1
    verts = [(bx, by, bz - 0.032), (bx, by - 0.058, bz), (bx, by, bz + 0.032), (bx, by + 0.058, bz)]
    badge = L.mesh_object(name + '_badge', verts, [(0, 1, 2, 3)], None, smooth=False)
    uv = badge.data.uv_layers.new(name='UVMap')
    for lp, (u, v) in zip(badge.data.loops, ((0.5, 0.0), (1.0, 0.5), (0.5, 1.0), (0.0, 0.5))):
        uv.data[lp.index].uv = (u, v)
    badge.data.materials.append(PH.tex_material('cooler_badge', 0.0))
    parts.append(badge)
    return L.join(parts, name)


def build(fa=None, ra=None):
    L.set_collection('Baby')
    clear_centre_stack()
    # ---------------------------------------------------------------- tape deck (centre of the dash)
    deck, dial, door = tape_deck()
    # slightly smaller and nudged in/up so the dash's diagonal cut-out doesn't
    # swallow its right-hand end (placement found by ray-testing the face
    # from the driver's seat)
    for o in (deck, dial, door):
        o.data.transform(Matrix.Diagonal((1.0, 0.92, 0.92, 1.0)))
        o.location = (0.895, -0.015, 0.865)
        L.bake_transform(o)

    # ---------------------------------------------------------------- Legos in the defroster vent
    bricks = []
    for i, (mat, y, rot, tilt) in enumerate((('lego_red', 0.16, 12, 18), ('lego_blue', 0.205, -20, 35),
                                             ('lego_yellow', 0.25, 5, 10), ('lego_red', 0.295, -8, 22))):
        b = lego(f'lego_{i}', mat)
        b.data.transform(Matrix.Rotation(math.radians(tilt), 4, 'Y'))
        b.data.transform(Matrix.Rotation(math.radians(rot), 4, 'Z'))
        b.location = (0.965, y, 1.046)
        L.bake_transform(b)
        bricks.append(b)
    L.join(bricks, 'legos')
    vent = []
    for k in range(14):
        vent.append(L.box('vent_slat', (0.012, 0.004, 0.004), (0.965, 0.10 + 0.018 * k, 1.042), 'black'))
    L.join(vent, 'defroster_vent')

    # ---------------------------------------------------------------- rear door ashtray + army man
    door = bpy.data.objects.get('door_rl')
    tray = L.box('ashtray', (0.1, 0.035, 0.04), (-0.52, 0.765, 0.735), 'chrome', bevel=0.006)
    hollow = L.box('ashtray_hollow', (0.086, 0.024, 0.02), (-0.52, 0.762, 0.753), 'black')
    man = army_man('army_man')
    man.data.transform(Matrix.Rotation(math.radians(80), 4, 'Z'))
    man.data.transform(Matrix.Rotation(math.radians(-18), 4, 'X'))
    man.location = (-0.52, 0.762, 0.742)
    L.bake_transform(man)
    ash = L.join([tray, hollow], 'ashtray_rear')
    for o in (ash, man):
        if door:
            o.parent = door
            o.matrix_parent_inverse = door.matrix_world.inverted()

    # ---------------------------------------------------------------- the green cooler on the back seat
    # passenger side, its back against the seat back, latch towards the front
    cooler = green_cooler()
    cooler.location = (-0.42, -0.42, 0.686)
    L.bake_transform(cooler)

    # ---------------------------------------------------------------- carved initials trim
    # a wooden trim board on the package tray behind the back seat; the top face
    # carries the carving (u across the car, v towards the rear window)
    X0, X1, W, Z = -1.21, -1.13, 0.9, 1.071
    strip = L.box('initials_trim', (X1 - X0, W, 0.012), ((X0 + X1) / 2, 0.0, Z), 'wood_trim', bevel=0.002)
    me = strip.data
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co.y + W / 2) / W, (X1 - co.x) / (X1 - X0))
    return deck
