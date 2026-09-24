"""EEVEE preview renders (neutral light) for checking the build against the
reference stills. Optional EXPLODE=1 shows the panels pulled apart."""
import math
import os
import bpy
from mathutils import Vector
import preview as P


def setup(res=(1720, 908)):
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in engines else 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = res
    w = bpy.data.worlds.new('preview')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.75, 0.76, 0.78, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    for i, rot in enumerate([(math.radians(-45), 0, math.radians(200)), (math.radians(35), 0, math.radians(60))]):
        ld = bpy.data.lights.new(f'sun{i}', 'SUN')
        ld.energy = 2.5
        lo = bpy.data.objects.new(f'sun{i}', ld)
        sc.collection.objects.link(lo)
        lo.rotation_euler = rot


def shot(name, loc, target, out, ortho=None, lens=40):
    cam = P.camera(name, loc, target, ortho=ortho, lens=lens)
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.filepath = os.path.join(out, name + '.png')
    bpy.ops.render.render(write_still=True)
    return cam


def explode():
    offs = {'hood': (0.2, 0, 0.8), 'trunk_lid': (-0.3, 0, 0.8), 'door_fl': (0.1, 0.7, 0.0),
            'door_rl': (-0.1, 0.7, 0.0), 'door_fr': (0.1, -0.7, 0.0), 'door_rr': (-0.1, -0.7, 0.0)}
    for n, d in offs.items():
        o = bpy.data.objects.get(n)
        if o:
            o.location = Vector(o.location) + Vector(d)


def render_all(out, prefix='b'):
    setup()
    views = os.environ.get('VIEWS', 'side,f34,r34,front,rear,int').split(',')
    if os.environ.get('EXPLODE'):
        explode()
    for n in os.environ.get('HIDE', '').split(','):
        o = bpy.data.objects.get(n)
        if o:
            o.hide_render = True
    if 'side' in views:
        shot(f'{prefix}_side', (0, 30, 0.75), (0, 0, 0.75), out, ortho=6.2)
    if 'f34' in views:
        shot(f'{prefix}_f34', (5.2, 3.3, 0.9), (0.6, 0, 0.62), out, lens=40)
    if 'r34' in views:
        shot(f'{prefix}_r34', (-6.0, 3.0, 1.2), (-0.8, 0.3, 0.7), out, lens=45)
    if 'front' in views:
        shot(f'{prefix}_front', (30, 0, 0.75), (0, 0, 0.75), out, ortho=2.6)
    if 'rear' in views:
        shot(f'{prefix}_rear', (-30, 0, 0.75), (0, 0, 0.75), out, ortho=2.6)
    if 'int' in views:
        shot(f'{prefix}_int', (-0.35, 0.3, 1.18), (1.2, 0.0, 0.85), out, lens=22)
    if 'dash' in views:
        shot(f'{prefix}_dash', (0.25, -0.35, 1.08), (0.92, 0.02, 0.9), out, lens=24)
    if 'back' in views:
        shot(f'{prefix}_back', (0.1, 0.1, 1.12), (-0.9, 0.3, 0.85), out, lens=22)
    if 'trunk' in views:
        shot(f'{prefix}_trunk', (-4.6, 1.2, 2.2), (-2.0, 0, 0.8), out, lens=40)
