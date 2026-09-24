"""Quick Workbench preview renders for comparing the model against references."""
import math
import bpy
from mathutils import Vector, Euler
from bpy_extras.object_utils import world_to_camera_view


def setup(res=(1600, 900)):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'MATERIAL'
    sh.show_cavity = True
    sh.cavity_type = 'WORLD'
    sh.show_specular_highlight = True
    sh.background_type = 'VIEWPORT'
    sh.background_color = (0.55, 0.58, 0.6)
    sc.display.shading.show_object_outline = False
    colors = {
        'paint': (0.16, 0.17, 0.19, 1), 'chrome': (0.85, 0.86, 0.88, 1),
        'glass': (0.25, 0.32, 0.36, 1), 'tire': (0.03, 0.03, 0.03, 1),
        'rubber': (0.02, 0.02, 0.02, 1), 'lens_red': (0.6, 0.02, 0.02, 1),
        'lens_clear': (0.9, 0.9, 0.85, 1), 'lens_amber': (0.9, 0.45, 0.05, 1),
        'headlamp': (0.95, 0.95, 0.9, 1), 'tan': (0.62, 0.52, 0.38, 1),
        'vinyl': (0.03, 0.03, 0.035, 1), 'carpet': (0.04, 0.04, 0.04, 1),
        'black': (0.01, 0.01, 0.01, 1), 'engine': (0.8, 0.3, 0.05, 1),
    }
    for m in bpy.data.materials:
        for k, c in colors.items():
            if m.name.startswith(k):
                m.diffuse_color = c
                m.metallic = 1.0 if k == 'chrome' else 0.0
                m.roughness = 0.1 if k in ('chrome', 'paint', 'glass') else 0.6


def camera(name, loc, target, ortho=None, lens=50):
    cam_data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = ortho
    else:
        cam_data.lens = lens
    cam_data.clip_end = 200
    return cam


def render(cam, path):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def project(cam, point):
    sc = bpy.context.scene
    co = world_to_camera_view(sc, cam, Vector(point))
    return (co.x * sc.render.resolution_x, (1 - co.y) * sc.render.resolution_y)


def standard_views(outdir, prefix='v'):
    import dims as D
    info = {}
    setup((1720, 908))
    # driver side, front at image left (matches references/full-side-view.webp)
    cam = camera('cam_side', (0, 30, 0.7), (0, 0, 0.7), ortho=6.2)
    render(cam, f'{outdir}/{prefix}_side.png')
    info['side'] = [project(cam, (D.X_FA, D.Y_WHEEL, D.WHEEL_Z)),
                    project(cam, (D.X_RA, D.Y_WHEEL, D.WHEEL_Z))]
    cam = camera('cam_front', (30, 0, 0.75), (0, 0, 0.75), ortho=2.6)
    render(cam, f'{outdir}/{prefix}_front.png')
    cam = camera('cam_rear', (-30, 0, 0.75), (0, 0, 0.75), ortho=2.6)
    render(cam, f'{outdir}/{prefix}_rear.png')
    cam = camera('cam_top', (0, 0, 30), (0, 0, 0), ortho=6.2)
    cam.rotation_euler = (0, 0, math.radians(90))
    render(cam, f'{outdir}/{prefix}_top.png')
    # 3/4 front, low (like references/front-45deg-view.jpg)
    cam = camera('cam_f34', (5.2, 3.3, 0.9), (0.6, 0, 0.62), lens=40)
    render(cam, f'{outdir}/{prefix}_f34.png')
    # 3/4 rear (like references/back-view-45deg.jpg)
    cam = camera('cam_r34', (-6.0, 3.0, 1.2), (-0.8, 0.3, 0.7), lens=45)
    render(cam, f'{outdir}/{prefix}_r34.png')
    return info
