"""Download the CC0 source assets used to build the model and the scene.

They are not kept in git (a few hundred MB). Everything comes from Poly Haven
(polyhaven.com) and ambientCG (ambientcg.com), both CC0.

    python3 tools/fetch_assets.py            # everything
    python3 tools/fetch_assets.py models     # just the Poly Haven models

Files land in assets-src/polyhaven/{models,tex} and assets-src/ambientcg/<Asset>/.
"""
import io
import json
import os
import sys
import urllib.request
import zipfile

ROOT = os.path.join(os.path.dirname(__file__), '..', 'assets-src')
UA = {'User-Agent': 'baby-impala-fetch/1.0'}

# trunk arsenal props (glTF, 1k textures)
PH_MODELS = [
    'ammo_box', 'binder_notebook', 'bolt_action_rifle_7_62', 'can_rusted', 'crowbar_01', 'fish_knife',
    'hatchet', 'machete', 'medical_tape', 'ornate_medieval_dagger', 'russian_food_cans_01',
    'service_pistol', 'small_oil_can_01', 'vintage_flashlight', 'wine_bottles_01', 'wooden_axe_02',
]
# ground and motel surfaces (2k: diffuse, normal, roughness, AO)
PH_TEXTURES = [
    'asphalt_02', 'asphalt_04', 'bitumen', 'concrete_block_wall_02', 'concrete_pavement_02', 'painted_brick',
    'painted_plaster_wall', 'rough_pine_door', 'rusty_corrugated_iron', 'rusty_painted_metal',
    'weathered_peeling_timber',
]
# lighting presets (public/hdri/moon|sunset|day.hdr are these at 1k)
PH_HDRIS = ['narrow_moonlit_road', 'goegap_road', 'mall_parking_lot']
# prop materials and the paper for the journal UI
ACG = ['Cardboard001', 'Fabric029', 'Leather014', 'Leather032', 'Metal009', 'Paper002', 'Paper004', 'Paper006', 'Planks039']


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
        return r.read()


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)
    print('  ', os.path.relpath(path, ROOT), f'{len(data) // 1024} KB')


def ph_files(asset):
    return json.loads(get(f'https://api.polyhaven.com/files/{asset}'))


def fetch_models():
    for a in PH_MODELS:
        print(a)
        g = ph_files(a)['gltf']['1k']['gltf']
        out = os.path.join(ROOT, 'polyhaven', 'models', a)
        save(os.path.join(out, f'{a}.gltf'), get(g['url']))
        for rel, inc in g['include'].items():
            save(os.path.join(out, rel), get(inc['url']))


def fetch_textures():
    for a in PH_TEXTURES:
        print(a)
        f = ph_files(a)
        for kind, key in (('diff', 'Diffuse'), ('nor_gl', 'nor_gl'), ('rough', 'Rough'), ('ao', 'AO')):
            src = f[key]['2k']['jpg']['url']
            save(os.path.join(ROOT, 'polyhaven', 'tex', f'{a}_{kind}_2k.jpg'), get(src))


def fetch_hdris():
    for a in PH_HDRIS:
        print(a)
        save(os.path.join(ROOT, 'polyhaven', f'{a}_1k.hdr'), get(ph_files(a)['hdri']['1k']['hdr']['url']))


def fetch_ambientcg():
    for a in ACG:
        print(a)
        z = zipfile.ZipFile(io.BytesIO(get(f'https://ambientcg.com/get?file={a}_2K-JPG.zip')))
        for n in z.namelist():
            if n.lower().endswith('.jpg'):
                save(os.path.join(ROOT, 'ambientcg', a, n), z.read(n))


if __name__ == '__main__':
    jobs = {'models': fetch_models, 'textures': fetch_textures, 'hdris': fetch_hdris, 'ambientcg': fetch_ambientcg}
    for name in (sys.argv[1:] or jobs):
        jobs[name]()
