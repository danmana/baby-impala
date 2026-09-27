"""Cycles bakes: contact shadows baked into a surface's colour, so the gear
lying on it sits there instead of floating. Ambient occlusion gives the dark
line where things touch; a soft lamp above adds the drop shadow."""
import numpy as np
import bpy
from mathutils import Vector
import lib as L


def pixels(img):
    a = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def _target(obj, img):
    """Make `img` the active bake target in every material on obj."""
    nodes = []
    for mat in obj.data.materials:
        nt = mat.node_tree
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = img
        for m in nt.nodes:
            m.select = False
        n.select = True
        nt.nodes.active = n
        nodes.append((nt, n))
    return nodes


def _bake(obj, img, kind):
    nodes = _target(obj, img)
    L.activate(obj)
    bpy.ops.object.bake(type=kind, margin=8, use_clear=True)
    for nt, n in nodes:
        nt.nodes.remove(n)


def _blur(a, r=1):
    out = a.copy()
    n = 1
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx or dy:
                out += np.roll(np.roll(a, dy, 0), dx, 1)
                n += 1
    return out / n


def contact_shadows(obj, mover, base_path, out_path, light_dir, ao_dist=0.05, ao_strength=0.85,
                    shadow_strength=0.45, samples=64):
    """Bake onto obj (its UVs map the base image 1:1) and write
    base x shadows to out_path. `mover` is lifted far above the car while
    baking so nothing else is in reach; light_dir points from the surface
    towards the lamp."""
    sc = bpy.context.scene
    prev_engine = sc.render.engine
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new('bake')
    sc.world.light_settings.distance = ao_dist

    base = bpy.data.images.load(base_path, check_existing=False)
    w, h = base.size
    lift = Vector((0, 0, 6.0))
    mover.location += lift
    bpy.context.view_layer.update()

    ao = bpy.data.images.new('bake_ao', w, h, float_buffer=True, is_data=True)
    _bake(obj, ao, 'AO')

    # a soft lamp over the gear: an area light 1.2 m out along light_dir
    centre = sum((obj.matrix_world @ Vector(c) for c in obj.bound_box), Vector()) / 8
    ld = bpy.data.lights.new('bake_lamp', 'AREA')
    ld.size = 0.35
    ld.energy = 60
    lamp = bpy.data.objects.new('bake_lamp', ld)
    sc.collection.objects.link(lamp)
    d = Vector(light_dir).normalized()
    lamp.location = centre + d * 1.2
    lamp.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    sh = bpy.data.images.new('bake_shadow', w, h, float_buffer=True, is_data=True)
    _bake(obj, sh, 'SHADOW')
    bpy.data.objects.remove(lamp, do_unlink=True)
    bpy.data.lights.remove(ld)

    mover.location -= lift
    bpy.context.view_layer.update()
    sc.render.engine = prev_engine

    a = _blur(pixels(ao)[..., 0], 1)
    s = _blur(pixels(sh)[..., 0], 1)
    s = np.clip(s / max(np.percentile(s, 97), 1e-4), 0, 1)
    k = (1 - ao_strength * (1 - a)) * (1 - shadow_strength * (1 - s))
    px = pixels(base).copy()
    px[..., :3] *= k[..., None]
    out = bpy.data.images.new('baked', w, h)
    out.pixels.foreach_set(px.ravel())
    out.filepath_raw = out_path
    out.file_format = 'PNG'
    out.save()
    for im in (ao, sh, base, out):
        bpy.data.images.remove(im)
    print('baked contact shadows ->', out_path, f'ao {a.min():.2f}..{a.max():.2f}')
    return out_path
