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


def tape_deck():
    """Face points -X (towards the cabin). Dial window + slot + olive buttons."""
    parts = []
    w, h, d = 0.18, 0.052, 0.06
    parts.append(L.box('deck_body', (d, w, h), (0, 0, 0), 'plastic_black', bevel=0.003))
    # cassette slot with its flap
    parts.append(L.box('deck_slot', (0.004, 0.11, 0.008), (-d / 2 - 0.0015, -0.004, -0.009), 'black'))
    parts.append(L.box('deck_flap', (0.003, 0.10, 0.006), (-d / 2 - 0.003, -0.004, -0.014), 'steel', bevel=0.001))
    # chunky olive push buttons either side
    for y, z in ((0.074, 0.011), (-0.074, 0.011), (0.074, -0.011), (-0.074, -0.011)):
        parts.append(L.box('deck_btn', (0.014, 0.022, 0.016), (-d / 2 - 0.006, y, z), 'plastic_olive', bevel=0.002))
    o = L.join(parts, 'tape_deck')
    # FM/AM dial window: a separate UV-mapped quad for the dial texture
    x = -d / 2 - 0.0012
    dial = L.mesh_object('tape_deck_dial', [(x, 0.059, 0.002), (x, -0.059, 0.002), (x, -0.059, 0.022),
                                            (x, 0.059, 0.022)], [(0, 1, 2, 3)], 'dial', smooth=False)
    me = dial.data
    uv = me.uv_layers.new(name='UVMap')
    for li, (u, v) in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = (u, v)
    return o, dial


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


def build(fa=None, ra=None):
    L.set_collection('Baby')
    # ---------------------------------------------------------------- tape deck (centre of the dash)
    deck, dial = tape_deck()
    for o in (deck, dial):
        o.location = (0.905, -0.06, 0.845)
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
