"""The hunter's arsenal in Baby's trunk.

- a bulkhead closing the trunk off from the rear seat
- a grey-carpeted tray with the gear laid out in it
- the hinged false floor ('false_floor'): black carpet on top, a pegboard on
  its underside with the weapons hung on pegs and spring clips; it lifts to
  stand upright. Contact shadows are baked into the pegboard (bake.py)
- 'trunk_lid_inner': the underside of the lid, UV-mapped for the painted
  Devil's Trap (the texture itself is painted at runtime)

Items are named 'item_<key>'; the web app maps keys to names and lore.
"""
import math
import os
import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import lib as L
import props as P
import phprops as PH
import bake as B

HINGE_X = -1.665
BOARD_Z = 0.612          # board centre plane (closed)
BOARD_T = 0.02
BOARD_LEN = 0.80
BOARD_W = 1.44
TRAY_X = (-2.47, -1.68)
TRAY_Y = 0.70

# the pegboard panel on the false floor's underside (1/4" hardboard)
PEG_T = 0.0064
PEG_Z = BOARD_Z - BOARD_T / 2 - PEG_T
PANEL_W, PANEL_L = 1.42, 0.78
# its hole grid, as painted by tools/prop_textures.py (from the panel's hinge-side left corner)
PITCH = 0.0254
HOLE_X0, HOLE_Y0, HOLE_NX, HOLE_NY = 0.0242, 0.0217, 55, 30
PEG_R = 0.0022
TEX = PH.TEX


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
    o.location = (HINGE_X - h, -u, PEG_Z - 0.0002)
    L.bake_transform(o)
    return o


def board_point(u, h, n=0.0):
    """A point in front of the closed board: u to the viewer's right, h up
    from the hinge (as it stands), n out from the pegboard face."""
    return Vector((HINGE_X - h, -u, PEG_Z - n))


def hole_u(u, side=0):
    """u of the hole column nearest u (side -1 / +1: the next one out that way)."""
    x = (u + PANEL_W / 2 - HOLE_X0) / PITCH
    i = math.floor(x) if side < 0 else math.ceil(x) if side > 0 else round(x)
    return HOLE_X0 + min(max(i, 0), HOLE_NX - 1) * PITCH - PANEL_W / 2


def hole_h(h, below=True):
    y = (h - 0.01 - HOLE_Y0) / PITCH
    j = math.floor(y) if below else round(y)
    return HOLE_Y0 + min(max(j, 0), HOLE_NY - 1) * PITCH + 0.01


def extent(o):
    us = [-v.co.y for v in o.data.vertices]
    hs = [HINGE_X - v.co.x for v in o.data.vertices]
    return min(us), max(us), min(hs), max(hs)


class Probe:
    """Rays shot at the board through one item: where its outline and its
    front surface are, in board coordinates."""

    def __init__(self, o):
        self.tree = BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())

    def front(self, u, h):
        loc = self.tree.ray_cast(board_point(u, h, 0.3), Vector((0, 0, 1)), 0.35)[0]
        return None if loc is None else PEG_Z - loc.z

    def front_max(self, u, h, du=0.0, dh=0.0):
        best = None
        for k in range(-2, 3):
            f = self.front(u + du * k / 2, h + dh * k / 2)
            if f is not None and (best is None or f > best):
                best = f
        return best

    def _edge(self, fn, a, b):
        """refine the boundary between a (miss) and b (hit)"""
        for _ in range(10):
            m = (a + b) / 2
            if fn(m) is None:
                a = m
            else:
                b = m
        return b

    def bottom(self, u, lo, hi):
        """lowest h where the item is at column u (scanning up from lo)"""
        h = lo
        while h <= hi:
            if self.front(u, h) is not None:
                return self._edge(lambda x: self.front(u, x), h - 0.001, h)
            h += 0.001
        return None

    def inner_top(self, u, lo, hi):
        """scanning down from hi: where the first solid run ends (the inside
        of a loop's top)"""
        h, run = hi, False
        while h >= lo:
            hit = self.front(u, h) is not None
            if hit:
                run = True
            elif run:
                return self._edge(lambda x: self.front(u, x), h, h + 0.001)
            h -= 0.001
        return None

    def span_u(self, h, lo, hi):
        us = [lo + (hi - lo) * i / 200 for i in range(201)]
        hits = [u for u in us if self.front(u, h) is not None]
        return (min(hits), max(hits)) if hits else None

    def span_h(self, u, lo, hi):
        hs = [lo + (hi - lo) * i / 200 for i in range(201)]
        hits = [x for x in hs if self.front(u, x) is not None]
        return (min(hits), max(hits)) if hits else None


