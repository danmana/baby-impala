import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { Materials } from './materials';
import { Plate, drawKansas, drawOhio } from './plates';
import { drawDevilsTrap, drawDial, drawInitials } from './textures';

export interface CarParts {
  root: THREE.Group;
  byName: Map<string, THREE.Object3D>;
  meshes: THREE.Mesh[];
  plateFront: Plate;
  plateRear: Plate;
}

const OWN_MATS = new Set([
  'chrome', 'mirror', 'steel', 'steel_dark', 'gunmetal', 'silver', 'nickel', 'iron', 'brass', 'bowtie', 'drum',
  'exhaust', 'wood', 'wood_dark', 'wood_trim', 'leather', 'leather_dark', 'antler', 'ivory', 'felt', 'felt_red',
  'carpet', 'carpet_gray', 'strap', 'twine', 'sage', 'feather', 'bottle_glass', 'blood_glass', 'oil_glass',
  'salt_blue', 'ammo_green', 'cardboard', 'shell_red', 'paper', 'plastic_black', 'red_plastic', 'zippo_blue',
  'tape', 'burlap', 'canvas_olive', 'bead_blue', 'led_red', 'led_green', 'engine', 'engine_dark', 'underbody',
  'radiator', 'wire_red', 'spot_lens', 'black', 'rubber', 'plastic_olive', 'dial', 'lens_clear', 'lego_red',
  'lego_blue', 'lego_yellow', 'army_green', 'trap_paint', 'paint', 'tire',
]);

function tex(canvas: HTMLCanvasElement, srgb = true) {
  const t = new THREE.CanvasTexture(canvas);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

/** Spotlight lens: a hot filament, a reflector glow and concentric Fresnel rings. */
function drawLens(): HTMLCanvasElement {
  const S = 256;
  const c = document.createElement('canvas');
  c.width = c.height = S;
  const g = c.getContext('2d')!;
  const cx = S / 2;
  const bg = g.createRadialGradient(cx, cx, 0, cx, cx, cx);
  bg.addColorStop(0, '#fff8ea');
  bg.addColorStop(0.18, '#ffe7c0');
  bg.addColorStop(0.55, '#b58a56');
  bg.addColorStop(1, '#2a1c10');
  g.fillStyle = bg;
  g.fillRect(0, 0, S, S);
  g.globalCompositeOperation = 'multiply';
  for (let r = 10; r < cx; r += 7) {
    g.strokeStyle = `rgba(90,70,50,${0.18 + 0.2 * (r / cx)})`;
    g.lineWidth = 2;
    g.beginPath();
    g.arc(cx, cx, r, 0, Math.PI * 2);
    g.stroke();
  }
  g.globalCompositeOperation = 'lighter';
  const core = g.createRadialGradient(cx, cx, 0, cx, cx, 26);
  core.addColorStop(0, 'rgba(255,255,255,1)');
  core.addColorStop(1, 'rgba(255,240,210,0)');
  g.fillStyle = core;
  g.fillRect(0, 0, S, S);
  return c;
}

export async function loadCar(buffer: ArrayBuffer, mats: Materials): Promise<CarParts> {
  const draco = new DRACOLoader(); // decoder files are bundled by Vite from three/examples
  const loader = new GLTFLoader();
  loader.setDRACOLoader(draco);
  const gltf = await loader.parseAsync(buffer, '');
  draco.dispose();
  await Promise.all([
    document.fonts.load('330px "League Gothic"'),
    document.fonts.load('40px "Special Elite"'),
  ]).catch(() => undefined);

  const root = new THREE.Group();
  root.name = 'baby';
  root.add(gltf.scene);
  const byName = new Map<string, THREE.Object3D>();
  const meshes: THREE.Mesh[] = [];

  // painted textures on our own parts
  const trap = mats.get('trap_paint') as THREE.MeshStandardMaterial;
  trap.map = tex(drawDevilsTrap());
  trap.needsUpdate = true;
  const trim = new THREE.MeshStandardMaterial({ map: tex(drawInitials()), roughness: 0.6, envMapIntensity: 0.4 });
  const lens = mats.get('spot_lens') as THREE.MeshPhysicalMaterial;
  const lensTex = tex(drawLens());
  lens.emissiveMap = lensTex;
  lens.emissive.set(0xffffff);
  lens.needsUpdate = true;
  const dialTex = tex(drawDial());
  const dial = new THREE.MeshStandardMaterial({ map: dialTex, emissiveMap: dialTex, emissive: 0xffd6a0, emissiveIntensity: 0, roughness: 0.3 });
  mats.registerLamp('dial', dial);
  mats.extra.push(trim, dial);

  gltf.scene.traverse((o) => {
    byName.set(o.name, o);
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    meshes.push(m);
    const src = m.material as THREE.MeshStandardMaterial;
    const key = src.name.replace(/\.\d+$/, '');
    if (m.name.startsWith('initials_trim')) m.material = trim;
    else if (m.name.startsWith('tape_deck_dial')) m.material = dial;
    else if (OWN_MATS.has(key)) m.material = mats.get(key)!;
    else m.material = mats.upgrade(src, m.name);
    // refractive glass (KHR_materials_transmission from the scanned bottles)
    // makes three render the whole scene a second time; alpha glass reads the same
    const phys = m.material as THREE.MeshPhysicalMaterial;
    if (phys.isMeshPhysicalMaterial && phys.transmission > 0) {
      phys.transmission = 0;
      phys.transparent = true;
      phys.opacity = 0.42;
      phys.depthWrite = false;
      phys.roughness = Math.min(phys.roughness, 0.08);
    }
    const mat = m.material as THREE.Material;
    const glass = mat.transparent;
    m.castShadow = !glass;
    m.receiveShadow = true;
    if (glass) m.renderOrder = 2;
  });

  // licence plates on the stock plate mounts
  const texK = tex(drawKansas());
  const texO = tex(drawOhio());
  gltf.scene.updateMatrixWorld(true);
  const mkPlate = (anchor: string) => {
    const p = new Plate(texK, texO, null);
    const holder = new THREE.Group();
    holder.name = `${anchor}_holder`;
    const a = byName.get(anchor);
    if (a) {
      a.getWorldPosition(holder.position);
      // outward normal stored by the Blender build (Blender axes: x, y, z -> three: x, z, -y)
      const bn = (a.userData.normal as number[] | undefined) ?? [anchor.includes('front') ? 1 : -1, 0, 0];
      const n = new THREE.Vector3(bn[0], bn[2], -bn[1]).normalize();
      holder.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
      // keep the plate's text upright
      const up = new THREE.Vector3(0, 1, 0).applyQuaternion(holder.quaternion);
      const want = new THREE.Vector3(0, 1, 0).sub(n.clone().multiplyScalar(n.y)).normalize();
      const roll = Math.atan2(new THREE.Vector3().crossVectors(up, want).dot(n), up.dot(want));
      holder.rotateZ(roll);
    }
    holder.add(p.pivot);
    root.add(holder);
    p.pivot.traverse((c) => {
      if ((c as THREE.Mesh).isMesh) {
        c.userData.hotspot = 'plates';
        meshes.push(c as THREE.Mesh);
      }
    });
    return p;
  };
  const plateFront = mkPlate('anchor_plate_front');
  const plateRear = mkPlate('anchor_plate_rear');
  return { root, byName, meshes, plateFront, plateRear };
}
