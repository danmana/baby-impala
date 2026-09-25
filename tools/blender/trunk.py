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
import phprops as PH

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


def flat(o):
    """Orient mesh data so its longest extent runs along X and its thinnest
    along Z (lying flat / pressed flat against the felt)."""
    size = PH.size_of(o)
    order = sorted(range(3), key=lambda i: -size[i])  # long, mid, thin
    axes = [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))]
    M = Matrix((axes[order[0]], axes[order[1]], axes[order[2]])).to_4x4()
    if M.determinant() < 0:
        M = Matrix((axes[order[0]], -axes[order[1]], axes[order[2]])).to_4x4()
    o.data.transform(M)
    return o


def lay(key, obj, x, y, rz=0.0, lift=0.0, flat_it=True):
    obj.name = f'item_{key}'
    obj.data.name = f'item_{key}'
    if flat_it:
        flat(obj)
    PH.texturize(obj)
    place_on_tray(obj, x, y, rz, lift)
    return obj


def mount(key, obj, u, h, theta=0.0, flat_it=True, stretch=None):
    """stretch: (across, thickness) scale after flattening, to broaden a blade."""
    obj.name = f'item_{key}'
    obj.data.name = f'item_{key}'
    if flat_it:
        flat(obj)
    if stretch:
        obj.data.transform(Matrix.Diagonal((1.0, stretch[0], stretch[1], 1.0)))
    PH.texturize(obj)
    place_on_board(obj, u, h, theta)
    return obj


