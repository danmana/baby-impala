"""Geometry helpers for building Baby procedurally inside Blender.

Coordinate system (Blender): X forward (front of the car is +X), Y to the car's
left (driver side, +Y), Z up. Ground is Z = 0. Units are metres.
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix


# ---------------------------------------------------------------- scene utils

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def collection(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    return col


_current_collection = [None]


def set_collection(name):
    _current_collection[0] = collection(name)


def link(obj):
    col = _current_collection[0] or bpy.context.scene.collection
    col.objects.link(obj)
    return obj


# fallback look for the materials we create (the web app replaces most of these)
MAT_COLORS = {
    'chrome': ((0.9, 0.9, 0.9), 1.0, 0.08), 'steel': ((0.6, 0.6, 0.6), 1.0, 0.3),
    'steel_dark': ((0.25, 0.25, 0.26), 1.0, 0.4), 'gunmetal': ((0.08, 0.08, 0.09), 0.9, 0.35),
    'silver': ((0.85, 0.85, 0.87), 1.0, 0.18), 'nickel': ((0.7, 0.68, 0.64), 1.0, 0.25),
    'iron': ((0.2, 0.19, 0.18), 0.9, 0.6), 'brass': ((0.7, 0.53, 0.24), 1.0, 0.35),
    'wood': ((0.33, 0.2, 0.1), 0.0, 0.7), 'wood_dark': ((0.18, 0.1, 0.05), 0.0, 0.6),
    'leather': ((0.29, 0.17, 0.09), 0.0, 0.65), 'leather_dark': ((0.12, 0.08, 0.05), 0.0, 0.6),
    'antler': ((0.72, 0.64, 0.5), 0.0, 0.6), 'ivory': ((0.86, 0.82, 0.72), 0.0, 0.4),
    'felt': ((0.02, 0.02, 0.02), 0.0, 1.0), 'felt_red': ((0.3, 0.03, 0.04), 0.0, 1.0),
    'carpet': ((0.03, 0.03, 0.03), 0.0, 1.0), 'carpet_gray': ((0.22, 0.22, 0.21), 0.0, 1.0),
    'strap': ((0.04, 0.04, 0.04), 0.0, 0.8), 'twine': ((0.55, 0.45, 0.3), 0.0, 0.9),
    'sage': ((0.45, 0.5, 0.42), 0.0, 0.9), 'feather': ((0.8, 0.78, 0.74), 0.0, 0.8),
    'bottle_glass': ((0.6, 0.7, 0.72), 0.0, 0.05), 'blood_glass': ((0.25, 0.02, 0.02), 0.0, 0.1),
    'oil_glass': ((0.55, 0.42, 0.1), 0.0, 0.1), 'salt_blue': ((0.1, 0.25, 0.6), 0.0, 0.5),
    'ammo_green': ((0.2, 0.26, 0.14), 0.3, 0.6), 'cardboard': ((0.45, 0.33, 0.2), 0.0, 0.9),
    'shell_red': ((0.55, 0.06, 0.05), 0.0, 0.5), 'paper': ((0.85, 0.82, 0.74), 0.0, 0.9),
    'plastic_black': ((0.03, 0.03, 0.03), 0.0, 0.5), 'red_plastic': ((0.6, 0.05, 0.03), 0.0, 0.5),
    'zippo_blue': ((0.1, 0.2, 0.5), 0.3, 0.5), 'tape': ((0.5, 0.5, 0.5), 0.2, 0.6),
    'burlap': ((0.5, 0.4, 0.26), 0.0, 1.0), 'canvas_olive': ((0.3, 0.3, 0.18), 0.0, 0.9),
    'bead_blue': ((0.1, 0.2, 0.6), 0.2, 0.3), 'led_red': ((0.8, 0.05, 0.05), 0.0, 0.3),
    'led_green': ((0.1, 0.7, 0.1), 0.0, 0.3), 'engine': ((0.6, 0.2, 0.04), 0.1, 0.5),
    'engine_dark': ((0.05, 0.05, 0.05), 0.4, 0.6), 'exhaust': ((0.15, 0.13, 0.12), 0.8, 0.5),
    'underbody': ((0.02, 0.02, 0.02), 0.0, 0.9), 'radiator': ((0.05, 0.05, 0.05), 0.6, 0.5),
    'wire_red': ((0.5, 0.05, 0.03), 0.0, 0.5), 'spot_lens': ((0.8, 0.8, 0.75), 0.2, 0.05),
    'drum': ((0.1, 0.1, 0.1), 0.7, 0.6), 'trap_paint': ((0.02, 0.02, 0.02), 0.0, 0.4),
    'tan': ((0.45, 0.35, 0.24), 0.0, 0.7), 'vinyl': ((0.02, 0.02, 0.02), 0.0, 0.45),
    'lego_red': ((0.6, 0.03, 0.03), 0.0, 0.35), 'lego_blue': ((0.03, 0.15, 0.6), 0.0, 0.35),
    'lego_yellow': ((0.8, 0.6, 0.02), 0.0, 0.35), 'army_green': ((0.2, 0.33, 0.12), 0.0, 0.5),
    'dial': ((0.03, 0.03, 0.03), 0.0, 0.3), 'plastic_olive': ((0.35, 0.33, 0.2), 0.0, 0.55),
    'wood_trim': ((0.3, 0.18, 0.08), 0.0, 0.55), 'bowtie': ((0.7, 0.55, 0.25), 1.0, 0.3),
    'mirror': ((0.95, 0.95, 0.95), 1.0, 0.02), 'paint': ((0.01, 0.01, 0.012), 0.0, 0.3),
    'black': ((0.01, 0.01, 0.01), 0.0, 0.5), 'rubber': ((0.02, 0.02, 0.02), 0.0, 0.7),
    'tire': ((0.02, 0.02, 0.02), 0.0, 0.85), 'lens_clear': ((0.8, 0.8, 0.78), 0.0, 0.1),
}


def material(name):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        spec = MAT_COLORS.get(name)
        if spec:
            (r, g, b), metal, rough = spec
            mat.diffuse_color = (r, g, b, 1.0)
            mat.metallic = metal
            mat.roughness = rough
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get('Principled BSDF')
            if bsdf:
                bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
                bsdf.inputs['Metallic'].default_value = metal
                bsdf.inputs['Roughness'].default_value = rough
    return mat


def activate(obj):
    for o in bpy.context.view_layer.objects.selected[:]:
        if o is not None:
            o.select_set(False)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def apply_modifiers(obj):
    activate(obj)
    for m in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def delete(obj):
    me = obj.data if obj.type == 'MESH' else None
    bpy.data.objects.remove(obj, do_unlink=True)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)
    bpy.context.view_layer.update()


# ---------------------------------------------------------------- mesh makers

def mesh_object(name, verts, faces, mat=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(clean_customdata=False)
    me.update()
    obj = bpy.data.objects.new(name, me)
    link(obj)
    if mat:
        obj.data.materials.append(material(mat))
    if smooth:
        me.shade_smooth()
    return obj


def grid_faces(rows, cols, close_cols=False, close_rows=False, flip=False):
    """Quad faces for a rows x cols vertex grid (row-major)."""
    faces = []
    rr = rows if close_rows else rows - 1
    cc = cols if close_cols else cols - 1
    for r in range(rr):
        r2 = (r + 1) % rows
        for c in range(cc):
            c2 = (c + 1) % cols
            a, b, cq, d = r * cols + c, r * cols + c2, r2 * cols + c2, r2 * cols + c
            faces.append((a, d, cq, b) if flip else (a, b, cq, d))
    return faces


def loft(name, sections, mat=None, close_sections=False, cap_start=False,
         cap_end=False, flip=False, smooth=True):
    """sections: list of equal-length point lists (Vectors or tuples)."""
    rows = len(sections)
    cols = len(sections[0])
    verts = [Vector(p) for s in sections for p in s]
    faces = grid_faces(rows, cols, close_cols=close_sections, flip=flip)
    if cap_start:
        f = list(range(cols))
        faces.append(tuple(f if flip else reversed(f)))
    if cap_end:
        base = (rows - 1) * cols
        f = [base + i for i in range(cols)]
        faces.append(tuple(reversed(f) if flip else f))
    return mesh_object(name, verts, faces, mat, smooth)


def lathe(name, profile, segments=48, mat=None, axis='X', center=(0, 0, 0),
          angle=2 * math.pi, smooth=True, cap=False, close=False):
    """Revolve a 2D profile [(axial, radius), ...] around an axis.
    axis 'X': axial along X, radius in the YZ plane; 'Y': axial along Y."""
    full = abs(angle - 2 * math.pi) < 1e-6
    n = segments if full else segments + 1
    verts = []
    cx, cy, cz = center
    for i in range(n):
        t = angle * i / segments
        ct, st = math.cos(t), math.sin(t)
        for (a, r) in profile:
            if axis == 'X':
                verts.append((cx + a, cy + r * ct, cz + r * st))
            elif axis == 'Y':
                verts.append((cx + r * ct, cy + a, cz + r * st))
            else:
                verts.append((cx + r * ct, cy + r * st, cz + a))
    cols = len(profile)
    faces = grid_faces(n, cols, close_rows=full, close_cols=close)
    if axis == 'Y':
        faces = [tuple(reversed(f)) for f in faces]
    obj = mesh_object(name, verts, faces, mat, smooth)
    if any(abs(r) < 1e-6 for (_, r) in profile):
        weld(obj)
    if close:
        fix_normals(obj)
    return obj


def weld(obj, dist=1e-6):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=dist)
    bm.to_mesh(obj.data)
    bm.free()


def frame_along(path, up=Vector((0, 0, 1))):
    """Parallel-transport frames (tangent, normal, binormal) along a polyline."""
    pts = [Vector(p) for p in path]
    n = len(pts)
    tangents = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        tangents.append(t.normalized())
    frames = []
    nrm = up.cross(tangents[0])
    if nrm.length < 1e-6:
        nrm = Vector((0, 1, 0)).cross(tangents[0])
    nrm.normalize()
    for i in range(n):
        t = tangents[i]
        if i > 0:
            # parallel transport
            prev_t = tangents[i - 1]
            axis = prev_t.cross(t)
            if axis.length > 1e-8:
                ang = prev_t.angle(t)
                nrm = Matrix.Rotation(ang, 3, axis.normalized()) @ nrm
        b = t.cross(nrm).normalized()
        nrm = b.cross(t).normalized()
        frames.append((t, nrm, b))
    return pts, frames


def sweep(name, path, profile, mat=None, closed_profile=True, cap=True,
          up=Vector((0, 0, 1)), scale=None, smooth=True, fixed_side=None):
    """Sweep a 2D profile [(u, v)] along a 3D path.
    u runs along the frame 'normal' (side), v along the binormal (up-ish).
    fixed_side: optional Vector; if given, the profile's u-axis is locked to
    this direction projected perpendicular to the tangent (good for trims that
    must stay flat against a body side)."""
    pts, frames = frame_along(path, up)
    verts = []
    for i, (p, (t, nrm, b)) in enumerate(zip(pts, frames)):
        if fixed_side is not None:
            side = Vector(fixed_side)
            side = (side - t * side.dot(t)).normalized()
            upv = t.cross(side).normalized()
            nrm, b = side, upv
        s = scale(i / (len(pts) - 1)) if scale else 1.0
        for (u, v) in profile:
            verts.append(p + nrm * (u * s) + b * (v * s))
    rows, cols = len(pts), len(profile)
    faces = grid_faces(rows, cols, close_cols=closed_profile)
    if cap and closed_profile:
        faces.append(tuple(reversed(range(cols))))
        base = (rows - 1) * cols
        faces.append(tuple(base + i for i in range(cols)))
    return mesh_object(name, verts, faces, mat, smooth)


def box(name, size, center=(0, 0, 0), mat=None, bevel=0.0, segments=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(center)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    link(obj)
    if mat:
        obj.data.materials.append(material(mat))
    if bevel > 0:
        m = obj.modifiers.new('bevel', 'BEVEL')
        m.width = bevel
        m.segments = segments
        m.limit_method = 'NONE'
        apply_modifiers(obj)
        obj.data.shade_smooth()
        auto_smooth(obj, 35)
    return obj


def cylinder(name, radius, depth, center=(0, 0, 0), axis='Z', segments=32, mat=None,
             bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=depth)
    rot = {'X': Matrix.Rotation(math.pi / 2, 4, 'Y'),
           'Y': Matrix.Rotation(math.pi / 2, 4, 'X'),
           'Z': Matrix.Identity(4)}[axis]
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    link(obj)
    if mat:
        obj.data.materials.append(material(mat))
    if bevel > 0:
        m = obj.modifiers.new('bevel', 'BEVEL')
        m.width = bevel
        m.segments = 2
        m.limit_method = 'ANGLE'
        apply_modifiers(obj)
    obj.data.shade_smooth()
    auto_smooth(obj, 40)
    return obj


def prism(name, outline, zmin, zmax, axis='Z'):
    """Extrude a closed 2D outline into a solid.
    axis 'Z': outline in (x, y), extruded along z.
    axis 'Y': outline in (x, z), extruded along y from zmin..zmax (as y).
    axis 'X': outline in (y, z), extruded along x."""
    n = len(outline)
    verts = []
    for h in (zmin, zmax):
        for (a, b) in outline:
            if axis == 'Z':
                verts.append((a, b, h))
            elif axis == 'Y':
                verts.append((a, h, b))
            else:
                verts.append((h, a, b))
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    faces.append(tuple(reversed(range(n))))
    faces.append(tuple(n + i for i in range(n)))
    obj = mesh_object(name, verts, faces, None, smooth=False)
    fix_normals(obj)
    return obj


def fix_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def flip_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


# ---------------------------------------------------------------- modifiers

def boolean(obj, cutter, op='DIFFERENCE', solver='MANIFOLD', keep_cutter=False):
    """Boolean with solver fallback: MANIFOLD is fast and robust on our closed
    shells; EXACT occasionally returns empty results on long cut chains."""
    backup = obj.data.copy()
    before = len(obj.data.polygons)
    for s in (solver, 'EXACT', 'FLOAT'):
        m = obj.modifiers.new('bool', 'BOOLEAN')
        m.operation = op
        m.object = cutter
        m.solver = s
        apply_modifiers(obj)
        n = len(obj.data.polygons)
        ok = n > 0 and (op != 'DIFFERENCE' or n > before * 0.2)
        if ok:
            break
        print(f'  boolean {op} with {s} failed on {obj.name} ({n} faces), retrying')
        old = obj.data
        obj.data = backup.copy()
        bpy.data.meshes.remove(old)
    bpy.data.meshes.remove(backup)
    if not keep_cutter:
        delete(cutter)
    return obj


def solidify(obj, thickness, offset=-1.0, even=True):
    m = obj.modifiers.new('solid', 'SOLIDIFY')
    m.thickness = thickness
    m.offset = offset
    m.use_even_offset = even
    m.use_quality_normals = True
    apply_modifiers(obj)
    return obj


def subdivide(obj, levels=1):
    m = obj.modifiers.new('subd', 'SUBSURF')
    m.levels = levels
    m.render_levels = levels
    apply_modifiers(obj)
    return obj


def bevel(obj, width, segments=2, angle=30):
    m = obj.modifiers.new('bevel', 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    apply_modifiers(obj)
    return obj


def auto_smooth(obj, angle_deg=35):
    """Smooth shading with sharp edges above angle (baked into sharp_edge)."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    lim = math.radians(angle_deg)
    sharp = []
    for e in bm.edges:
        if len(e.link_faces) != 2:
            sharp.append(True)
            continue
        try:
            a = e.calc_face_angle()
        except ValueError:
            a = 0
        sharp.append(a > lim)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    attr = me.attributes.get('sharp_edge')
    if attr is None:
        attr = me.attributes.new('sharp_edge', 'BOOLEAN', 'EDGE')
    attr.data.foreach_set('value', sharp)
    me.update()


