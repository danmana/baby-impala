"""Cut the one-piece body shell into separate panels (hood, trunk lid, four
doors) along Baby's real shut lines, so they can open and explode apart.

The source body is a single low-poly shell, so instead of booleans we bisect
it with the planes that bound each panel and then hand every face whose
centre falls inside a panel's volume to that panel. Small trim pieces
(handles, locks, side mouldings, window cranks) follow the panel they sit on.
"""
import math
import bmesh
import bpy
from mathutils import Vector, Matrix
import lib as L

# shut lines measured from the model's baked panel gaps (metres, car space)
X_DOOR_F = 0.937
X_BLINE = -0.02
X_DOOR_R = -0.984
Z_DOOR_BOT = 0.30
Z_DOOR_TOP = 1.13
Y_DOOR_IN = 0.76
# rear door's lower back corner curves round the wheel arch: approximated by
# a slanted line from (X_DOOR_R, 0.60) down to (-0.80, Z_DOOR_BOT)
ARCH_A = (X_DOOR_R, 0.60)
ARCH_B = (-0.80, Z_DOOR_BOT)

X_HOOD_R = 1.13
X_HOOD_F = 2.63
Y_HOOD = 0.84
Z_HOOD = 0.725

X_TRUNK_F = -1.56
Y_TRUNK = 0.80
Z_TRUNK = 0.815


def arch_side(x, z):
    """> 0 when (x, z) is in front of the rear door's slanted lower rear edge."""
    (x0, z0), (x1, z1) = ARCH_A, ARCH_B
    return (x1 - x0) * (z - z0) - (z1 - z0) * (x - x0)


def in_door(c, front, rear, side):
    if side * c.y < Y_DOOR_IN or not (Z_DOOR_BOT < c.z < Z_DOOR_TOP):
        return False
    if not (rear < c.x < front):
        return False
    if rear == X_DOOR_R and c.z < ARCH_A[1] and arch_side(c.x, c.z) < 0:
        return False
    return True


REGIONS = {
    'door_fl': lambda c: in_door(c, X_DOOR_F, X_BLINE, 1),
    'door_fr': lambda c: in_door(c, X_DOOR_F, X_BLINE, -1),
    'door_rl': lambda c: in_door(c, X_BLINE, X_DOOR_R, 1),
    'door_rr': lambda c: in_door(c, X_BLINE, X_DOOR_R, -1),
    'hood': lambda c: X_HOOD_R < c.x < X_HOOD_F and abs(c.y) < Y_HOOD and c.z > Z_HOOD,
    'trunk_lid': lambda c: c.x < X_TRUNK_F and abs(c.y) < Y_TRUNK and c.z > Z_TRUNK,
}

PIVOTS = {
    'door_fl': (X_DOOR_F, 1.0, 0.7), 'door_fr': (X_DOOR_F, -1.0, 0.7),
    'door_rl': (X_BLINE, 1.0, 0.7), 'door_rr': (X_BLINE, -1.0, 0.7),
    'hood': (X_HOOD_R + 0.02, 0.0, 0.98),
    'trunk_lid': (X_TRUNK_F - 0.025, 0.0, 1.10),  # top-front edge: swings clear of the body and glass
}


def bisect(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    planes = [
        ((X_DOOR_F, 0, 0), (1, 0, 0)), ((X_BLINE, 0, 0), (1, 0, 0)), ((X_DOOR_R, 0, 0), (1, 0, 0)),
        ((0, 0, Z_DOOR_BOT), (0, 0, 1)), ((0, 0, Z_DOOR_TOP), (0, 0, 1)),
        ((0, Y_DOOR_IN, 0), (0, 1, 0)), ((0, -Y_DOOR_IN, 0), (0, 1, 0)),
        ((X_HOOD_R, 0, 0), (1, 0, 0)), ((X_HOOD_F, 0, 0), (1, 0, 0)),
        ((0, Y_HOOD, 0), (0, 1, 0)), ((0, -Y_HOOD, 0), (0, 1, 0)), ((0, 0, Z_HOOD), (0, 0, 1)),
        ((X_TRUNK_F, 0, 0), (1, 0, 0)), ((0, Y_TRUNK, 0), (0, 1, 0)), ((0, -Y_TRUNK, 0), (0, 1, 0)),
        ((0, 0, Z_TRUNK), (0, 0, 1)),
    ]
    # slanted rear-door edge
    (x0, z0), (x1, z1) = ARCH_A, ARCH_B
    d = Vector((x1 - x0, 0, z1 - z0)).normalized()
    n = Vector((-d.z, 0, d.x))
    planes.append(((x0, 0, z0), tuple(n)))
    for co, no in planes:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, dist=1e-5)
    bm.to_mesh(obj.data)
    bm.free()


def separate(obj, name, test):
    """Move faces whose centre passes `test` into a new object."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    sel = [f for f in bm.faces if test(f.calc_center_median())]
    if not sel:
        bm.free()
        return None
    # new mesh with the selected faces
    bm2 = bm.copy()
    keep_idx = {f.index for f in sel}
    bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.index not in keep_idx], context='FACES')
    bmesh.ops.delete(bm2, geom=[v for v in bm2.verts if not v.link_faces], context='VERTS')
    me2 = bpy.data.meshes.new(name)
    bm2.to_mesh(me2)
    bm2.free()
    bmesh.ops.delete(bm, geom=sel, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    for m in obj.data.materials:
        me2.materials.append(m)
    o = bpy.data.objects.new(name, me2)
    for col in obj.users_collection:
        col.objects.link(o)
    return o


ACCESSORIES = [
    'FrontHandle_Chrome', 'Backhandle_Chrome', 'Lock_Chrome', 'Sidechrome1_Chrome', 'Sidechrome2_Chrome',
    'Sidechrome3_Chrome', 'Sidechrome4_Chrome', 'Sidechrome5_Chrome', 'Sidechromedoor_Chrome',
    'SideWindow_Chrome', 'Dooropener_Indoor', 'Basearmholder_Indoor', 'HandleBase_Indoor',
    'endHandle_Indoor', 'BackLock_Chrome', 'SideGlass_Window',
]


def run():
    body = bpy.data.objects['CarUP_UpCar']
    body.name = 'body'
    body.data.name = 'body'
    bisect(body)
    panels = {}
    for name, test in REGIONS.items():
        p = separate(body, name, test)
        if p:
            panels[name] = p
    # trim pieces ride along with their panel
    for acc in ACCESSORIES:
        o = bpy.data.objects.get(acc)
        if not o:
            continue
        parts = L.split_loose(o)
        rest = []
        groups = {}
        for p in parts:
            vs = [v.co for v in p.data.vertices]
            c = sum(vs, Vector()) / len(vs)
            owner = None
            for name, test in REGIONS.items():
                # trim sits on the skin: test with a slightly relaxed point
                cc = Vector((c.x, c.y * 0.97, c.z))
                if test(c) or test(cc):
                    owner = name
                    break
            if owner:
                groups.setdefault(owner, []).append(p)
            else:
                rest.append(p)
        for owner, ps in groups.items():
            joined = L.join(ps, f'{owner}_{acc.split("_")[0].lower()}')
            panels[owner] = L.join([panels[owner], joined], owner)
        if rest:
            L.join(rest, acc)
    for name, p in panels.items():
        L.set_origin(p, PIVOTS[name])
    return body, panels
