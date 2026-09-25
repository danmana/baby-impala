import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

/** Stroke-drawn capitals for neon tubing (unit box: x 0..0.6, y 0..1). */
const GLYPHS: Record<string, [number, number][][]> = {
  V: [[[0, 1], [0.3, 0], [0.6, 1]]],
  A: [[[0, 0], [0.3, 1], [0.6, 0]], [[0.12, 0.38], [0.48, 0.38]]],
  C: [[[0.6, 0.85], [0.45, 1], [0.15, 1], [0, 0.8], [0, 0.2], [0.15, 0], [0.45, 0], [0.6, 0.15]]],
  N: [[[0, 0], [0, 1], [0.6, 0], [0.6, 1]]],
  Y: [[[0, 1], [0.3, 0.5], [0.6, 1]], [[0.3, 0.5], [0.3, 0]]],
  O: [[[0.15, 0], [0.45, 0], [0.6, 0.2], [0.6, 0.8], [0.45, 1], [0.15, 1], [0, 0.8], [0, 0.2], [0.15, 0]]],
};

function neonWord(word: string, size: number, spacing: number, mat: THREE.Material, radius: number) {
  const g = new THREE.Group();
  let x = 0;
  for (const ch of word) {
    const strokes = GLYPHS[ch];
    if (strokes) {
      for (const s of strokes) {
        const pts = s.map(([u, v]) => new THREE.Vector3(x + u * size, v * size, 0));
        const curve = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.05);
        const m = new THREE.Mesh(new THREE.TubeGeometry(curve, Math.max(10, pts.length * 12), radius, 8, false), mat);
        m.userData.letter = ch;
        g.add(m);
      }
    }
    x += size * 0.6 + spacing;
  }
  g.userData.width = x - spacing;
  return g;
}

function canvasTex(w: number, h: number, draw: (c: CanvasRenderingContext2D) => void) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  draw(c.getContext('2d')!);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

export interface MotelMaps {
  wall: { diff: THREE.Texture; nor: THREE.Texture; arm: THREE.Texture };
  walk: { diff: THREE.Texture; nor: THREE.Texture; arm: THREE.Texture };
  door: { diff: THREE.Texture; nor: THREE.Texture; arm: THREE.Texture };
  metal: { diff: THREE.Texture; nor: THREE.Texture; arm: THREE.Texture };
  roof: { diff: THREE.Texture; nor: THREE.Texture; arm: THREE.Texture };
}

type PBR = MotelMaps['wall'];

/** A textured material with its own repeat (textures are cloned so repeats don't clash). */
function pbr(set: PBR, repeat: [number, number], color: THREE.ColorRepresentation, extra: THREE.MeshStandardMaterialParameters = {}) {
  const clone = (t: THREE.Texture, srgb: boolean) => {
    const c = t.clone();
    c.wrapS = c.wrapT = THREE.RepeatWrapping;
    c.repeat.set(...repeat);
    c.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    c.anisotropy = 8;
    c.needsUpdate = true;
    return c;
  };
  const arm = clone(set.arm, false);
  return new THREE.MeshStandardMaterial({
    map: clone(set.diff, true), normalMap: clone(set.nor, false), roughnessMap: arm, aoMap: arm,
    color, roughness: 1, metalness: 0, ...extra,
  });
}

/** Box with UVs scaled to its real size, so tiling textures keep a constant texel density. */
function worldBox(w: number, h: number, d: number, tile: number) {
  const g = new THREE.BoxGeometry(w, h, d);
  const uv = g.getAttribute('uv') as THREE.BufferAttribute;
  const n = g.getAttribute('normal') as THREE.BufferAttribute;
  for (let i = 0; i < uv.count; i++) {
    const ax = Math.abs(n.getX(i)), ay = Math.abs(n.getY(i));
    const sx = ax > 0.5 ? d : w;
    const sy = ay > 0.5 ? d : h;
    uv.setXY(i, (uv.getX(i) * sx) / tile, (uv.getY(i) * sy) / tile);
  }
  return g;
}

/**
 * A run-down roadside motel close behind the car, with a buzzing, flickering
 * red VACANCY sign. Its light reaches the car through a rectangular area light
 * (shaped highlights in the paint and chrome) and a soft red fill.
 */
