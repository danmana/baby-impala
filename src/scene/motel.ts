import * as THREE from 'three';

/** Stroke-drawn capitals for neon tubing (unit box: x 0..0.6, y 0..1). */
const GLYPHS: Record<string, [number, number][][]> = {
  V: [[[0, 1], [0.3, 0], [0.6, 1]]],
  A: [[[0, 0], [0.3, 1], [0.6, 0]], [[0.12, 0.38], [0.48, 0.38]]],
  C: [[[0.6, 0.85], [0.45, 1], [0.15, 1], [0, 0.8], [0, 0.2], [0.15, 0], [0.45, 0], [0.6, 0.15]]],
  N: [[[0, 0], [0, 1], [0.6, 0], [0.6, 1]]],
  Y: [[[0, 1], [0.3, 0.5], [0.6, 1]], [[0.3, 0.5], [0.3, 0]]],
  O: [[[0.15, 0], [0.45, 0], [0.6, 0.2], [0.6, 0.8], [0.45, 1], [0.15, 1], [0, 0.8], [0, 0.2], [0.15, 0]]],
  M: [[[0, 0], [0, 1], [0.3, 0.45], [0.6, 1], [0.6, 0]]],
  T: [[[0, 1], [0.6, 1]], [[0.3, 1], [0.3, 0]]],
  E: [[[0.6, 1], [0, 1], [0, 0], [0.6, 0]], [[0, 0.5], [0.45, 0.5]]],
  L: [[[0, 1], [0, 0], [0.6, 0]]],
};

function neonWord(word: string, size: number, spacing: number, mat: THREE.Material, radius = 0.02) {
  const g = new THREE.Group();
  let x = 0;
  for (const ch of word) {
    const strokes = GLYPHS[ch];
    if (strokes) {
      for (const s of strokes) {
        const pts = s.map(([u, v]) => new THREE.Vector3(x + u * size, v * size, 0));
        const curve = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.05);
        const geo = new THREE.TubeGeometry(curve, Math.max(8, pts.length * 10), radius, 6, false);
        const m = new THREE.Mesh(geo, mat);
        m.userData.letter = ch;
        g.add(m);
      }
    }
    x += size * 0.6 + spacing;
  }
  g.userData.width = x - spacing;
  return g;
}

function canvasTex(w: number, h: number, draw: (c: CanvasRenderingContext2D) => void, repeat?: [number, number]) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  draw(c.getContext('2d')!);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  if (repeat) {
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(...repeat);
  }
  t.anisotropy = 4;
  return t;
}

function rnd(seed: number) {
  let s = seed;
  return () => ((s = (s * 16807) % 2147483647) / 2147483647);
}

/**
 * Run-down roadside motel close behind the car, with a buzzing, flickering
 * red VACANCY sign. The sign's light reaches the car through a RectAreaLight
 * (shaped reflections in the paint and chrome) and a point light.
 */
export class Motel {
  readonly group = new THREE.Group();
  readonly neonLight: THREE.RectAreaLight;
  readonly neonFill: THREE.PointLight;
  readonly windowLight: THREE.PointLight;
  private neonMat: THREE.MeshStandardMaterial;
  private neonFlickerMat: THREE.MeshStandardMaterial;
  private noMat: THREE.MeshStandardMaterial;
  private tvMat: THREE.MeshStandardMaterial;
  private windowMats: THREE.MeshStandardMaterial[] = [];
  private on = false;
  private fade = 0;
  private flickerT = 0;
  private burst = 0;
  private level = 1;
  reduced = false;
  /** the car-facing plane of the wall (camera must stay in front of it) */
  readonly wallZ = 4.35;