def peg(u, h, reach):
    """An L-shaped pegboard hook in the hole at (u, h): straight out of the
    board by `reach`, then turned up in front of what it holds."""
    rb = 0.005
    pts = [board_point(u, h, -0.004), board_point(u, h, reach - rb)]
    for k in range(1, 6):
        a = (math.pi / 2) * k / 5
        pts.append(board_point(u, h + rb * (1 - math.cos(a)), reach - rb + rb * math.sin(a)))
    pts.append(board_point(u, h + 0.017, reach))
    return L.sweep('peg', pts, P._circle(PEG_R, 8), 'steel')


def clip(pr, at_u, at_h, along):
    """A spring-steel clip across an item: a band hugging its front surface,
    screwed to the board either side. `along`: the item's axis ('u' / 'h')."""
    step = 0.0015
    ts = [step * i for i in range(-45, 46)]
    pos = (lambda t: (at_u + t, at_h)) if along == 'h' else (lambda t: (at_u, at_h + t))
    band = (0.0, 0.004) if along == 'h' else (0.004, 0.0)
    hs = [pr.front_max(*pos(t), du=band[1], dh=band[0]) for t in ts]
    hit = [i for i, x in enumerate(hs) if x is not None]
    if not hit:
        return []
    # the solid run nearest the station
    runs, cur = [], [hit[0]]
    for i in hit[1:]:
        if i == cur[-1] + 1:
            cur.append(i)
        else:
            runs.append(cur)
            cur = [i]
    runs.append(cur)
    run = min(runs, key=lambda r: min(abs(ts[i]) for i in r))
    i0, i1 = run[0], run[-1]
    env = [max(hs[j] for j in range(max(i0, i - 2), min(i1, i + 2) + 1)) for i in range(i0, i1 + 1)]
    lift = 0.0013
    path2 = [(ts[i0] - 0.008, 0.0007), (ts[i0] - 0.0025, env[0] * 0.8 + lift)]
    path2 += [(ts[i0 + k], env[k] + lift) for k in range(0, i1 - i0 + 1, 2)]
    path2 += [(ts[i1] + 0.0025, env[-1] * 0.8 + lift), (ts[i1] + 0.008, 0.0007)]
    pts = L.catmull([board_point(*pos(t), n) for t, n in path2], 3)
    side = Vector((-1, 0, 0)) if along == 'h' else Vector((0, -1, 0))
    b = L.sweep('clip', pts, [(-0.004, -0.0006), (0.004, -0.0006), (0.004, 0.0006), (-0.004, 0.0006)], 'steel',
                fixed_side=side, smooth=False)
    parts = [b]
    for t in (ts[i0] - 0.0085, ts[i1] + 0.0085):
        c = board_point(*pos(t), 0.0008)
        parts.append(L.cylinder('screw', 0.0034, 0.0016, tuple(c), axis='Z', segments=10, mat='steel', bevel=0.0005))
    return parts


def fix(o, spec):
    """Hang item o on the board: pegs under it ('rest', 'flank'), a peg in a
    loop ('hang'), spring clips across it ('clip'). Items move down onto
    their pegs, so pegs sit in real holes. Returns the hardware."""
    out = []
    umin, umax, hmin, hmax = extent(o)
    uc = (umin + umax) / 2
    pr = Probe(o)
    rests = []
    for f in spec:
        if f[0] == 'rest':
            rests += [hole_u(uc + du) for du in f[1]]
        elif f[0] == 'flank':
            sp = pr.span_u(hmin + 0.15 * (hmax - hmin), umin, umax)
            if sp:
                rests += [hole_u(sp[0] - 0.0045 - PEG_R, -1), hole_u(sp[1] + 0.0045 + PEG_R, 1)]
        elif f[0] == 'hang':
            dus = f[1] if isinstance(f[1], (tuple, list)) else (f[1],)
            cols = [hole_u(uc + du) for du in dus]
            tops = [(uu, pr.inner_top(uu, hmin, hmax + 0.002)) for uu in cols]
            tops = [(uu, t) for uu, t in tops if t is not None]
            if tops:
                t0 = tops[0][1]
                row = hole_h(t0 - PEG_R, below=False)
                sft = t0 - PEG_R - row
                o.data.transform(Matrix.Translation((sft, 0, 0)))
                pr = Probe(o)
                for uu, t in tops:
                    reach = (pr.front_max(uu, t - sft + 0.003, du=0.004) or 0.01) + 0.004
                    out.append(peg(uu, row + (t - t0), reach))
                umin, umax, hmin, hmax = extent(o)
    if rests:
        found = []
        for uu in rests:
            hb = pr.bottom(uu, hmin - 0.002, hmax)
            if hb is not None:
                hp = hb - PEG_R - 0.0002
                found.append((uu, hb, hole_h(hp), hp - hole_h(hp)))
        if found:
            s = min(f[3] for f in found)
            o.data.transform(Matrix.Translation((s, 0, 0)))
            pr = Probe(o)
            for uu, hb, row, _ in found:
                reach = (pr.front_max(uu, hb - s + 0.004, dh=0.006) or 0.01) + 0.004
                out.append(peg(uu, row, reach))
            umin, umax, hmin, hmax = extent(o)
    for f in spec:
        if f[0] != 'clip':
            continue
        vertical = (hmax - hmin) > (umax - umin)
        for fr in f[1]:
            if vertical:
                at_h = hmin + fr * (hmax - hmin)
                sp = pr.span_u(at_h, umin, umax)
                if sp:
                    out += clip(pr, (sp[0] + sp[1]) / 2, at_h, 'h')
            else:
                at_u = umin + fr * (umax - umin)
                sp = pr.span_h(at_u, hmin, hmax)
                if sp:
                    out += clip(pr, at_u, (sp[0] + sp[1]) / 2, 'u')
    return out