def set_material(obj, name):
    obj.data.materials.clear()
    obj.data.materials.append(material(name))
    for p in obj.data.polygons:
        p.material_index = 0


def set_origin(obj, point):
    """Move the object's origin to a world-space point without moving geometry."""
    point = Vector(point)
    mw = obj.matrix_world.copy()
    local = mw.inverted() @ point
    obj.data.transform(Matrix.Translation(-local))
    obj.matrix_world = mw @ Matrix.Translation(local)


def join(objs, name=None):
    objs = [o for o in objs if o is not None]
    if len(objs) == 1:
        if name:
            objs[0].name = name
            objs[0].data.name = name
        return objs[0]
    activate(objs[0])
    for o in objs[1:]:
        o.select_set(True)
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    if name:
        o.name = name
        o.data.name = name
    return o


def split_loose(obj):
    """Split an object into one object per connected component."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    seen = set()
    groups = []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack = [f]
        comp = []
        seen.add(f.index)
        while stack:
            cur = stack.pop()
            comp.append(cur.index)
            for e in cur.edges:
                for nf in e.link_faces:
                    if nf.index not in seen:
                        seen.add(nf.index)
                        stack.append(nf)
        groups.append(comp)
    bm.free()
    parts = []
    for gi, comp in enumerate(groups):
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        keep = set(comp)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
        loose = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
        nm = bpy.data.meshes.new(f"{obj.name}_{gi}")
        bm.to_mesh(nm)
        bm.free()
        for m in me.materials:
            nm.materials.append(m)
        o = bpy.data.objects.new(f"{obj.name}_{gi}", nm)
        for col in obj.users_collection:
            col.objects.link(o)
        o.matrix_world = obj.matrix_world
        parts.append(o)
    delete(obj)
    return parts


def bbox(obj):
    ws = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    mn = Vector((min(v.x for v in ws), min(v.y for v in ws), min(v.z for v in ws)))
    mx = Vector((max(v.x for v in ws), max(v.y for v in ws), max(v.z for v in ws)))
    return mn, mx


def mirror_y(obj, name):
    """Duplicate an object mirrored across the XZ plane (y -> -y)."""
    me = obj.data.copy()
    me.transform(Matrix.Scale(-1, 4, (0, 1, 0)))
    me.flip_normals()
    o = bpy.data.objects.new(name, me)
    for col in obj.users_collection:
        col.objects.link(o)
    o.matrix_world = Matrix.Scale(1, 4)
    # mirror object location too
    loc = obj.matrix_world.translation.copy()
    me.transform(Matrix.Translation((0, 0, 0)))
    o.location = (loc.x, -loc.y, loc.z)
    # geometry was defined relative to obj origin: re-center
    return o


def duplicate(obj, name, linked=False):
    o = obj.copy()
    if not linked:
        o.data = obj.data.copy()
    o.name = name
    for col in obj.users_collection:
        col.objects.link(o)
    return o


def empty(name, location, parent=None):
    o = bpy.data.objects.new(name, None)
    o.location = location
    o.empty_display_size = 0.05
    link(o)
    if parent:
        o.parent = parent
    return o


# ---------------------------------------------------------------- curves

def catmull(points, n_per_seg=8, closed=False, alpha=0.5):
    """Centripetal Catmull-Rom through points; returns a dense polyline."""
    P = [Vector(p) for p in points]
    if closed:
        P = [P[-1]] + P + [P[0], P[1]]
    else:
        P = [P[0] + (P[0] - P[1])] + P + [P[-1] + (P[-1] - P[-2])]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]

        def tj(ti, a, b):
            return ti + max((b - a).length, 1e-6) ** alpha
        t0 = 0.0
        t1 = tj(t0, p0, p1)
        t2 = tj(t1, p1, p2)
        t3 = tj(t2, p2, p3)
        for k in range(n_per_seg):
            t = t1 + (t2 - t1) * k / n_per_seg
            a1 = p0 * ((t1 - t) / (t1 - t0)) + p1 * ((t - t0) / (t1 - t0))
            a2 = p1 * ((t2 - t) / (t2 - t1)) + p2 * ((t - t1) / (t2 - t1))
            a3 = p2 * ((t3 - t) / (t3 - t2)) + p3 * ((t - t2) / (t3 - t2))
            b1 = a1 * ((t2 - t) / (t2 - t0)) + a2 * ((t - t0) / (t2 - t0))
            b2 = a2 * ((t3 - t) / (t3 - t1)) + a3 * ((t - t1) / (t3 - t1))
            out.append(b1 * ((t2 - t) / (t2 - t1)) + b2 * ((t - t1) / (t2 - t1)))
    if not closed:
        out.append(Vector(points[-1]))
    return out


def resample(poly, n):
    """Resample a polyline to n points evenly by arc length."""
    P = [Vector(p) for p in poly]
    d = [0.0]
    for i in range(1, len(P)):
        d.append(d[-1] + (P[i] - P[i - 1]).length)
    L = d[-1]
    out = []
    j = 0
    for k in range(n):
        s = L * k / (n - 1)
        while j < len(d) - 2 and d[j + 1] < s:
            j += 1
        seg = d[j + 1] - d[j]
        t = 0 if seg < 1e-9 else (s - d[j]) / seg
        out.append(P[j].lerp(P[j + 1], t))
    return out


def pchip(xs, ys):
    """Monotone cubic interpolation; returns f(x). xs ascending."""
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    dlt = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0] = dlt[0]
    m[-1] = dlt[-1]
    for i in range(1, n - 1):
        if dlt[i - 1] * dlt[i] <= 0:
            m[i] = 0.0
        else:
            w1 = 2 * h[i] + h[i - 1]
            w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / dlt[i - 1] + w2 / dlt[i])

    def f(x):
        if x <= xs[0]:
            return ys[0] + m[0] * (x - xs[0])
        if x >= xs[-1]:
            return ys[-1] + m[-1] * (x - xs[-1])
        i = 0
        while xs[i + 1] < x:
            i += 1
        t = (x - xs[i]) / h[i]
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i]
                + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * m[i + 1])
    return f


def table(pairs):
    """pairs: [(x, y), ...] in any order -> pchip function."""
    pairs = sorted(pairs)
    return pchip([p[0] for p in pairs], [p[1] for p in pairs])


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def superellipse(cx, cz, a, b, n=2.5, steps=48, start=0.0, end=math.pi):
    pts = []
    for i in range(steps + 1):
        t = start + (end - start) * i / steps
        c, s = math.cos(t), math.sin(t)
        x = cx + a * math.copysign(abs(c) ** (2 / n), c)
        z = cz + b * math.copysign(abs(s) ** (2 / n), s)
        pts.append((x, z))
    return pts


# ---------------------------------------------------------------- patches

def polyline_fn(points, n=64):
    """Return f(t) for t in [0,1] sampling an arc-length-resampled polyline."""
    P = resample(points, n)

    def f(t):
        t = max(0.0, min(1.0, t))
        k = t * (len(P) - 1)
        i = min(int(k), len(P) - 2)
        return P[i].lerp(P[i + 1], k - i)
    return f


def coons(name, B, T, Lf, R, nu=24, nv=24, mat=None, bulge=None, flip=False,
          smooth=True):
    """Coons patch from four boundary functions (t in [0,1] -> Vector).
    B(u), T(u): bottom/top; Lf(v), R(v): left/right. Corners must match:
    B(0)=Lf(0), B(1)=R(0), T(0)=Lf(1), T(1)=R(1).
    bulge(u, v) -> Vector offset (optional)."""
    P00, P10, P01, P11 = B(0), B(1), T(0), T(1)
    verts = []
    for j in range(nv + 1):
        v = j / nv
        for i in range(nu + 1):
            u = i / nu
            p = (B(u) * (1 - v) + T(u) * v + Lf(v) * (1 - u) + R(v) * u
                 - (P00 * ((1 - u) * (1 - v)) + P10 * (u * (1 - v))
                    + P01 * ((1 - u) * v) + P11 * (u * v)))
            if bulge:
                p = p + bulge(u, v)
            verts.append(p)
    faces = grid_faces(nv + 1, nu + 1, flip=flip)
    obj = mesh_object(name, verts, faces, mat, smooth)
    return obj


def surface_normals_fn(obj):
    """Return f(point) -> (closest point, normal) on obj's surface."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(obj, dg)

    def f(p):
        loc, nrm, idx, dist = tree.find_nearest(Vector(p))
        return loc, nrm
    return f


