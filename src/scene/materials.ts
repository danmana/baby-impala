import * as THREE from 'three';

/**
 * Materials for everything in the GLB. The base model's textured materials
 * (UpCar_M1 paint, Chrome_M, FrontChromes_M, Window_M, Indoor_M, wheel_M)
 * are upgraded in place (clear coat, glass, glowing lamps); the parts we
 * built in Blender get physically based materials by name.
 */
export class Materials {
  readonly m = new Map<string, THREE.Material>();
  /** named emissive controls: intensity setters for lamps, dash, etc. */
  readonly lamps = new Map<string, THREE.MeshStandardMaterial[]>();
  env: THREE.Texture | null;

  constructor(env: THREE.Texture | null) {
    this.env = env;
    const std = (p: THREE.MeshStandardMaterialParameters) => new THREE.MeshStandardMaterial({ envMap: env, ...p });
    const phy = (p: THREE.MeshPhysicalMaterialParameters) => new THREE.MeshPhysicalMaterial({ envMap: env, ...p });
    const add = (k: string, mat: THREE.Material) => this.m.set(k, mat);

    add('chrome', std({ color: 0xf2f0ec, metalness: 1.0, roughness: 0.1, envMapIntensity: 1.3 }));
    add('mirror', std({ color: 0xffffff, metalness: 1.0, roughness: 0.01, envMapIntensity: 1.3 }));
    add('steel', std({ color: 0x9a9a9a, metalness: 1.0, roughness: 0.32 }));
    add('steel_dark', std({ color: 0x3a3a3c, metalness: 1.0, roughness: 0.45 }));
    add('gunmetal', std({ color: 0x1c1c1f, metalness: 0.85, roughness: 0.38 }));
    add('silver', std({ color: 0xdcdce0, metalness: 1.0, roughness: 0.16 }));
    add('nickel', std({ color: 0xbdb6a8, metalness: 1.0, roughness: 0.25 }));
    add('iron', std({ color: 0x3a3632, metalness: 0.9, roughness: 0.62 }));
    add('brass', std({ color: 0xb58a3c, metalness: 1.0, roughness: 0.34 }));
    add('bowtie', std({ color: 0xd2b060, metalness: 1.0, roughness: 0.25 }));
    add('drum', std({ color: 0x1c1b1a, metalness: 0.7, roughness: 0.6 }));
    add('exhaust', std({ color: 0x2c2825, metalness: 0.8, roughness: 0.5 }));
    add('wood', std({ color: 0x5b3a1f, roughness: 0.72 }));
    add('wood_dark', std({ color: 0x2e1a0d, roughness: 0.6 }));
    add('wood_trim', std({ color: 0x4d2f17, roughness: 0.55 }));
    add('leather', std({ color: 0x4a2c1a, roughness: 0.62 }));
    add('leather_dark', std({ color: 0x21150c, roughness: 0.6 }));
    add('antler', std({ color: 0xb7a58a, roughness: 0.6 }));
    add('ivory', std({ color: 0xe0d6c0, roughness: 0.38 }));
    add('felt', std({ color: 0x0a0a0a, roughness: 1.0, envMapIntensity: 0.05 }));
    add('felt_red', std({ color: 0x4e0a0e, roughness: 1.0, envMapIntensity: 0.05 }));
    add('carpet', std({ color: 0x0c0c0c, roughness: 1.0, envMapIntensity: 0.1 }));
    add('carpet_gray', std({ color: 0x3c3b39, roughness: 1.0, envMapIntensity: 0.15 }));
    add('strap', std({ color: 0x0b0b0b, roughness: 0.8 }));
    add('twine', std({ color: 0x9a8360, roughness: 0.9 }));
    add('sage', std({ color: 0x78806c, roughness: 0.95 }));
    add('feather', std({ color: 0xd6d0c4, roughness: 0.8, side: THREE.DoubleSide }));
    add('bottle_glass', phy({ color: 0x9fb4b8, roughness: 0.05, transmission: 0, transparent: true, opacity: 0.55, envMapIntensity: 1.2 }));
    add('blood_glass', phy({ color: 0x3a0404, roughness: 0.1, transparent: true, opacity: 0.9 }));
    add('oil_glass', phy({ color: 0x8a6412, roughness: 0.1, transparent: true, opacity: 0.8 }));
    add('salt_blue', std({ color: 0x1d3f8c, roughness: 0.5 }));
    add('ammo_green', std({ color: 0x353f22, roughness: 0.6, metalness: 0.3 }));
    add('cardboard', std({ color: 0x73553a, roughness: 0.9 }));
    add('shell_red', std({ color: 0x8c1510, roughness: 0.45 }));
    add('paper', std({ color: 0xd9d1bb, roughness: 0.9 }));
    add('plastic_black', std({ color: 0x0b0b0b, roughness: 0.5 }));
    add('red_plastic', std({ color: 0x9a120a, roughness: 0.5 }));
    add('zippo_blue', std({ color: 0x1e3a78, roughness: 0.5, metalness: 0.3 }));
    add('tape', std({ color: 0x8b8b8b, roughness: 0.6, metalness: 0.2 }));
    add('burlap', std({ color: 0x7d6645, roughness: 1.0 }));
    add('canvas_olive', std({ color: 0x4f5030, roughness: 0.9 }));
    add('bead_blue', std({ color: 0x1b3aa0, roughness: 0.3, metalness: 0.2 }));
    add('led_red', std({ color: 0x400404, emissive: 0xff2010, emissiveIntensity: 0.6 }));
    add('led_green', std({ color: 0x053005, emissive: 0x30ff40, emissiveIntensity: 0.6 }));
    add('engine', std({ color: 0xa3420f, roughness: 0.5, metalness: 0.1 }));
    add('engine_dark', std({ color: 0x151515, roughness: 0.6, metalness: 0.4 }));
    add('underbody', std({ color: 0x060606, roughness: 0.95, envMapIntensity: 0.15 }));
    add('radiator', std({ color: 0x0d0d0d, roughness: 0.5, metalness: 0.6 }));
    add('wire_red', std({ color: 0x7a0e08, roughness: 0.5 }));
    add('spot_lens', phy({ color: 0xc9c7bd, roughness: 0.06, clearcoat: 1, emissive: 0xfff2dc, emissiveIntensity: 0, metalness: 0.3 }));
    add('black', std({ color: 0x030303, roughness: 0.55 }));
    add('rubber', std({ color: 0x080808, roughness: 0.7 }));
    add('plastic_olive', std({ color: 0x7b7650, roughness: 0.55 }));
    add('dial', std({ color: 0x111111, roughness: 0.35, emissive: 0xffffff, emissiveIntensity: 0 }));
    add('lens_clear', std({ color: 0xdedbd4, roughness: 0.1, metalness: 0.2 }));
    add('lego_red', std({ color: 0xb01010, roughness: 0.32 }));
    add('lego_blue', std({ color: 0x1040b0, roughness: 0.32 }));
    add('lego_yellow', std({ color: 0xe0b010, roughness: 0.32 }));
    add('army_green', std({ color: 0x3f5a2a, roughness: 0.5 }));
    add('trap_paint', std({ color: 0x9a968e, roughness: 0.6, envMapIntensity: 0.5, side: THREE.DoubleSide }));
    add('paint', phy({ color: 0x040406, roughness: 0.3, clearcoat: 1.0, clearcoatRoughness: 0.05 }));
    add('tire', std({ color: 0x111111, roughness: 0.86 }));
  }

