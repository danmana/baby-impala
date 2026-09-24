"""GLB export: downsize the source textures for the web, wire the baked AO
maps into glTF occlusion, and write a Draco-compressed GLB with WebP images."""
import os
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
AO_DIR = os.path.join(ROOT, 'assets-src', 'sketchfab', 'textures')

# longest edge per source material (pixels)
SIZES = {'UpCar_M1': 2048, 'FrontChromes_M': 1024, 'Chrome_M': 1024, 'Indoor_M': 1024,
         'wheel_M': 1024, 'Window_M': 512}


def gltf_output_group():
    g = bpy.data.node_groups.get('glTF Material Output')
    if g is None:
        g = bpy.data.node_groups.new('glTF Material Output', 'ShaderNodeTree')
        g.interface.new_socket(name='Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
        g.interface.new_socket(name='Thickness', in_out='INPUT', socket_type='NodeSocketFloat')
    return g


def add_ao(mat):
    base = mat.name.replace('.001', '')
    path = os.path.join(AO_DIR, f'{base}_Mixed_AO.png')
    if not os.path.exists(path) or not mat.use_nodes:
        return
    nt = mat.node_tree
    if any(n.type == 'GROUP' and n.node_tree and n.node_tree.name == 'glTF Material Output' for n in nt.nodes):
        return
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = 'Non-Color'
    size = SIZES.get(base, 1024) // 2
    if img.size[0] > size:
        img.scale(size, size)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    # use the same UV map as the base colour texture
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    grp = nt.nodes.new('ShaderNodeGroup')
    grp.node_tree = gltf_output_group()
    nt.links.new(tex.outputs['Color'], sep.inputs[0])
    nt.links.new(sep.outputs[0], grp.inputs['Occlusion'])


def resize_images():
    for img in bpy.data.images:
        if img.source != 'FILE' or img.size[0] == 0:
            continue
        key = next((k for k in SIZES if img.name.startswith(k)), None)
        if key is None:
            continue
        target = SIZES[key]
        if 'normal' in img.name.lower() and key != 'UpCar_M1':
            target = min(target, 1024)
        if img.size[0] > target:
            img.scale(target, target)


def run(path, log=print):
    for o in list(bpy.data.objects):
        if o.type in ('CAMERA', 'LIGHT'):
            bpy.data.objects.remove(o, do_unlink=True)
    for m in bpy.data.materials:
        add_ao(m)
    resize_images()
    tris = 0
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.data.calc_loop_triangles()
            tris += len(o.data.loop_triangles)
    log('triangles', tris)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        export_apply=True,
        export_yup=True,
        export_extras=True,
        export_materials='EXPORT',
        export_normals=True,
        export_texcoords=True,
        export_image_format='WEBP',
        export_image_quality=82,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=7,
        export_draco_position_quantization=16,
        export_draco_normal_quantization=12,
        export_draco_texcoord_quantization=14,
        export_cameras=False,
        export_lights=False,
    )
    log('exported', path, os.path.getsize(path) // 1024, 'KB')