def build(fa=None, ra=None):
    L.set_collection('Baby')
    lid_inner()

    # bulkhead between the rear seat back and the trunk
    bh = L.box('trunk_bulkhead', (0.02, 1.62, 0.66), (-1.62, 0, 0.40 + 0.33), 'felt')
    PH.texturize(bh)

    # tray: bottom follows the sloped floor, grey carpet, low dividers
    x0, x1 = TRAY_X
    sec = []
    for x in (x0, x1):
        z = floor_z(x) + 0.008
        sec.append([Vector((x, -TRAY_Y, z)), Vector((x, TRAY_Y, z))])
    tray = L.loft('trunk_tray', sec, mat='carpet_gray', flip=True)
    parts = [tray]
    for yy in (-0.27, 0.27):
        parts.append(L.box('tray_div', (0.37, 0.02, 0.07), (-1.89, yy, floor_z(-1.89) + 0.04), 'carpet_gray', bevel=0.004))
    parts.append(L.box('tray_div', (0.02, 2 * TRAY_Y, 0.06), (-2.085, 0, floor_z(-2.085) + 0.035), 'carpet_gray', bevel=0.004))
    for yy in (-TRAY_Y, TRAY_Y):
        parts.append(L.box('tray_wall', (x1 - x0, 0.02, 0.2), ((x0 + x1) / 2, yy, floor_z((x0 + x1) / 2) + 0.1), 'carpet_gray'))
    tray = L.join(parts, 'trunk_tray')
    PH.texturize(tray)

    items = []
    # ---------------------------------------------------------------- long guns across the rear
    rifle = PH.import_ph('bolt_action_rifle_7_62', keep=['bolt_action_rifle_7_62', 'bolt_action_rifle_7_62_bolt_a',
                                                        'bolt_action_rifle_7_62_trigger', 'bolt_action_rifle_7_62_wrap'], tex_size=1024)
    items.append(lay('rifle', rifle, -2.36, 0.0, 90))
    items.append(lay('shotgun', P.pump_shotgun('p'), -2.19, -0.07, 90))
    items.append(lay('bandolier', P.bandolier('p'), -2.17, -0.20, 94, lift=0.035, flat_it=False))
    items.append(lay('sawed_off', P.sawed_off('p'), -2.19, 0.52, 93))
    items.append(lay('emf', P.emf('p'), -2.265, 0.44, 88, flat_it=False))
    items.append(lay('lock_picks', P.lockpicks('p'), -2.28, -0.62, 90, flat_it=False))

    # ---------------------------------------------------------------- front-left: ammo and salt
    ammo = PH.import_ph('ammo_box')
    items.append(lay('ammo_can', ammo, -1.775, 0.49, 0, flat_it=False))
    ammo2 = PH.import_ph('ammo_box')
    ammo2.data.transform(Matrix.Scale(0.92, 4))
    items.append(lay('ammo_can_2', ammo2, -1.885, 0.49, 0, flat_it=False))
    salt = PH.import_ph('russian_food_cans_01', keep=['russian_food_cans_01_salt_box'])
    salt.data.transform(Matrix.Scale(1.6, 4))
    items.append(lay('salt', salt, -2.02, 0.34, 20, flat_it=False))
    items.append(lay('rock_salt', P.shells_box('p', (5, 4), 'shell_red'), -2.00, 0.55, 0, flat_it=False))

    # ---------------------------------------------------------------- centre: the Colt, the journal, IDs
    case = P.box_prop('colt_case', (0.40, 0.17, 0.045), 'wood_dark')
    felt = L.box('colt_felt', (0.38, 0.15, 0.004), (0, 0, 0.046), 'felt_red')
    gun = P.colt('colt_gun')
    # lay it on its side in the case (the profile faces up)
    gun.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'X'))
    gun.data.transform(Matrix.Translation((-0.05, 0.035, 0.062)))
    # the thirteen rounds in two rows under the barrel, clear of the grip
    rounds = [L.cylinder('colt_round', 0.0055, 0.03, (0.0 + 0.022 * i, -0.029, 0.052), axis='Y', segments=10, mat='silver')
              for i in range(7)]
    rounds += [L.cylinder('colt_round', 0.0055, 0.03, (0.011 + 0.022 * i, -0.061, 0.052), axis='Y', segments=10, mat='silver')
               for i in range(6)]
    case = L.join([case, felt, gun] + rounds, 'colt')
    # grip towards the back of the car, so from behind it reads as a gun lying in its case
    items.append(lay('colt', case, -1.985, -0.03, -90, flat_it=False))
    journal = PH.import_ph('binder_notebook', keep=['binder_notebook_closed'], tex_size=1024)
    items.append(lay('journal', journal, -1.80, 0.15, 84, flat_it=False))
    items.append(lay('silver_bullets', P.bullets_box('p'), -1.785, -0.035, 4, flat_it=False))
    items.append(lay('fake_ids', P.badge_wallet('p'), -1.795, -0.14, 12, flat_it=False))
    items.append(lay('fake_ids_2', P.badge_wallet('p'), -1.79, -0.15, -9, lift=0.013, flat_it=False))
    items.append(lay('duct_tape', P.duct_tape('p'), -1.80, -0.225, 0, flat_it=False))

    # ---------------------------------------------------------------- front-right: light, water, jars
    torch = PH.import_ph('vintage_flashlight', decimate=0.6)
    items.append(lay('flashlight', torch, -1.80, -0.49, 0, flat_it=False))
    bottle = PH.import_ph('wine_bottles_01', keep=['wine_bottles_01_alsace'], decimate=0.5)
    items.append(lay('holy_water', bottle, -1.955, -0.47, 90))
    items.append(lay('dead_mans_blood', P.jar('p', 0.09, 0.03, 'blood_glass', 'brass'), -2.04, -0.63, flat_it=False))
    items.append(lay('holy_oil', P.jar('p', 0.08, 0.035, 'oil_glass', 'brass'), -2.04, -0.31, flat_it=False))
    items.append(lay('lighter_fluid', P.lighter_fluid('p'), -2.035, -0.47, 90, flat_it=False))

    # ---------------------------------------------------------------- the false floor
    board = L.box('false_floor', (BOARD_LEN, BOARD_W, BOARD_T), (HINGE_X - BOARD_LEN / 2, 0, BOARD_Z),
                  'carpet', bevel=0.004)
    felt = L.box('false_floor_felt', (BOARD_LEN - 0.02, BOARD_W - 0.02, 0.002),
                 (HINGE_X - BOARD_LEN / 2, 0, BOARD_Z - BOARD_T / 2 - 0.0008), 'felt')
    board = L.join([board, felt], 'false_floor')
    PH.texturize(board)
    L.set_origin(board, (HINGE_X, 0, BOARD_Z))

    mounted = []
    machete = PH.import_ph('machete', tex_size=1024)
    mounted.append(mount('machete', machete, 0.02, 0.70, 0))
    mounted.append(mount('arrow', P.arrow('p'), -0.02, 0.61, 2, flat_it=False))
    hatchet = PH.import_ph('hatchet')
    # lying across the board, head to the left, parallel to the board's edges
    mounted.append(mount('hatchet', hatchet, -0.565, 0.36, 180))
    mounted.append(mount('ruby_knife', P.ruby_knife('p'), -0.33, 0.30, 90))
    knife = PH.import_ph('fish_knife')
    mounted.append(mount('silver_knife', knife, -0.225, 0.40, 88, stretch=(1.3, 0.9)))
    mounted.append(mount('bowie', P.bowie('p'), 0.06, 0.44, 92))
    mounted.append(mount('angel_blade', P.angel_blade('p'), -0.12, 0.47, 90))
    mounted.append(mount('stake', P.stake('p', 0.32), -0.02, 0.19, 88))
    mounted.append(mount('stake_2', P.stake('p', 0.28), 0.04, 0.17, 93))
    mounted.append(mount('cross', P.cross('p'), 0.21, 0.36, 90, flat_it=False))
    crowbar = PH.import_ph('crowbar_01')
    mounted.append(mount('crowbar', crowbar, 0.62, 0.36, 90))
    pistol = PH.import_ph('service_pistol', keep=['service_pistol_pistol_a', 'service_pistol_slide_a', 'service_pistol_hammer_a',
                                                  'service_pistol_trigger_a'], decimate=0.45)
    mounted.append(mount('pistol', pistol, 0.40, 0.16, 0))
    mounted.append(mount('sage', P.sage('p'), -0.52, 0.62, 25, flat_it=False))
    mounted.append(mount('brass_knuckles', P.knuckles('p'), 0.42, 0.50, 0, flat_it=False))
    mounted.append(mount('dreamcatcher', P.dreamcatcher('p'), 0.44, 0.63, 0, flat_it=False))
    mounted.append(mount('rosary', P.rosary('p'), 0.18, 0.12, 0, flat_it=False))
    mounted.append(mount('hex_bag', P.hex_bag('p'), -0.52, 0.10, 0, flat_it=False))
    mounted.append(mount('flares', P.flare('p'), -0.30, 0.08, 0))
    mounted.append(mount('chain', P.chain('p', 10), -0.14, 0.08, 0, flat_it=False))
    # nylon straps holding things to the felt
    straps = []
    for (u, hh, w, th) in ((0.02, 0.70, 0.03, 90), (-0.48, 0.36, 0.05, 90), (-0.33, 0.30, 0.04, 0), (0.62, 0.36, 0.04, 0),
                           (-0.02, 0.18, 0.05, 0), (0.21, 0.36, 0.05, 0), (0.40, 0.16, 0.05, 90), (-0.225, 0.40, 0.04, 0)):
        st = L.box('strap', (w, 0.024, 0.006), (0, 0, 0.003), 'strap')
        place_on_board(st, u, hh, th)
        st.location.z -= 0.014
        L.bake_transform(st)
        straps.append(st)
    straps = L.join(straps, 'false_floor_straps')
    PH.texturize(straps)
    for o in mounted + [straps]:
        o.parent = board
        o.matrix_parent_inverse = board.matrix_world.inverted()
    return items, mounted