  get(name: string): THREE.Material | undefined {
    const key = name.replace(/\.\d+$/, '');
    return this.m.get(key);
  }

  registerLamp(key: string, mat: THREE.MeshStandardMaterial) {
    const arr = this.lamps.get(key) ?? [];
    arr.push(mat);
    this.lamps.set(key, arr);
  }

  setLamp(key: string, v: number) {
    for (const m of this.lamps.get(key) ?? []) m.emissiveIntensity = v;
    const own = this.m.get(key) as THREE.MeshStandardMaterial | undefined;
    if (own && 'emissiveIntensity' in own && !this.lamps.has(key)) own.emissiveIntensity = v;
  }

  setEnv(env: THREE.Texture) {
    this.env = env;
    const seen = new Set<THREE.Material>();
    const apply = (mat: THREE.Material) => {
      if (seen.has(mat)) return;
      seen.add(mat);
      const s = mat as THREE.MeshStandardMaterial;
      if ('envMap' in s) {
        s.envMap = env;
        s.needsUpdate = true;
      }
    };
    this.m.forEach(apply);
    this.extra.forEach(apply);
  }

  /** materials created while upgrading the GLB (so env swaps reach them too) */
  readonly extra: THREE.Material[] = [];

  /** Upgrade the base model's textured material to our look. */
  upgrade(src: THREE.MeshStandardMaterial, meshName: string): THREE.Material {
    const env = this.env;
    const name = src.name;
    const keep = (m: THREE.MeshStandardMaterial) => {
      m.envMap = env;
      this.extra.push(m);
      return m;
    };
    if (name.startsWith('UpCar')) {
      const cached = this.m.get('__paint');
      if (cached) return cached;
      const p = new THREE.MeshPhysicalMaterial({
        map: src.map, normalMap: src.normalMap, normalScale: new THREE.Vector2(1, 1).multiply(src.normalScale),
        roughnessMap: src.roughnessMap, metalnessMap: src.metalnessMap, aoMap: src.aoMap, aoMapIntensity: 1,
        color: new THREE.Color(0x9a9aa0), roughness: 0.85, metalness: 0.0,
        clearcoat: 1.0, clearcoatRoughness: 0.075, envMap: env, envMapIntensity: 1.1, specularIntensity: 0.5,
        side: THREE.DoubleSide,
      });
      p.name = 'paint_textured';
      this.m.set('__paint', p);
      this.extra.push(p);
      return p;
    }
    if (name.startsWith('Window')) {
      const isLamp = meshName.startsWith('GlassLapm');
      const g = new THREE.MeshPhysicalMaterial({
        map: src.map, color: isLamp ? 0xe8e6de : 0x8c9296, roughness: 0.03, metalness: 0.0,
        transparent: true, opacity: isLamp ? 0.55 : 0.28, envMap: env, envMapIntensity: 1.5,
        side: THREE.DoubleSide, depthWrite: false, specularIntensity: 1.0,
        emissive: isLamp ? 0xfff0d0 : 0x000000, emissiveIntensity: 0,
      });
      g.name = isLamp ? 'headlamp_glass' : 'glass';
      if (isLamp) this.registerLamp('headlamp', g);
      else this.m.set('__glass', g);
      this.extra.push(g);
      return g;
    }
    if (name.startsWith('FrontChromes')) {
      // lamps share this atlas: clone per lamp group so each can glow
      const lamp = lampGroup(meshName);
      if (!lamp) {
        const c = this.m.get('__frontchromes');
        if (c) return c;
        src.envMapIntensity = 1.2;
        this.m.set('__frontchromes', keep(src));
        return src;
      }
      const cached = this.m.get(`__fc_${lamp}`);
      if (cached) return cached;
      const c = src.clone();
      c.emissive = new THREE.Color(1, 1, 1);
      c.emissiveMap = src.map;
      c.emissiveIntensity = 0;
      c.envMapIntensity = 1.2;
      if (lamp === 'tail') maskRed(c);
      if (lamp === 'signal') maskAmber(c);
      this.registerLamp(lamp === 'tail' ? 'tail' : lamp === 'signal' ? 'signal' : 'headlamp_bulb', c);
      this.m.set(`__fc_${lamp}`, c);
      return keep(c);
    }
    if (name.startsWith('Chrome')) {
      src.envMapIntensity = 1.35;
      return keep(src);
    }
    if (name.startsWith('Indoor')) {
      if (meshName.startsWith('BviewMirror') || meshName.startsWith('MirrorHandle')) {
        const c = this.m.get('__mirror_in') ?? keep(Object.assign(src.clone(), { envMapIntensity: 0.18 }));
        this.m.set('__mirror_in', c);
        return c;
      }
      src.envMapIntensity = 0.5;
      return keep(src);
    }
    if (name.startsWith('wheel')) {
      src.envMapIntensity = 0.5;
      return keep(src);
    }
    return keep(src);
  }
}