  constructor(env: THREE.Texture | null) {
    const g = this.group;
    g.name = 'motel';
    const Z = this.wallZ;
    const r = rnd(42);

    // painted cinder block with grime
    const wallTex = canvasTex(1024, 512, (c) => {
      c.fillStyle = '#6f7a6e';
      c.fillRect(0, 0, 1024, 512);
      for (let y = 0; y < 512; y += 32) {
        for (let x = (y / 32) % 2 ? -32 : 0; x < 1024; x += 64) {
          const v = 100 + r() * 30;
          c.fillStyle = `rgba(${v},${v + 12},${v},0.25)`;
          c.fillRect(x + 1, y + 1, 62, 30);
        }
        c.fillStyle = 'rgba(40,40,36,0.35)';
        c.fillRect(0, y, 1024, 2);
      }
      for (let i = 0; i < 60; i++) {
        c.fillStyle = `rgba(30,26,20,${0.05 + r() * 0.12})`;
        const x = r() * 1024;
        c.fillRect(x, 0, 2 + r() * 12, 512 * (0.3 + r() * 0.7));
      }
      const gr = c.createLinearGradient(0, 380, 0, 512);
      gr.addColorStop(0, 'rgba(20,18,14,0)');
      gr.addColorStop(1, 'rgba(20,18,14,0.6)');
      c.fillStyle = gr;
      c.fillRect(0, 0, 1024, 512);
    }, [3, 1]);
    const wallMat = new THREE.MeshStandardMaterial({ map: wallTex, roughness: 0.95, envMap: env, envMapIntensity: 0.3 });
    const wall = new THREE.Mesh(new THREE.BoxGeometry(20, 3.3, 0.3), wallMat);
    wall.position.set(-1, 1.65, Z + 0.15);
    wall.receiveShadow = true;
    g.add(wall);

    // walkway
    const walk = new THREE.Mesh(new THREE.BoxGeometry(20, 0.16, 1.9),
      new THREE.MeshStandardMaterial({ color: 0x3a3a38, roughness: 0.9, envMap: env, envMapIntensity: 0.2 }));
    walk.position.set(-1, 0.08, Z - 0.95);
    walk.receiveShadow = true;
    g.add(walk);

    // canopy + fascia + posts
    const fasciaTex = canvasTex(1024, 64, (c) => {
      c.fillStyle = '#7b2f22';
      c.fillRect(0, 0, 1024, 64);
      for (let i = 0; i < 140; i++) {
        c.fillStyle = `rgba(220,200,170,${r() * 0.15})`;
        c.fillRect(r() * 1024, r() * 64, 4 + r() * 30, 1 + r() * 4);
      }
    }, [4, 1]);
    const canopy = new THREE.Mesh(new THREE.BoxGeometry(20, 0.12, 2.1),
      new THREE.MeshStandardMaterial({ color: 0x1e1d1b, roughness: 0.9, envMap: env, envMapIntensity: 0.2 }));
    canopy.position.set(-1, 2.72, Z - 1.0);
    g.add(canopy);
    const fascia = new THREE.Mesh(new THREE.BoxGeometry(20, 0.34, 0.06),
      new THREE.MeshStandardMaterial({ map: fasciaTex, roughness: 0.8, envMap: env, envMapIntensity: 0.4 }));
    fascia.position.set(-1, 2.64, Z - 2.05);
    g.add(fascia);
    const postMat = new THREE.MeshStandardMaterial({ color: 0x2b2b2a, roughness: 0.5, metalness: 0.8, envMap: env });
    for (let x = -10; x <= 8; x += 3.2) {
      const p = new THREE.Mesh(new THREE.BoxGeometry(0.08, 2.6, 0.08), postMat);
      p.position.set(x, 1.3, Z - 1.95);
      g.add(p);
    }

    // rooms: door + window, some lit
    const doorColors = ['#7a2a24', '#2f5a5c', '#7a2a24', '#6b5a2a', '#2f5a5c', '#7a2a24'];
    const lit = [true, false, true, true, false, true];
    let room = 12;
    for (let i = 0; i < 6; i++) {
      const x = -8.6 + i * 3.2;
      const num = room++;
      const doorTex = canvasTex(256, 512, (c) => {
        c.fillStyle = doorColors[i];
        c.fillRect(0, 0, 256, 512);
        c.strokeStyle = 'rgba(0,0,0,0.35)';
        c.lineWidth = 6;
        c.strokeRect(28, 40, 200, 180);
        c.strokeRect(28, 260, 200, 210);
        for (let k = 0; k < 200; k++) {
          c.fillStyle = `rgba(230,220,200,${r() * 0.12})`;
          c.fillRect(r() * 256, r() * 512, 2 + r() * 10, 1 + r() * 3);
        }
        c.fillStyle = '#c8a24a';
        c.font = 'bold 54px Georgia, serif';
        c.textAlign = 'center';
        c.fillText(String(num), 128, 120);
        c.beginPath();
        c.arc(210, 300, 12, 0, Math.PI * 2);
        c.fill();
      });
      const door = new THREE.Mesh(new THREE.PlaneGeometry(0.95, 2.1),
        new THREE.MeshStandardMaterial({ map: doorTex, roughness: 0.7, envMap: env, envMapIntensity: 0.4 }));
      door.position.set(x, 1.05 + 0.16, Z - 0.005);
      door.rotation.y = Math.PI;
      g.add(door);
      const winTex = canvasTex(256, 192, (c) => {
        const gr = c.createLinearGradient(0, 0, 256, 0);
        gr.addColorStop(0, '#d9a45e');
        gr.addColorStop(0.5, '#f2c887');
        gr.addColorStop(1, '#c78a45');
        c.fillStyle = gr;
        c.fillRect(0, 0, 256, 192);
        c.fillStyle = 'rgba(90,50,20,0.35)';
        for (let k = 0; k < 10; k++) c.fillRect(k * 26, 0, 10, 192);
        c.fillStyle = '#2a2622';
        c.fillRect(0, 0, 256, 8);
        c.fillRect(0, 184, 256, 8);
        c.fillRect(124, 0, 8, 192);
      });
      const wm = new THREE.MeshStandardMaterial({
        color: 0x111111, map: winTex, emissive: 0xffffff, emissiveMap: winTex,
        emissiveIntensity: lit[i] ? 0.9 : 0.0, roughness: 0.2, envMap: env,
      });
      wm.userData.base = lit[i] ? 0.9 : 0.0;
      this.windowMats.push(wm);
      const win = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 1.1), wm);
      win.position.set(x + 1.45, 1.45, Z - 0.005);
      win.rotation.y = Math.PI;
      g.add(win);
      // window AC unit
      const ac = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.38, 0.45),
        new THREE.MeshStandardMaterial({ color: 0x8d8c86, roughness: 0.6, metalness: 0.5, envMap: env }));
      ac.position.set(x + 1.45, 0.62, Z - 0.23);
      g.add(ac);
      // porch lamp
      const lamp = new THREE.Mesh(new THREE.SphereGeometry(0.07, 12, 8),
        new THREE.MeshStandardMaterial({ color: 0x222222, emissive: 0xffc27a, emissiveIntensity: lit[i] ? 3 : 0.2 }));
      lamp.position.set(x + 0.75, 2.35, Z - 0.1);
      g.add(lamp);
    }
    // one room with the TV on: cold flicker
    this.tvMat = this.windowMats[3];

    // ice machine glowing at the end of the walkway
    const ice = new THREE.Mesh(new THREE.BoxGeometry(0.9, 1.6, 0.7), [
      new THREE.MeshStandardMaterial({ color: 0x6e7c86, roughness: 0.5, metalness: 0.6, envMap: env }),
      new THREE.MeshStandardMaterial({ color: 0x6e7c86, roughness: 0.5, metalness: 0.6, envMap: env }),
      new THREE.MeshStandardMaterial({ color: 0x6e7c86, roughness: 0.5, metalness: 0.6, envMap: env }),
      new THREE.MeshStandardMaterial({ color: 0x6e7c86, roughness: 0.5, metalness: 0.6, envMap: env }),
      new THREE.MeshStandardMaterial({ color: 0x6e7c86, roughness: 0.5, metalness: 0.6, envMap: env }),
      new THREE.MeshStandardMaterial({ color: 0x0a1a24, emissive: 0x7ec8ff, emissiveIntensity: 0.9, roughness: 0.3,
        map: canvasTex(128, 256, (c) => {
          c.fillStyle = '#123';
          c.fillRect(0, 0, 128, 256);
          c.fillStyle = '#9fe0ff';
          c.font = 'bold 34px Arial';
          c.textAlign = 'center';
          c.fillText('ICE', 64, 70);
        }) }),
    ]);
    ice.position.set(7.2, 0.96, Z - 0.5);
    g.add(ice);

    // --- the VACANCY sign on a pole
    const sign = new THREE.Group();
    sign.position.set(-1.3, 2.55, Z - 2.45);
    sign.scale.setScalar(0.8);
    const board = new THREE.Mesh(new THREE.BoxGeometry(3.3, 1.35, 0.12),
      new THREE.MeshStandardMaterial({ color: 0x14100e, roughness: 0.6, metalness: 0.4, envMap: env }));
    board.position.set(0, 0.1, 0.06);
    sign.add(board);
    const frame = new THREE.Mesh(new THREE.BoxGeometry(3.4, 1.45, 0.08),
      new THREE.MeshStandardMaterial({ color: 0x6a5a48, roughness: 0.4, metalness: 0.9, envMap: env }));
    frame.position.set(0, 0.1, 0.1);
    sign.add(frame);
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.07, 2.2, 10), postMat);
    pole.position.set(0, -1.62, 0.12);
    sign.add(pole);
    // painted MOTEL above
    const motelWord = canvasTex(512, 128, (c) => {
      c.fillStyle = '#14100e';
      c.fillRect(0, 0, 512, 128);
      c.fillStyle = '#d8c7a0';
      c.font = 'bold 92px Georgia, serif';
      c.textAlign = 'center';
      c.textBaseline = 'middle';
      c.fillText('MOTEL', 256, 70);
    });
    const motelPlate = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 0.5),
      new THREE.MeshStandardMaterial({ map: motelWord, roughness: 0.7, envMap: env, envMapIntensity: 0.3 }));
    motelPlate.position.set(0, 0.5, -0.005);
    motelPlate.rotation.y = Math.PI;
    sign.add(motelPlate);

    this.neonMat = new THREE.MeshStandardMaterial({ color: 0x220000, emissive: 0xff1c10, emissiveIntensity: 0, roughness: 0.3 });
    this.neonFlickerMat = this.neonMat.clone();
    this.noMat = new THREE.MeshStandardMaterial({ color: 0x1a0505, emissive: 0xff1c10, emissiveIntensity: 0.0, roughness: 0.4 });
    const word = neonWord('VACANCY', 0.38, 0.06, this.neonMat, 0.026);
    // the last two letters are on a flaky transformer
    word.children.forEach((m) => {
      if (m.userData.letter === 'C' || m.userData.letter === 'Y') {
        const idx = word.children.indexOf(m);
        if (idx >= word.children.length - 3) (m as THREE.Mesh).material = this.neonFlickerMat;
      }
    });
    // text faces the car (-Z); rotating it half a turn makes it read left to right from there
    const no = neonWord('NO', 0.3, 0.05, this.noMat, 0.02);
    const gap = 0.14;
    const total = word.userData.width + gap + no.userData.width;
    const left = total / 2; // viewer's left is +X
    no.rotation.y = Math.PI;
    no.position.set(left, -0.3, -0.02);
    word.rotation.y = Math.PI;
    word.position.set(left - no.userData.width - gap, -0.36, -0.02);
    sign.add(word, no);
    g.add(sign);

    this.neonLight = new THREE.RectAreaLight(0xff2418, 0, 2.6, 0.5);
    this.neonLight.position.set(-1.3, 2.3, Z - 2.6);
    this.neonLight.lookAt(-1.0, 0.7, 0);
    g.add(this.neonLight);
    this.neonFill = new THREE.PointLight(0xff2a1a, 0, 9, 1.8);
    this.neonFill.position.set(-1.3, 2.25, Z - 2.8);
    g.add(this.neonFill);
    this.windowLight = new THREE.PointLight(0xffb36b, 0, 7, 2);
    this.windowLight.position.set(1.5, 1.6, Z - 1.4);
    g.add(this.windowLight);

    g.visible = false;
  }

  setOn(on: boolean) {
    this.on = on;
    if (on) this.group.visible = true;
  }

  get isOn() { return this.on; }

  update(dt: number, t: number) {
    this.fade += ((this.on ? 1 : 0) - this.fade) * Math.min(1, dt * 3);
    if (!this.on && this.fade < 0.01) {
      this.group.visible = false;
      this.neonLight.intensity = 0;
      this.neonFill.intensity = 0;
      this.windowLight.intensity = 0;
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
    this.neonMat.emissiveIntensity = 4.2 * lv;
    // the last letters drop out on their own sometimes
    const flaky = Math.sin(t * 13.7) > 0.93 || (this.burst > 0 && Math.random() < 0.5) ? 0.05 : 1;
    this.neonFlickerMat.emissiveIntensity = 4.2 * lv * (this.reduced ? 1 : flaky);
    this.noMat.emissiveIntensity = 0.04 * this.fade;
    this.neonLight.intensity = 9 * lv;
    this.neonFill.intensity = 14 * lv;
    this.windowLight.intensity = 5 * this.fade;
    for (const m of this.windowMats) m.emissiveIntensity = m.userData.base * this.fade;
    // TV glow in room 15
    const tv = 0.5 + 0.35 * Math.sin(t * 7.1) * Math.sin(t * 2.3) + (Math.random() < 0.05 ? 0.3 : 0);
    this.tvMat.emissive.setRGB(0.55 + 0.2 * tv, 0.7 + 0.2 * tv, 1.0);
    this.tvMat.emissiveIntensity = (0.4 + tv * 0.5) * this.fade;
  }
}