def pegboard_material(col_path):
    mat = bpy.data.materials.new('pegboard')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    col = nt.nodes.new('ShaderNodeTexImage')
    col.image = bpy.data.images.load(col_path, check_existing=True)
    nt.links.new(col.outputs['Color'], bsdf.inputs['Base Color'])
    nor = nt.nodes.new('ShaderNodeTexImage')
    nor.image = bpy.data.images.load(os.path.join(TEX, 'pegboard_nor.png'), check_existing=True)
    nor.image.colorspace_settings.name = 'Non-Color'
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(nor.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = 0.72
    return mat, col


def pegboard_panel():
    """The pegboard face as one quad (its UVs map the pegboard image 1:1, so
    contact shadows can be baked straight into it) plus the board's edge."""
    x_hi, x_lo = HINGE_X - 0.01, HINGE_X - 0.01 - PANEL_L
    y = PANEL_W / 2
    verts = [(x_hi, y, PEG_Z), (x_hi, -y, PEG_Z), (x_lo, -y, PEG_Z), (x_lo, y, PEG_Z)]
    face = L.mesh_object('false_floor_peg', verts, [(0, 1, 2, 3)], None, smooth=True)
    uv = face.data.uv_layers.new(name='UVMap')
    for lp in face.data.loops:
        co = face.data.vertices[lp.vertex_index].co
        uv.data[lp.index].uv = ((-co.y + y) / PANEL_W, (x_hi - co.x) / PANEL_L)
    mat, _ = pegboard_material(os.path.join(TEX, 'pegboard_col.png'))
    face.data.materials.append(mat)
    edge = L.box('false_floor_edge', (PANEL_L, PANEL_W, PEG_T - 0.0004), ((x_hi + x_lo) / 2, 0, PEG_Z + 0.0004 + (PEG_T - 0.0004) / 2),
                 'wood_dark', bevel=0.0015)
    PH.texturize(edge)
    return face, edge


def pivot(name, mesh):
    """An empty at `mesh`'s hinge that the mesh (and everything else that
    swings with it) hangs from. Keeps the hinge objects mesh-free: three's
    OutlinePass hides every unselected mesh while it draws its mask, and a
    hidden mesh takes its children (the gear, the painted trap) with it."""
    e = bpy.data.objects.new(name, None)
    L.link(e)
    e.matrix_world = mesh.matrix_world.copy()
    mesh.parent = e
    mesh.matrix_parent_inverse = e.matrix_world.inverted()
    return e


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
    # ride with the lid: both hang from a 'trunk_lid' pivot at the hinge
    lid.name = 'trunk_lid_panel'
    piv = pivot('trunk_lid', lid)
    o.parent = piv
    o.matrix_parent_inverse = piv.matrix_world.inverted()
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
                                                        'bolt_action_rifle_7_62_trigger', 'bolt_action_rifle_7_62_wrap'], tex_size=512)
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
    slab = L.box('false_floor_board', (BOARD_LEN, BOARD_W, BOARD_T), (HINGE_X - BOARD_LEN / 2, 0, BOARD_Z),
                 'carpet', bevel=0.004)
    PH.texturize(slab)
    L.set_origin(slab, (HINGE_X, 0, BOARD_Z))
    board = pivot('false_floor', slab)
    panel, edge = pegboard_panel()

    # the gear on the pegboard, laid out like a tool board: long pieces across
    # the top, blades standing in a row, the small stuff along the bottom.
    # u: to the viewer's right, h: up from the hinge, theta: in-plane angle
    mounted, hardware = [], []

    def put(key, obj, u, h, theta, spec, flat_it=True, stretch=None):
        o = mount(key, obj, u, h, theta, flat_it=flat_it, stretch=stretch)
        hardware.extend(fix(o, spec))
        mounted.append(o)

    put('machete', PH.import_ph('machete', tex_size=1024), -0.12, 0.728, 0, [('rest', (-0.27, 0.2)), ('clip', (0.07,))])
    put('arrow', P.arrow('p'), -0.12, 0.645, 0, [('rest', (-0.25, 0.25))], flat_it=False)
    put('dreamcatcher', P.dreamcatcher('p'), 0.44, 0.60, 0, [('hang', 0.0)], flat_it=False)
    put('crowbar', PH.import_ph('crowbar_01'), 0.625, 0.45, 90, [('clip', (0.25, 0.7))])
    put('sage', P.sage('p'), -0.625, 0.645, 90, [('clip', (0.3, 0.72))], flat_it=False)
    put('hatchet', PH.import_ph('hatchet'), -0.605, 0.335, 90, [('flank',), ('clip', (0.2,))])
    put('bowie', P.bowie('p'), -0.495, 0.35, 90, [('flank',), ('clip', (0.14,))])
    put('silver_knife', PH.import_ph('fish_knife'), -0.405, 0.295, 90, [('flank',), ('clip', (0.2,))], stretch=(1.3, 0.9))
    put('ruby_knife', P.ruby_knife('p'), -0.325, 0.33, 90, [('flank',), ('clip', (0.14,))])
    put('angel_blade', P.angel_blade('p'), -0.245, 0.37, 90, [('clip', (0.14, 0.52))], flat_it=False)
    put('stake', P.stake('p', 0.32, seed=1), -0.17, 0.335, 90, [('clip', (0.22, 0.6))], flat_it=False)
    put('stake_2', P.stake('p', 0.28, seed=4), -0.12, 0.315, 90, [('clip', (0.22, 0.6))], flat_it=False)
    put('hammer', PH.import_ph('cross_pein_hammer'), -0.03, 0.335, 90, [('flank',), ('clip', (0.2,))])
    put('cross', P.cross('p'), 0.15, 0.35, 90, [('rest', (-0.07, 0.07))], flat_it=False)
    pistol = PH.import_ph('service_pistol', keep=['service_pistol_pistol_a', 'service_pistol_slide_a', 'service_pistol_hammer_a',
                                                  'service_pistol_trigger_a'], decimate=0.45)
    put('pistol', pistol, 0.40, 0.335, 0, [('clip', (0.3, 0.82))])
    put('brass_knuckles', P.knuckles('p'), 0.40, 0.205, 0, [('hang', -0.0125)], flat_it=False)
    put('flares', P.flare('p'), -0.50, 0.09, 0, [('rest', (-0.06, 0.06)), ('clip', (0.5,))], flat_it=False)
    put('chain', P.hanging_chain('p'), -0.12, 0.085, 0, [('hang', (-0.115, 0.115))], flat_it=False)
    put('hex_bag', P.hex_bag('p'), 0.30, 0.085, 0, [('rest', (0.0,))], flat_it=False)
    put('rosary', P.rosary('p'), 0.53, 0.10, 90, [('hang', 0.0)], flat_it=False)
    hooks = L.join(hardware, 'false_floor_hooks')
    PH.texturize(hooks)
    for o in mounted + [hooks, panel, edge]:
        o.parent = board
        o.matrix_parent_inverse = board.matrix_world.inverted()

    # contact shadows into the pegboard: a lamp up and to the left, low enough
    # (about 50 degrees off the board) that the drop shadows show past the gear
    baked = os.path.join(TEX, 'pegboard_baked.png')
    if not os.environ.get('BABY_NO_BAKE'):
        B.contact_shadows(panel, board, os.path.join(TEX, 'pegboard_col.png'), baked,
                          light_dir=(-0.7, 0.3, -0.64), ao_dist=0.03, ao_strength=0.7, shadow_strength=0.55)
    if os.path.exists(baked):
        for n in panel.data.materials[0].node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image and n.image.name.startswith('pegboard_col'):
                n.image = bpy.data.images.load(baked, check_existing=True)
                print('pegboard colour ->', n.image.name)
    return items, mounted