export class Motel {
  readonly group = new THREE.Group();
  /** lights live outside the toggled group so turning the motel on never changes the light count */
  readonly lights = new THREE.Group();
  readonly neonFill: THREE.PointLight;
  private neonMat: THREE.MeshStandardMaterial;
  private neonFlickerMat: THREE.MeshStandardMaterial;
  private noMat: THREE.MeshStandardMaterial;
  private tvMat: THREE.MeshStandardMaterial;
  private windowMats: THREE.MeshStandardMaterial[] = [];
  private lampMats: THREE.MeshStandardMaterial[] = [];
  private on = false;
  private fade = 0;
  private flickerT = 0;
  private burst = 0;
  private level = 1;
  reduced = false;
  /** the car-facing plane of the wall (camera must stay in front of it) */
  readonly wallZ = 4.35;

  constructor(maps: MotelMaps) {
    const g = this.group;
    g.name = 'motel';
    const Z = this.wallZ;
    const W = 22, X0 = -1;

    // ---------------------------------------------------------------- walls, plinth, walkway
    const wallMat = pbr(maps.wall, [1, 1], 0xd9d1b8, { envMapIntensity: 0.35 });
    const wall = new THREE.Mesh(worldBox(W, 3.3, 0.3, 1.25), wallMat);
    wall.position.set(X0, 1.65 + 0.16, Z + 0.15);
    wall.receiveShadow = true;
    g.add(wall);
    const plinthMat = pbr(maps.walk, [1, 1], 0x8f8a82);
    const plinth = new THREE.Mesh(worldBox(W, 0.32, 0.34, 1.4), plinthMat);
    plinth.position.set(X0, 0.16 + 0.16, Z + 0.13);
    g.add(plinth);
    const walkMat = pbr(maps.walk, [1, 1], 0xa9a49b, { envMapIntensity: 0.3 });
    const walk = new THREE.Mesh(worldBox(W, 0.16, 1.9, 1.5), walkMat);
    walk.position.set(X0, 0.08, Z - 0.95);
    walk.receiveShadow = true;
    walk.castShadow = true;
    g.add(walk);
    const curb = new THREE.Mesh(worldBox(W, 0.17, 0.12, 1.5), plinthMat);
    curb.position.set(X0, 0.085, Z - 1.9);
    g.add(curb);

    // ---------------------------------------------------------------- canopy, fascia, posts
    const roofMat = pbr(maps.roof, [1, 1], 0x6e6258, { metalness: 0.6 });
    const canopy = new THREE.Mesh(worldBox(W, 0.1, 2.15, 1.2), roofMat);
    canopy.position.set(X0, 2.82, Z - 1.0);
    canopy.castShadow = true;
    g.add(canopy);
    const soffit = new THREE.Mesh(new THREE.PlaneGeometry(W, 2.1),
      new THREE.MeshStandardMaterial({ color: 0x2a2724, roughness: 0.95 }));
    soffit.rotation.x = Math.PI / 2;
    soffit.position.set(X0, 2.765, Z - 1.0);
    g.add(soffit);
    const fasciaMat = pbr(maps.metal, [1, 1], 0x9a4a32, { metalness: 0.35 });
    const fascia = new THREE.Mesh(worldBox(W, 0.38, 0.06, 1.1), fasciaMat);
    fascia.position.set(X0, 2.72, Z - 2.08);
    g.add(fascia);
    const postMat = pbr(maps.metal, [0.3, 1.5], 0x5b574f, { metalness: 0.7 });
    for (let x = -10.4; x <= 8.6; x += 3.2) {
      const p = new THREE.Mesh(worldBox(0.09, 2.6, 0.09, 1), postMat);
      p.position.set(x, 1.46, Z - 1.98);
      p.castShadow = true;
      g.add(p);
    }

    // ---------------------------------------------------------------- rooms
    const doorTints = [0x3f6a68, 0x7a2e28, 0x3f6a68, 0x8a6a2a, 0x3f6a68, 0x7a2e28];
    const lit = [true, false, true, true, false, true];
    const trimMat = new THREE.MeshStandardMaterial({ color: 0xcfc6b0, roughness: 0.7 });
    const glassMat = new THREE.MeshPhysicalMaterial({ color: 0x0a0c0d, roughness: 0.05, metalness: 0, envMapIntensity: 1.2,
      transparent: true, opacity: 0.35 });
    const acMat = pbr(maps.metal, [0.6, 0.4], 0x9b9890, { metalness: 0.55 });
    for (let i = 0; i < 6; i++) {
      const x = -8.6 + i * 3.2;
      const num = 12 + i;
      // door with frame and a brass number
      const doorMat = pbr(maps.door, [0.8, 1.6], doorTints[i], { envMapIntensity: 0.3 });
      const door = new THREE.Mesh(new RoundedBoxGeometry(0.95, 2.1, 0.05, 2, 0.01), doorMat);
      door.position.set(x, 1.05 + 0.16, Z - 0.02);
      g.add(door);
      for (const [w, h, dx, dy] of [[0.08, 2.2, -0.515, 0], [0.08, 2.2, 0.515, 0], [1.11, 0.08, 0, 1.11]] as number[][]) {
        const f = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.07), trimMat);
        f.position.set(x + dx, 1.05 + 0.16 + dy, Z - 0.03);
        g.add(f);
      }
      const plate = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.12), new THREE.MeshStandardMaterial({
        map: canvasTex(128, 80, (c) => {
          c.fillStyle = '#9c7a3a';
          c.fillRect(0, 0, 128, 80);
          c.fillStyle = '#2b1d0c';
          c.font = 'bold 58px Georgia, serif';
          c.textAlign = 'center';
          c.textBaseline = 'middle';
          c.fillText(String(num), 64, 44);
        }), metalness: 0.8, roughness: 0.35,
      }));
      plate.rotation.y = Math.PI;
      plate.position.set(x, 1.72, Z - 0.05);
      g.add(plate);
      const knob = new THREE.Mesh(new THREE.SphereGeometry(0.03, 12, 8), new THREE.MeshStandardMaterial({ color: 0xb08d45, metalness: 1, roughness: 0.3 }));
      knob.position.set(x + 0.36, 1.12, Z - 0.07);
      g.add(knob);

      // window: frame, glass, curtain behind (lit rooms glow warm)
      const wx = x + 1.45;
      const curtainTex = canvasTex(256, 192, (c) => {
        const gr = c.createLinearGradient(0, 0, 256, 0);
        gr.addColorStop(0, '#caa06a');
        gr.addColorStop(0.5, '#e8c28a');
        gr.addColorStop(1, '#b98a52');
        c.fillStyle = gr;
        c.fillRect(0, 0, 256, 192);
        for (let k = 0; k < 18; k++) {
          c.fillStyle = `rgba(80,45,15,${0.15 + (k % 3) * 0.06})`;
          c.fillRect(k * 14 + (k % 2) * 3, 0, 5, 192);
        }
        c.fillStyle = 'rgba(0,0,0,0.25)';
        c.fillRect(122, 0, 12, 192);
      });
      const wm = new THREE.MeshStandardMaterial({ color: 0x151210, map: curtainTex, emissive: 0xffffff, emissiveMap: curtainTex,
        emissiveIntensity: 0, roughness: 0.9 });
      wm.userData.base = lit[i] ? 1.1 : 0.0;
      this.windowMats.push(wm);
      const curtain = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 1.1), wm);
      curtain.rotation.y = Math.PI;
      // just proud of the wall face (the wall has no openings), behind the glass
      curtain.position.set(wx, 1.55, Z - 0.006);
      g.add(curtain);
      const glass = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 1.1), glassMat);
      glass.rotation.y = Math.PI;
      glass.position.set(wx, 1.55, Z - 0.025);
      g.add(glass);
      for (const [w, h, dx, dy] of [[1.62, 0.07, 0, 0.585], [1.62, 0.1, 0, -0.6], [0.07, 1.2, -0.78, 0], [0.07, 1.2, 0.78, 0], [0.04, 1.1, 0, 0]] as number[][]) {
        const f = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.08), trimMat);
        f.position.set(wx + dx, 1.55 + dy, Z - 0.03);
        g.add(f);
      }
      // window AC unit with a grille
      const ac = new THREE.Mesh(new RoundedBoxGeometry(0.62, 0.4, 0.48, 2, 0.02), acMat);
      ac.position.set(wx, 0.72, Z - 0.26);
      ac.castShadow = true;
      g.add(ac);
      const grille = new THREE.Mesh(new THREE.PlaneGeometry(0.52, 0.3), new THREE.MeshStandardMaterial({
        map: canvasTex(128, 80, (c) => {
          c.fillStyle = '#2c2b28';
          c.fillRect(0, 0, 128, 80);
          c.fillStyle = '#6d6a62';
          for (let k = 0; k < 80; k += 5) c.fillRect(0, k, 128, 2);
        }), metalness: 0.6, roughness: 0.6,
      }));
      grille.rotation.y = Math.PI;
      grille.position.set(wx, 0.72, Z - 0.505);
      g.add(grille);
      // porch lamp
      const lampMat = new THREE.MeshStandardMaterial({ color: 0x3a3632, emissive: 0xffc27a, emissiveIntensity: 0, roughness: 0.4 });
      lampMat.userData.base = lit[i] ? 2.6 : 0.25;
      this.lampMats.push(lampMat);
      const lamp = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.09, 0.16, 16), lampMat);
      lamp.position.set(x + 0.75, 2.38, Z - 0.1);
      g.add(lamp);
    }
    this.tvMat = this.windowMats[3];

    // ice machine at the end of the walkway
    const iceBody = new THREE.Mesh(new RoundedBoxGeometry(0.9, 1.6, 0.7, 3, 0.03), pbr(maps.metal, [0.6, 1], 0xa3a6a6, { metalness: 0.7 }));
    iceBody.position.set(7.2, 0.96, Z - 0.5);
    iceBody.castShadow = true;
    g.add(iceBody);
    const icePanel = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.5), new THREE.MeshStandardMaterial({
      map: canvasTex(256, 200, (c) => {
        c.fillStyle = '#0d2330';
        c.fillRect(0, 0, 256, 200);
        c.fillStyle = '#bfeaff';
        c.font = 'bold 96px Arial Black, Arial';
        c.textAlign = 'center';
        c.fillText('ICE', 128, 132);
      }), emissive: 0x9fe0ff, emissiveIntensity: 0, roughness: 0.3,
    }));
    icePanel.material.userData.base = 1.2;
    this.lampMats.push(icePanel.material);
    icePanel.rotation.y = Math.PI;
    icePanel.position.set(7.2, 1.3, Z - 0.856);
    g.add(icePanel);

    // ---------------------------------------------------------------- the sign
    const sign = new THREE.Group();
    sign.position.set(-1.3, 2.55, Z - 2.45);
    sign.scale.setScalar(0.8);
    const boxMat = pbr(maps.metal, [1.2, 0.6], 0x2a2320, { metalness: 0.4 });
    const cabinet = new THREE.Mesh(new RoundedBoxGeometry(3.4, 1.5, 0.3, 3, 0.04), boxMat);
    cabinet.position.set(0, 0.1, 0.14);
    cabinet.castShadow = true;
    sign.add(cabinet);
    const face = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 1.3), new THREE.MeshStandardMaterial({ color: 0x120e0c, roughness: 0.85, metalness: 0.1 }));
    face.rotation.y = Math.PI;
    face.position.set(0, 0.1, -0.012);
    sign.add(face);
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.08, 2.4, 14), postMat);
    pole.position.set(0, -1.7, 0.14);
    pole.castShadow = true;
    sign.add(pole);
    const motelWord = canvasTex(512, 128, (c) => {
      c.fillStyle = '#120e0c';
      c.fillRect(0, 0, 512, 128);
      c.fillStyle = '#ddcfad';
      c.font = 'bold 96px Georgia, serif';
      c.textAlign = 'center';
      c.textBaseline = 'middle';
      c.fillText('MOTEL', 256, 70);
      // chipped paint
      for (let k = 0; k < 90; k++) {
        c.fillStyle = 'rgba(18,14,12,0.85)';
        c.fillRect(Math.random() * 512, Math.random() * 128, 2 + Math.random() * 5, 1 + Math.random() * 3);
      }
    });
    const motelPlate = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 0.52), new THREE.MeshStandardMaterial({ map: motelWord, roughness: 0.7 }));
    motelPlate.rotation.y = Math.PI;
    motelPlate.position.set(0, 0.48, -0.02);
    sign.add(motelPlate);

    // glass tubes: bright core when lit, a dull red glass when off
    this.neonMat = new THREE.MeshStandardMaterial({ color: 0x3a0806, emissive: 0xff2412, emissiveIntensity: 0, roughness: 0.25 });
    this.neonFlickerMat = this.neonMat.clone();
    this.noMat = new THREE.MeshStandardMaterial({ color: 0x2a0806, emissive: 0xff2412, emissiveIntensity: 0, roughness: 0.3 });
    const word = neonWord('VACANCY', 0.38, 0.06, this.neonMat, 0.017);
    word.children.forEach((m, idx) => {
      if (idx >= word.children.length - 3) (m as THREE.Mesh).material = this.neonFlickerMat;
    });
    const no = neonWord('NO', 0.3, 0.05, this.noMat, 0.015);
    const gap = 0.14;
    const total = word.userData.width + gap + no.userData.width;
    const left = total / 2; // text faces the car (-Z): half a turn makes it read left to right from there
    no.rotation.y = Math.PI;
    no.position.set(left, -0.3, -0.03);
    word.rotation.y = Math.PI;
    word.position.set(left - no.userData.width - gap, -0.36, -0.03);
    sign.add(word, no);
    // tube supports
    for (let k = 0; k < 6; k++) {
      const s = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.04, 6), new THREE.MeshStandardMaterial({ color: 0x777777, metalness: 1, roughness: 0.4 }));
      s.rotation.x = Math.PI / 2;
      s.position.set(-1.4 + k * 0.52, -0.2, -0.01);
      sign.add(s);
    }
    g.add(sign);

    this.neonFill = new THREE.PointLight(0xff2a1a, 0, 9, 1.8);
    this.neonFill.position.set(-1.3, 2.25, Z - 2.8);
    // (no RectAreaLight: its LTC shading costs every car fragment even at zero
    // intensity; the neon's reflection in the paint comes from the env map)
    this.lights.add(this.neonFill);

    g.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) {
        m.receiveShadow = true;
        m.raycast = () => undefined;
      }
    });
    g.visible = false;
  }

  setOn(on: boolean) {
    this.on = on;
    if (on) this.group.visible = true;
  }

  get isOn() { return this.on; }

  /** night: 1 at night, ~0 in daylight (lit windows and lamps matter less) */
  update(dt: number, t: number, night: number) {
    this.fade += ((this.on ? 1 : 0) - this.fade) * Math.min(1, dt * 3);
    if (!this.on && this.fade < 0.01) {
      this.group.visible = false;
      this.neonFill.intensity = 0;
      return;
    }
    // neon: mostly steady with a mains buzz, then bursts of stutter
    this.flickerT -= dt;
    if (this.flickerT <= 0) {
      this.burst = this.reduced ? 0 : 0.25 + Math.random() * 0.6;
      this.flickerT = 2.5 + Math.random() * 6;
    }
    let target = 1;
    if (this.burst > 0) {
      this.burst -= dt;
      target = Math.random() < 0.45 ? 0.08 : 1;
    }
    const hum = 0.96 + 0.04 * Math.sin(t * 120 * Math.PI);
    this.level += (target - this.level) * (target < this.level ? 0.9 : 0.5);
    const lv = this.level * hum * this.fade;
    const glow = 3.6 * (0.45 + 0.55 * night);
    this.neonMat.emissiveIntensity = glow * lv;
    const flaky = Math.sin(t * 13.7) > 0.93 || (this.burst > 0 && Math.random() < 0.5) ? 0.05 : 1;
    this.neonFlickerMat.emissiveIntensity = glow * lv * (this.reduced ? 1 : flaky);
    this.noMat.emissiveIntensity = 0.05 * this.fade;
    this.neonFill.intensity = 14 * lv * night;
    for (const m of this.windowMats) m.emissiveIntensity = m.userData.base * this.fade * (0.25 + 0.75 * night);
    for (const m of this.lampMats) m.emissiveIntensity = m.userData.base * this.fade * (0.2 + 0.8 * night);
    // someone in room 15 is watching TV
    const tv = 0.5 + 0.35 * Math.sin(t * 7.1) * Math.sin(t * 2.3) + (Math.random() < 0.05 ? 0.3 : 0);
    this.tvMat.emissive.setRGB(0.55 + 0.2 * tv, 0.7 + 0.2 * tv, 1.0);
    this.tvMat.emissiveIntensity = (0.4 + tv * 0.5) * this.fade * (0.3 + 0.7 * night);
  }
}