function lampGroup(mesh: string): string | null {
  if (mesh.startsWith('BackLapmFrame') || mesh.startsWith('BackLapmPartition')) return 'tail';
  if (mesh.startsWith('ColorLamp') || mesh.startsWith('SideLamp')) return 'signal';
  if (mesh.startsWith('LampBulb') || mesh.startsWith('LampMirror')) return 'bulb';
  return null;
}

/** Only the red parts of the taillight atlas glow. */
function maskRed(m: THREE.MeshStandardMaterial) {
  m.onBeforeCompile = (s) => {
    s.fragmentShader = s.fragmentShader.replace(
      '#include <emissivemap_fragment>',
      `#ifdef USE_EMISSIVEMAP
        vec4 emTex = texture2D( emissiveMap, vEmissiveMapUv );
        float redness = smoothstep(0.06, 0.25, emTex.r - max(emTex.g, emTex.b));
        totalEmissiveRadiance *= vec3(1.0, 0.12, 0.08) * redness * 2.5;
      #endif`,
    );
  };
  m.customProgramCacheKey = () => 'mask-red';
}

function maskAmber(m: THREE.MeshStandardMaterial) {
  m.onBeforeCompile = (s) => {
    s.fragmentShader = s.fragmentShader.replace(
      '#include <emissivemap_fragment>',
      `#ifdef USE_EMISSIVEMAP
        vec4 emTex = texture2D( emissiveMap, vEmissiveMapUv );
        float warm = smoothstep(0.05, 0.2, emTex.r - emTex.b);
        totalEmissiveRadiance *= vec3(1.0, 0.45, 0.08) * warm * 2.0;
      #endif`,
    );
  };
  m.customProgramCacheKey = () => 'mask-amber';
}