def molding(name, path, normal_fn, width=0.012, height=0.006, mat='chrome',
            lift=0.001, closed=False, profile=None, cap=True):
    """Half-round chrome strip following `path` on a surface.
    normal_fn(p) -> (point_on_surface, normal)."""
    pts = [Vector(p) for p in path]
    if profile is None:
        profile = []
        k = 8
        for i in range(k + 1):
            a = math.pi * i / k
            profile.append((-math.cos(a) * width / 2, math.sin(a) * height))
        profile.append((width / 2 * 0.9, -0.0015))
        profile.append((-width / 2 * 0.9, -0.0015))
    n = len(pts)
    verts = []
    for i in range(n):
        if closed:
            t = (pts[(i + 1) % n] - pts[i - 1]).normalized()
        else:
            t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        sp, nrm = normal_fn(pts[i])
        if nrm is None:
            nrm = Vector((0, 0, 1))
        nrm = (nrm - t * nrm.dot(t)).normalized()
        side = t.cross(nrm).normalized()
        base = pts[i] + nrm * lift
        for (u, v) in profile:
            verts.append(base + side * u + nrm * v)
    cols = len(profile)
    faces = grid_faces(n, cols, close_cols=True, close_rows=closed)
    if cap and not closed:
        faces.append(tuple(reversed(range(cols))))
        b = (n - 1) * cols
        faces.append(tuple(b + i for i in range(cols)))
    obj = mesh_object(name, verts, faces, mat, True)
    auto_smooth(obj, 50)
    return obj


