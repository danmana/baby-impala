"""The hunter's arsenal in Baby's trunk.

- a bulkhead closing the trunk off from the rear seat
- a grey-carpeted tray with the gear laid out in it
- the hinged false floor ('false_floor'): black carpet on top, black felt on
  its underside with weapons strapped to it; it lifts to stand upright
- 'trunk_lid_inner': the underside of the lid, UV-mapped for the painted
  Devil's Trap (the texture itself is painted at runtime)

Items are named 'item_<key>'; the web app maps keys to names and lore.
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix
import lib as L
import props as P

HINGE_X = -1.665
BOARD_Z = 0.612          # board centre plane (closed)
BOARD_T = 0.02
BOARD_LEN = 0.80
BOARD_W = 1.44
TRAY_X = (-2.47, -1.68)
TRAY_Y = 0.70


def floor_z(x):
    return 0.398 - 0.1217 * (x + 1.7)


def place_on_tray(o, x, y, rot=0.0, lift=0.0, parent=None):
    o.data.transform(Matrix.Rotation(math.radians(rot), 4, 'Z'))
    mn = min(v.co.z for v in o.data.vertices)
    o.location = (x, y, floor_z(x) + 0.012 - mn + lift)
    L.bake_transform(o)
    return o


def place_on_board(o, u, h, theta=0.0):
    """Mount an item on the board's underside. u: viewer-right (m), h: height
    above the hinge when the board stands up, theta: in-plane angle (deg)."""
    t = math.radians(theta)
    R = Vector((0, -1, 0))        # viewer's right
    U = Vector((-1, 0, 0))        # up along the standing board (closed: towards the rear)
    N = Vector((0, 0, -1))        # faces the viewer once the board stands up
    X = R * math.cos(t) + U * math.sin(t)
    Z = N
    Y = Z.cross(X)
    mx = max(v.co.z for v in o.data.vertices)
    # the item's back (its lowest local z) sits on the felt
    mn = min(v.co.z for v in o.data.vertices)
    o.data.transform(Matrix.Translation((0, 0, -mn)))
    M = Matrix((X, Y, Z)).transposed().to_4x4()
    o.data.transform(M)
    o.location = (HINGE_X - h, -u, BOARD_Z - BOARD_T / 2 - 0.0015)
    L.bake_transform(o)
    return o


def lid_inner():
    lid = bpy.data.objects.get('trunk_lid')
    if lid is None:
        return None
    me = lid.data.copy()
    bm = bmesh.new()
    bm.from_mesh(me)
    mw = lid.matrix_world
    bmesh.ops.transform(bm, matrix=mw, verts=bm.verts)
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < 0.35], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    for v in bm.verts:
        v.co.z -= 0.012
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    xs = [v.co.x for v in bm.verts]
    x0, x1 = min(xs), max(xs)
    # drop the body atlas UVs inherited from the lid: the trap gets its own planar map
    for layer in list(bm.loops.layers.uv.values()):
        bm.loops.layers.uv.remove(layer)
    for f in bm.faces:
        f.material_index = 0
    uv = bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        for lp in f.loops:
            co = lp.vert.co
            lp[uv].uv = ((co.y + 0.80) / 1.60, (co.x - x0) / (x1 - x0))
    out = bpy.data.meshes.new('trunk_lid_inner')
    bm.to_mesh(out)
    bm.free()
    bpy.data.meshes.remove(me)
    out.materials.clear()
    o = bpy.data.objects.new('trunk_lid_inner', out)
    L.link(o)
    o.data.materials.append(L.material('trap_paint'))
    # ride with the lid
    o.parent = lid
    o.matrix_parent_inverse = lid.matrix_world.inverted()
    print('lid inner bounds x', round(x0, 3), round(x1, 3))
    return o


def build(fa=None, ra=None):
    L.set_collection('Baby')
    lid_inner()

    # bulkhead between the rear seat back and the trunk
    bh = L.box('trunk_bulkhead', (0.02, 1.62, 0.66), (-1.62, 0, 0.40 + 0.33), 'carpet')

    # tray: bottom follows the sloped floor, grey carpet, a few dividers
    x0, x1 = TRAY_X
    sec = []
    for x in (x0, x1):
        z = floor_z(x) + 0.008
        sec.append([Vector((x, -TRAY_Y, z)), Vector((x, TRAY_Y, z))])
    tray = L.loft('trunk_tray', sec, mat='carpet_gray', flip=True)
    parts = [tray]
    for yy in (-0.26, 0.26):
        parts.append(L.box('tray_div', (x1 - x0, 0.02, 0.07), ((x0 + x1) / 2, yy, floor_z((x0 + x1) / 2) + 0.04),
                           'carpet_gray', bevel=0.004))
    parts.append(L.box('tray_div', (0.02, 2 * TRAY_Y, 0.07), (-2.06, 0, floor_z(-2.06) + 0.04), 'carpet_gray',
                       bevel=0.004))
    for yy in (-TRAY_Y, TRAY_Y):
        parts.append(L.box('tray_wall', (x1 - x0, 0.02, 0.2), ((x0 + x1) / 2, yy, floor_z((x0 + x1) / 2) + 0.1),
                           'carpet_gray'))
    L.join(parts, 'trunk_tray')

    # ---------------------------------------------------------------- tray gear
    items = []

    def tray(key, obj, x, y, rot=0.0, lift=0.0):
        obj.name = f'item_{key}'
        place_on_tray(obj, x, y, rot, lift)
        items.append(obj)

    tray('shotgun', P.pump_shotgun('p'), -2.08, 0.02, 68)
    tray('sawed_off', P.sawed_off('p'), -2.36, -0.44, 88)
    tray('ammo_can', P.ammo_can('p'), -1.80, 0.50, 90)
    tray('ammo_can_2', P.ammo_can('p', (0.24, 0.12, 0.15)), -1.79, -0.53, 90)
    tray('rock_salt', P.shells_box('p', (5, 4), 'shell_red'), -2.28, 0.44, 0)
    tray('silver_bullets', P.bullets_box('p'), -2.40, 0.15, 10)
    tray('bandolier', P.bandolier('p'), -1.95, -0.28, 84)
    tray('holy_water', P.bottle('p', 0.15, 0.04, 0.012, 'bottle_glass', 'gunmetal', flat=True), -1.78, 0.18, 20)
    tray('holy_water_2', P.bottle('p', 0.13, 0.035, 0.011, 'bottle_glass', 'brass', flat=True), -1.76, 0.07, -15)
    tray('dead_mans_blood', P.jar('p', 0.09, 0.03, 'blood_glass', 'brass'), -1.74, -0.06)
    tray('salt', P.can('p', 0.12, 0.045, 'salt_blue', 'steel'), -1.76, -0.30)
    tray('holy_oil', P.jar('p', 0.08, 0.035, 'oil_glass', 'brass'), -1.85, -0.37)
    tray('flashlight', P.flashlight('p'), -2.42, -0.12, 92)
    tray('flashlight_2', P.flashlight('p', 0.24, 0.018), -2.38, 0.02, 80)
    tray('fake_ids', P.badge_wallet('p'), -2.30, 0.26, 12)
    tray('fake_ids_2', P.badge_wallet('p'), -2.27, 0.30, -8, lift=0.013)
    tray('journal', P.journal('p'), -2.18, 0.56, 6)
    tray('emf', P.emf('p'), -2.08, -0.55, 80)
    tray('lighter_fluid', P.lighter_fluid('p'), -1.86, -0.12, 0)
    tray('crowbar', P.crowbar('p'), -2.45, 0.30, 92)
    tray('rope', P.rope('p'), -1.95, 0.30)
    tray('chain', P.chain('p'), -2.19, -0.14, 90)
    tray('duct_tape', P.duct_tape('p'), -2.00, -0.52)
    tray('hex_bag', P.hex_bag('p'), -1.92, 0.54)
    tray('machete', P.machete('p'), -2.13, 0.40, 96)
    tray('lock_picks', P.lockpicks('p'), -2.36, -0.24, 5)
    tray('flares', P.flare('p'), -2.22, 0.08, 95)
    # the Colt in its wooden case
    case = P.box_prop('colt_case', (0.40, 0.17, 0.045), 'wood_dark')
    felt = L.box('colt_felt', (0.38, 0.15, 0.004), (0, 0, 0.046), 'felt_red')
    gun = P.colt('colt_gun')
    gun.data.transform(Matrix.Translation((0.03, 0.02, 0.066)))
    rounds = []
    for i in range(6):
        rounds.append(L.cylinder('colt_round', 0.005, 0.028, (-0.14 + 0.02 * i, -0.05, 0.052), axis='Y',
                                 segments=8, mat='brass'))
    case = L.join([case, felt, gun] + rounds, 'colt')
    tray('colt', case, -2.26, -0.03, 90)

    # ---------------------------------------------------------------- the false floor
    board = L.box('false_floor', (BOARD_LEN, BOARD_W, BOARD_T), (HINGE_X - BOARD_LEN / 2, 0, BOARD_Z),
                  'carpet', bevel=0.004)
    felt = L.box('false_floor_felt', (BOARD_LEN - 0.02, BOARD_W - 0.02, 0.002),
                 (HINGE_X - BOARD_LEN / 2, 0, BOARD_Z - BOARD_T / 2 - 0.0008), 'felt')
    board = L.join([board, felt], 'false_floor')
    L.set_origin(board, (HINGE_X, 0, BOARD_Z))

    mounted = []

    def mount(key, obj, u, h, theta=0.0):
        obj.name = f'item_{key}'
        place_on_board(obj, u, h, theta)
        mounted.append(obj)

    mount('arrow', P.arrow('p'), 0.0, 0.72, 0)
    mount('bowie', P.knife('p', 0.36, 0.62, 0.04, 'leather'), -0.26, 0.60, -8)
    mount('sage', P.sage('p'), -0.52, 0.56, 28)
    mount('stake', P.stake('p', 0.32), -0.60, 0.26, 96)
    mount('hatchet', P.hatchet('p'), -0.40, 0.25, 84)
    mount('brass_knuckles', P.knuckles('p'), -0.20, 0.40, 0)
    mount('silver_knife', P.knife('p', 0.28, 0.6, 0.03, 'wood', blade_mat='silver'), -0.02, 0.52, 2)
    mount('sheath_knife', P.sheath_knife('p'), -0.02, 0.24, 92)
    mount('ruby_knife', P.ruby_knife('p'), 0.17, 0.32, 88)
    mount('angel_blade', P.angel_blade('p'), 0.22, 0.62, 4)
    mount('cross', P.cross('p'), 0.42, 0.44, 90)
    mount('holster', P.holster('p'), 0.30, 0.10, 90)
    mount('pouch', P.pouch('p'), 0.55, 0.14, 0)
    mount('dreamcatcher', P.dreamcatcher('p'), 0.62, 0.52, 0)
    mount('rosary', P.rosary('p'), 0.64, 0.30, 0)
    mount('stake_2', P.stake('p', 0.26), 0.08, 0.10, 4)
    # nylon straps holding things to the felt
    straps = []
    for (u, h, w, th) in ((0.0, 0.72, 0.03, 90), (-0.26, 0.6, 0.05, 82), (-0.4, 0.28, 0.04, -6), (0.17, 0.3, 0.04, 0),
                          (0.42, 0.44, 0.05, 0), (-0.6, 0.26, 0.04, 6), (-0.02, 0.24, 0.05, 2)):
        s = L.box('strap', (w, 0.024, 0.006), (0, 0, 0.003), 'strap')
        place_on_board(s, u, h, th)
        s.location.z -= 0.012
        L.bake_transform(s)
        straps.append(s)
    L.join(straps, 'false_floor_straps')
    for o in mounted + [bpy.data.objects['false_floor_straps']]:
        o.parent = board
        o.matrix_parent_inverse = board.matrix_world.inverted()
    return items, mounted
