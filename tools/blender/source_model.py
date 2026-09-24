"""Import the Sketchfab base model ("Chevrolet Impala 1967" by Eques_inferno,
CC BY 4.0) and normalise it to Baby's real-world scale and our axes:
X forward, Y to the driver's side, Z up, ground at Z = 0, metres."""
import math
import os
import bpy
from mathutils import Vector, Matrix
import lib as L

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SRC = os.environ.get('BABY_SRC', os.path.join(ROOT, 'assets-src', 'sketchfab', 'scene.gltf'))

# wheel centres of the source model (its own units, Y = length axis)
SRC_FRONT_Y = -0.1675
SRC_REAR_Y = 0.1569
WHEELBASE = 3.023


def import_source():
    bpy.ops.import_scene.gltf(filepath=SRC)
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    ws = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    zmin = min(v.z for v in ws)
    s = WHEELBASE / (SRC_REAR_Y - SRC_FRONT_Y)
    mid = (SRC_FRONT_Y + SRC_REAR_Y) / 2
    # centre the wheelbase slightly forward of the origin so the body centre sits near x=0
    M = (Matrix.Translation((0.26, 0, 0)) @ Matrix.Scale(s, 4) @ Matrix.Rotation(math.pi / 2, 4, 'Z')
         @ Matrix.Translation((0, -mid, -zmin)))
    world = {o.name: o.matrix_world.copy() for o in meshes}
    for o in meshes:
        o.parent = None
    # drop the empties left from the FBX hierarchy
    for o in list(bpy.data.objects):
        if o.type == 'EMPTY':
            bpy.data.objects.remove(o, do_unlink=True)
    col = L.collection('Baby')
    for o in meshes:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        # bake transforms into the mesh data so every part lives in car space
        if o.data.users > 1:
            o.data = o.data.copy()
        o.data.transform(M @ world[o.name])
        o.matrix_world = Matrix.Identity(4)
        o.name = o.name.replace('_LP', '').replace('_M_0', '').replace('_M1_0', '')
    bpy.context.view_layer.update()
    return meshes, s, M


def axles(M):
    fa = M @ Vector((0, SRC_FRONT_Y, -0.0039))
    ra = M @ Vector((0, SRC_REAR_Y, -0.0039))
    return fa, ra