def plan_sweep(name, path_xy, profile_uz, mat=None, closed_path=False, cap=True,
               smooth=True, sharp_angle=40):
    """Sweep a profile [(u, z)] along a plan-view path [(x, y)]; u is the
    horizontal outward normal offset (left of the travel direction), z absolute."""
    P = [Vector((p[0], p[1], 0)) for p in path_xy]
    n = len(P)
    verts = []
    for i in range(n):
        if closed_path:
            t = P[(i + 1) % n] - P[i - 1]
        else:
            t = P[min(i + 1, n - 1)] - P[max(i - 1, 0)]
        t.z = 0
        t.normalize()
        nrm = Vector((t.y, -t.x, 0))  # right-hand normal in plan
        for (u, z) in profile_uz:
            verts.append(Vector((P[i].x + nrm.x * u, P[i].y + nrm.y * u, z)))
    cols = len(profile_uz)
    faces = grid_faces(n, cols, close_cols=True, close_rows=closed_path)
    if cap and not closed_path:
        faces.append(tuple(reversed(range(cols))))
        b = (n - 1) * cols
        faces.append(tuple(b + i for i in range(cols)))
    obj = mesh_object(name, verts, faces, mat, smooth)
    fix_normals(obj)
    auto_smooth(obj, sharp_angle)
    return obj


