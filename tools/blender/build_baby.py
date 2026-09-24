"""Build Baby — the 1967 Chevrolet Impala 4-door hardtop — and export a GLB.

Base body: "Chevrolet Impala 1967" by Eques_inferno (CC BY 4.0), adapted
into Baby with the modules in this folder.

Run:  npm run model                    (full build + export)
      BABY_PREVIEW=1 npm run model     (also render EEVEE previews into .work/)
"""
import os
import sys
import json
import time
import importlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import lib as L  # noqa: E402
import source_model as SM  # noqa: E402
import cleanup  # noqa: E402
import panels as PN  # noqa: E402
import baby_parts  # noqa: E402

t0 = time.time()


def log(*a):
    print(f'[{time.time() - t0:6.1f}s]', *a, flush=True)


L.reset_scene()
log('import source model')
meshes, scale, M = SM.import_source()
fa, ra = SM.axles(M)
L.set_collection('Baby')
log('cleanup')
cleanup.run(fa, ra)
log('panels')
body, panels = PN.run()
log('baby parts')
baby_parts.build(fa, ra)

OPTIONAL = ['trunk', 'engine', 'interior']
stages = os.environ.get('BABY_STAGES', 'all')
stages = OPTIONAL if stages == 'all' else [s for s in stages.split(',') if s in OPTIONAL]
for st in stages:
    if os.path.exists(os.path.join(HERE, f'{st}.py')):
        log(st)
        importlib.import_module(st).build(fa, ra)

if os.environ.get('BABY_PREVIEW'):
    import preview_eevee  # noqa: E402
    preview_eevee.render_all(os.path.join(ROOT, '.work'), os.environ.get('BABY_PREFIX', 'b'))
    log('preview rendered')

if os.environ.get('BABY_SAVE_BLEND'):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, '.work', 'baby.blend'))

if not os.environ.get('BABY_NO_EXPORT'):
    import export  # noqa: E402
    export.run(os.path.join(ROOT, 'public', 'models', 'baby.glb'), log)
