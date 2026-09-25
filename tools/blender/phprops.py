"""Photoscanned props (Poly Haven, CC0) and scanned-texture materials for the
procedural ones, so the trunk gear reads as real objects, not flat shapes."""
import math
import os
import bpy
import bmesh
from mathutils import Vector, Matrix
import lib as L

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PH = os.path.join(ROOT, 'assets-src', 'polyhaven', 'models')
TEX = os.path.join(ROOT, 'assets-src', 'props_tex')


def import_ph(asset, keep=None, name=None, decimate=None, tex_size=512):
    """Import a Poly Haven glTF, keep only the named parts, join into one
    object with its origin at the bounding-box centre. Returns the object."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PH, asset, f'{asset}.gltf'))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = []
    for o in new:
        if o.type != 'MESH' or (keep and o.name.split('.')[0] not in keep):
            continue
        meshes.append(o)
    for o in new:
        if o not in meshes:
            bpy.data.objects.remove(o, do_unlink=True)
    for o in meshes:
        mw = o.matrix_world.copy()
        o.parent = None
        if o.data.users > 1:
            o.data = o.data.copy()
        o.data.transform(mw)
        o.matrix_world = Matrix.Identity(4)
        for c in list(o.users_collection):
            c.objects.unlink(o)
        L.link(o)
    obj = L.join(meshes, name or asset)
    vs = [v.co for v in obj.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    obj.data.transform(Matrix.Translation(-(mn + mx) / 2))
    if decimate and decimate < 1:
        m = obj.modifiers.new('dec', 'DECIMATE')
        m.ratio = decimate
        L.apply_modifiers(obj)
    for mat in obj.data.materials:
        if not mat or not mat.use_nodes:
            continue
        for n in mat.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image and n.image.size[0] > tex_size:
                n.image.scale(tex_size, tex_size)
    return obj


def orient(obj, rx=0.0, ry=0.0, rz=0.0):
    """Rotate mesh data (degrees, XYZ order) about its origin."""
    obj.data.transform(Matrix.Rotation(math.radians(rz), 4, 'Z') @ Matrix.Rotation(math.radians(ry), 4, 'Y')
                       @ Matrix.Rotation(math.radians(rx), 4, 'X'))
    return obj


def size_of(obj):
    vs = [v.co for v in obj.data.vertices]
    return Vector((max(v.x for v in vs) - min(v.x for v in vs), max(v.y for v in vs) - min(v.y for v in vs),
                   max(v.z for v in vs) - min(v.z for v in vs)))


# ------------------------------------------------------------------ scanned materials

_mats = {}


def _img(path):
    img = bpy.data.images.load(path, check_existing=True)
    return img


def tex_material(kind, metallic=0.0, rough_scale=1.0):
    """Principled material using the prepared texture set `kind` (col/nor/rough)."""
    key = f'tex_{kind}'
    if key in _mats:
        return _mats[key]
    mat = bpy.data.materials.new(key)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    col = nt.nodes.new('ShaderNodeTexImage')
    col.image = _img(os.path.join(TEX, f'{kind}_col.png'))
    nt.links.new(col.outputs['Color'], bsdf.inputs['Base Color'])
    rough = nt.nodes.new('ShaderNodeTexImage')
    rough.image = _img(os.path.join(TEX, f'{kind}_rough.png'))
    rough.image.colorspace_settings.name = 'Non-Color'
    nt.links.new(rough.outputs['Color'], bsdf.inputs['Roughness'])
    nor = nt.nodes.new('ShaderNodeTexImage')
    nor.image = _img(os.path.join(TEX, f'{kind}_nor.png'))
    nor.image.colorspace_settings.name = 'Non-Color'
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(nor.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Metallic'].default_value = metallic
    _mats[key] = mat
    return mat


# flat procedural material name -> (texture set, metallic)
REMAP = {
    'wood': ('wood_light', 0.0), 'wood_dark': ('wood_dark', 0.0), 'antler': ('wood_light', 0.0),
    'leather': ('leather_brown', 0.0), 'leather_dark': ('leather_black', 0.0), 'strap': ('leather_black', 0.0),
    'steel': ('steel', 1.0), 'steel_dark': ('gunmetal', 1.0), 'gunmetal': ('gunmetal', 0.9), 'iron': ('gunmetal', 0.85),
    'silver': ('silver', 1.0), 'nickel': ('silver', 1.0), 'brass': ('brass', 1.0),
    'felt': ('felt_black', 0.0), 'carpet': ('felt_black', 0.0), 'carpet_gray': ('carpet_grey', 0.0),
    'canvas_olive': ('canvas_olive', 0.0), 'cardboard': ('cardboard', 0.0), 'burlap': ('canvas_olive', 0.0),
    'ammo_green': ('canvas_olive', 0.35), 'twine': ('twine', 0.0), 'sage': ('sage', 0.0), 'shell_red': ('shell', 0.0),
}


def uv_unwrap(obj, scale=1.0):
    """Box-project UVs in world units so texel density matches across props."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for lp in f.loops:
            co = lp.vert.co
            if ax == 0:
                u, v = co.y, co.z
            elif ax == 1:
                u, v = co.x, co.z
            else:
                u, v = co.x, co.y
            lp[uv].uv = (u * scale * 4.0, v * scale * 4.0)
    bm.to_mesh(me)
    bm.free()


def texturize(obj):
    """Swap flat procedural materials on `obj` for scanned ones (and unwrap)."""
    changed = False
    for i, slot in enumerate(obj.material_slots):
        m = slot.material
        if not m:
            continue
        key = m.name.split('.')[0]
        if key in REMAP:
            kind, metal = REMAP[key]
            slot.material = tex_material(kind, metal)
            changed = True
    if changed:
        uv_unwrap(obj)
    return obj