def text_mesh(name, text, font_path, size, extrude=0.002, mat=None, align='CENTER',
              bevel=0.0):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = text
    cu.font = bpy.data.fonts.load(font_path, check_existing=True)
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.resolution_u = 4
    obj = bpy.data.objects.new(name, cu)
    link(obj)
    activate(obj)
    bpy.ops.object.convert(target='MESH')
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    if mat:
        obj.data.materials.clear()
        obj.data.materials.append(material(mat))
    return obj


def rounded_rect(w, h, r, n=6):
    """Closed 2D outline centred at 0 (w x h, corner radius r)."""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def place(obj, loc=(0, 0, 0), rot=(0, 0, 0)):
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def bake_transform(obj):
    """Apply location/rotation/scale into the mesh (object ends at identity)."""
    obj.data.transform(obj.matrix_basis)
    obj.matrix_basis.identity()
    return obj


def extrude_outline(name, outline, depth, mat=None, bevel_w=0.0, segments=2, smooth=True):
    """Closed 2D outline in the XY plane extruded along +Z by depth (from 0)."""
    obj = prism(name, outline, 0.0, depth, axis='Z')
    if mat:
        obj.data.materials.append(material(mat))
    if bevel_w > 0:
        m = obj.modifiers.new('bevel', 'BEVEL')
        m.width = bevel_w
        m.segments = segments
        m.limit_method = 'ANGLE'
        m.angle_limit = math.radians(30)
        apply_modifiers(obj)
    if smooth:
        auto_smooth(obj, 35)
    return obj
