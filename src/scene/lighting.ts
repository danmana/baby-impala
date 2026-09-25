import * as THREE from 'three';

export type PresetName = 'moon' | 'sunset' | 'day';

export interface Preset {
  label: string;
  hdri: string;
  /** multiplier on the HDRI radiance baked into the environment map */
  envIntensity: number;
  /** HDRI rotation about Y so its sun/moon lines up with our directional light */
  envRotation: number;
  /** brightest value any HDRI texel may reach, so the sun disk doesn't double the key light */
  envClamp: number;
  /** HDRI saturation (0 = grey) and colour tint, to grade the reflections to the mood */
  envSat: number;
  envTint: number;
  /** brightness of the soft sky band added behind the car (0 = none) */
  skyBand: number;
  sun: { azimuth: number; elevation: number; color: number; intensity: number };
  hemi: { sky: number; ground: number; intensity: number };
  exposure: number;
  /** backdrop at the horizon: the tone the ground fades into */
  background: number;
  /** backdrop overhead, and the glow low in the sky towards the sun or moon */
  sky: { top: number; glow: number; glowStrength: number };
  fog: { color: number; density: number };
  /** how visible light shafts, dust and ground fog are */
  haze: number;
  bloom: number;
  /** car lamps glare (dimmer in daylight) */
  lamps: number;
}

const deg = THREE.MathUtils.degToRad;

export const PRESETS: Record<PresetName, Preset> = {
  moon: {
    label: 'Moon',
    hdri: 'hdri/moon.hdr',
    envIntensity: 1.4,
    envRotation: deg(0),
    envClamp: 6,
    envSat: 0.3,
    envTint: 0xc4d0ff,
    skyBand: 0.6,
    sun: { azimuth: deg(-36), elevation: deg(40), color: 0xb9c8ff, intensity: 1.35 },
    hemi: { sky: 0x3a4866, ground: 0x0b0b0d, intensity: 0.35 },
    exposure: 1.15,
    background: 0x0a0e15,
    sky: { top: 0x020306, glow: 0x3a4a70, glowStrength: 0.35 },
    fog: { color: 0x07090d, density: 0.035 },
    haze: 1,
    bloom: 0.5,
    lamps: 1,
  },
  sunset: {
    label: 'Sunset',
    hdri: 'hdri/sunset.hdr',
    envIntensity: 1.1,
    envRotation: deg(24),
    envClamp: 14,
    envSat: 0.9,
    envTint: 0xffffff,
    skyBand: 0,
    sun: { azimuth: deg(-60), elevation: deg(10), color: 0xffa25e, intensity: 3.2 },
    hemi: { sky: 0x8a6a78, ground: 0x2a1a14, intensity: 0.45 },
    exposure: 0.95,
    background: 0x4a3027,
    sky: { top: 0x15121a, glow: 0xff8a4a, glowStrength: 1.1 },
    fog: { color: 0x3a2a24, density: 0.028 },
    haze: 0.55,
    bloom: 0.42,
    lamps: 0.75,
  },
  day: {
    label: 'Day',
    hdri: 'hdri/day.hdr',
    envIntensity: 0.9,
    envRotation: deg(9),
    envClamp: 10,
    envSat: 0.85,
    envTint: 0xffffff,
    skyBand: 0,
    sun: { azimuth: deg(-45), elevation: deg(35), color: 0xfff4e6, intensity: 3.4 },
    hemi: { sky: 0xbfd2ea, ground: 0x4a4540, intensity: 0.6 },
    exposure: 0.8,
    background: 0xaeb4ba,
    sky: { top: 0x7a8698, glow: 0xfff2dc, glowStrength: 0.25 },
    fog: { color: 0xa6abb0, density: 0.022 },
    haze: 0.12,
    bloom: 0.25,
    lamps: 0.45,
  },
};

/** Neon and motel windows added to the environment when the motel is shown. */
export interface EnvExtras {
  motel: boolean;
}

/**
 * Prefiltered environment built from an HDRI sphere (plus the motel's neon
 * and lit windows when it is on), so paint and chrome reflect the right world
 * without the HDRI ever being drawn as a background.
 */
export function buildEnv(renderer: THREE.WebGLRenderer, hdr: THREE.Texture, preset: Preset, extras: EnvExtras) {
  const scene = new THREE.Scene();
  const sphereMat = new THREE.ShaderMaterial({
    uniforms: {
      map: { value: hdr }, uGain: { value: preset.envIntensity }, uClamp: { value: preset.envClamp },
      uSat: { value: preset.envSat }, uTint: { value: new THREE.Color(preset.envTint) },
    },
    vertexShader: `varying vec2 vUv;
      void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform sampler2D map; uniform float uGain; uniform float uClamp; uniform float uSat; uniform vec3 uTint;
      varying vec2 vUv;
      void main() {
        vec3 c = texture2D(map, vUv).rgb * uGain;
        c = mix(vec3(dot(c, vec3(0.2126, 0.7152, 0.0722))), c, uSat) * uTint;
        c *= min(1.0, uClamp / max(max(c.r, c.g), max(c.b, 1e-4)));
        gl_FragColor = vec4(c, 1.0);
      }`,
    side: THREE.BackSide, depthWrite: false, toneMapped: false,
  });
  const sphere = new THREE.Mesh(new THREE.SphereGeometry(50, 64, 32), sphereMat);
  sphere.rotation.y = preset.envRotation;
  scene.add(sphere);
  const add = (w: number, hgt: number, color: THREE.ColorRepresentation, intensity: number, pos: [number, number, number], look: [number, number, number]) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, hgt),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(intensity), side: THREE.DoubleSide, toneMapped: false }));
    m.position.set(...pos);
    m.lookAt(...look);
    scene.add(m);
  };
  // a soft band of sky glow low behind the car: broad highlights along the
  // roofline and fenders instead of pinpoint glints from a rim light
  if (preset.skyBand > 0) {
    const band = new THREE.Mesh(new THREE.PlaneGeometry(40, 9),
      new THREE.ShaderMaterial({
        uniforms: { uCol: { value: new THREE.Color(preset.envTint).multiplyScalar(preset.skyBand) } },
        vertexShader: `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
        fragmentShader: `uniform vec3 uCol; varying vec2 vUv;
          void main() {
            float h = smoothstep(0.0, 0.35, vUv.y) * (1.0 - smoothstep(0.55, 1.0, vUv.y));
            float w = smoothstep(0.0, 0.3, vUv.x) * (1.0 - smoothstep(0.7, 1.0, vUv.x));
            gl_FragColor = vec4(uCol * h * w, 1.0);
          }`,
        side: THREE.DoubleSide, blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, transparent: true,
      }));
    band.position.set(-6, 5, 18);
    band.lookAt(0, 1, 0);
    scene.add(band);
    const band2 = band.clone();
    band2.position.set(6, 6, -18);
    band2.lookAt(0, 1, 0);
    band2.scale.setScalar(0.8);
    scene.add(band2);
  }
  if (extras.motel) {
    // the motel stands behind the car on +Z (three.js axes)
    const night = preset.haze;
    add(22, 4, 0x2a211c, 0.5 + 0.5 * (1 - night), [-1, 1.8, 5.2], [0, 1.8, 0]);
    for (let i = 0; i < 6; i++) add(1.5, 1.1, 0xffb36b, 1.8 * night, [-7.2 + i * 3.2, 1.45, 4.9], [-7.2 + i * 3.2, 1.45, 0]);
    add(2.6, 0.55, 0xff2a18, 9 * night + 1.5, [-1.3, 2.35, 1.95], [-1.3, 1.2, -6]);
  }
  const pmrem = new THREE.PMREMGenerator(renderer);
  const rt = pmrem.fromScene(scene, 0, 0.1, 120);
  pmrem.dispose();
  scene.traverse((o) => {
    const m = o as THREE.Mesh;
    if (m.isMesh) {
      m.geometry.dispose();
      (m.material as THREE.Material).dispose();
    }
  });
  return rt.texture;
}

const tmpA = new THREE.Color();
const tmpB = new THREE.Color();

/**
 * Sun (or moon), sky fill and the per-preset look. Switching presets blends
 * the lights, exposure, fog and backdrop over about a second; the prebuilt
 * environment maps swap halfway through.
 */
export class LightingRig {
  readonly group = new THREE.Group();
  readonly sun: THREE.DirectionalLight;
  readonly hemi: THREE.HemisphereLight;
  /** sky dome at infinity: a gradient, no clouds or HDRI, so the car stays the subject */
  readonly backdrop: THREE.Mesh;
  private sky = {
    uTop: { value: new THREE.Color() }, uHorizon: { value: new THREE.Color() },
    uGlow: { value: new THREE.Color() }, uSun: { value: new THREE.Vector3(1, 0, 0) },
  };
  current: PresetName = 'moon';
  private from: Preset = PRESETS.moon;
  private to: Preset = PRESETS.moon;
  private t = 1;
  private envSwapped = true;
  /** extra light for the exploded "workshop" view, 0..1 */
  workshop = 0;
  /** soft fill while the camera is in the cabin, 0..1 (sky light only: no highlights) */
  cabin = 0;
  cabinTarget = 0;
  /** current blended values the rest of the scene reads */
  readonly live = {
    haze: 1, bloom: 0.5, lamps: 1, exposure: 1,
    fogColor: new THREE.Color(), background: new THREE.Color(),
  };
  onEnvSwap: ((name: PresetName) => void) | null = null;

  constructor(private scene: THREE.Scene, private renderer: THREE.WebGLRenderer, shadows: boolean, shadowSize: number) {
    this.sun = new THREE.DirectionalLight(0xffffff, 1);
    this.sun.castShadow = shadows;
    const s = this.sun.shadow;
    s.mapSize.set(shadowSize, shadowSize);
    s.camera.left = -4.2;
    s.camera.right = 4.2;
    s.camera.top = 4.2;
    s.camera.bottom = -4.2;
    s.camera.near = 1;
    s.camera.far = 30;
    s.bias = -0.0003;
    s.normalBias = 0.025;
    s.radius = 3;
    this.sun.target.position.set(0, 0.4, 0);
    this.hemi = new THREE.HemisphereLight(0xffffff, 0x000000, 0.3);
    this.backdrop = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 24), new THREE.ShaderMaterial({
      uniforms: this.sky,
      vertexShader: `varying vec3 vDir;
        void main() {
          vDir = position;
          vec4 p = projectionMatrix * vec4(mat3(viewMatrix) * position, 1.0);
          gl_Position = p.xyww;
        }`,
      fragmentShader: `uniform vec3 uTop; uniform vec3 uHorizon; uniform vec3 uGlow; uniform vec3 uSun; varying vec3 vDir;
        void main() {
          vec3 d = normalize(vDir);
          float e = d.y;
          vec3 c = mix(uHorizon, uTop, smoothstep(0.0, 0.6, e));
          float toward = max(dot(normalize(d.xz + 1e-5), normalize(uSun.xz + 1e-5)), 0.0);
          c += uGlow * pow(toward, 5.0) * smoothstep(-0.02, 0.06, e) * (1.0 - smoothstep(0.05, 0.45, e));
          c += (fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453) - 0.5) / 255.0;
          gl_FragColor = vec4(c, 1.0);
        }`,
      side: THREE.BackSide, depthWrite: false,
    }));
    this.backdrop.frustumCulled = false;
    this.backdrop.renderOrder = -10;
    this.backdrop.name = 'sky';
    this.group.add(this.sun, this.sun.target, this.hemi, this.backdrop);
    this.apply(PRESETS.moon, PRESETS.moon, 1);
  }

  set(name: PresetName, instant = false) {
    if (name === this.current && this.t >= 1) return;
    this.from = this.snapshot();
    this.to = PRESETS[name];
    this.current = name;
    this.t = instant ? 1 : 0;
    this.envSwapped = instant;
    if (instant) this.onEnvSwap?.(name);
  }

  /** true while a preset change is blending (the sun is moving) */
  get blending() {
    return this.t < 1;
  }

  /** re-apply the current preset after its values were edited (dev tuning) */
  retarget() {
    this.from = this.to = PRESETS[this.current];
    this.t = 1;
  }

  /** the blended state right now, as a preset (for smooth re-targeting) */
  private snapshot(): Preset {
    const k = this.ease(this.t);
    return blend(this.from, this.to, k);
  }

  private ease(t: number) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  update(dt: number) {
    this.cabin += (this.cabinTarget - this.cabin) * Math.min(1, dt * 2.5);
    if (this.t < 1) {
      this.t = Math.min(1, this.t + dt / 1.1);
      if (!this.envSwapped && this.t >= 0.5) {
        this.envSwapped = true;
        this.onEnvSwap?.(this.current);
      }
    }
    this.apply(this.from, this.to, this.ease(this.t));
  }

  private apply(a: Preset, b: Preset, k: number) {
    const p = blend(a, b, k);
    const dir = new THREE.Vector3(
      Math.cos(p.sun.elevation) * Math.cos(p.sun.azimuth),
      Math.sin(p.sun.elevation),
      Math.cos(p.sun.elevation) * Math.sin(p.sun.azimuth),
    );
    this.sun.position.copy(dir.multiplyScalar(14)).add(this.sun.target.position);
    this.sun.color.set(p.sun.color);
    this.sun.intensity = p.sun.intensity * (1 + this.workshop * 0.35);
    // in the cabin the fill turns warm and neutral, so the tan dash reads as tan
    this.hemi.color.set(p.hemi.sky).lerp(tmpA.set(0xc9bba2), this.cabin * 0.7);
    this.hemi.groundColor.set(p.hemi.ground).lerp(tmpA.set(0x3a3128), this.cabin * 0.7);
    this.hemi.intensity = p.hemi.intensity + this.workshop * 0.9 + this.cabin * 1.4;
    this.renderer.toneMappingExposure = p.exposure;
    this.live.haze = p.haze;
    this.live.bloom = p.bloom;
    this.live.lamps = p.lamps;
    this.live.exposure = p.exposure;
    this.live.fogColor.set(p.fog.color);
    this.live.background.set(p.background);
    const fog = this.scene.fog as THREE.FogExp2 | null;
    if (fog) {
      fog.color.copy(this.live.fogColor);
      fog.density = p.fog.density;
    }
    if (this.scene.background instanceof THREE.Color) this.scene.background.copy(this.live.background);
    this.sky.uHorizon.value.copy(this.live.background);
    this.sky.uTop.value.set(p.sky.top);
    this.sky.uGlow.value.set(p.sky.glow).multiplyScalar(p.sky.glowStrength);
    this.sky.uSun.value.copy(dir);
  }
}

function lerpColor(a: number, b: number, k: number) {
  return tmpA.set(a).lerp(tmpB.set(b), k).getHex();
}

function lerpAngle(a: number, b: number, k: number) {
  let d = b - a;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  return a + d * k;
}

function blend(a: Preset, b: Preset, k: number): Preset {
  const n = (x: number, y: number) => x + (y - x) * k;
  return {
    label: k < 0.5 ? a.label : b.label,
    hdri: k < 0.5 ? a.hdri : b.hdri,
    envIntensity: n(a.envIntensity, b.envIntensity),
    envRotation: n(a.envRotation, b.envRotation),
    envClamp: n(a.envClamp, b.envClamp),
    envSat: n(a.envSat, b.envSat),
    envTint: lerpColor(a.envTint, b.envTint, k),
    skyBand: n(a.skyBand, b.skyBand),
    sun: {
      azimuth: lerpAngle(a.sun.azimuth, b.sun.azimuth, k),
      elevation: n(a.sun.elevation, b.sun.elevation),
      color: lerpColor(a.sun.color, b.sun.color, k),
      intensity: n(a.sun.intensity, b.sun.intensity),
    },
    hemi: { sky: lerpColor(a.hemi.sky, b.hemi.sky, k), ground: lerpColor(a.hemi.ground, b.hemi.ground, k), intensity: n(a.hemi.intensity, b.hemi.intensity) },
    exposure: n(a.exposure, b.exposure),
    background: lerpColor(a.background, b.background, k),
    sky: { top: lerpColor(a.sky.top, b.sky.top, k), glow: lerpColor(a.sky.glow, b.sky.glow, k), glowStrength: n(a.sky.glowStrength, b.sky.glowStrength) },
    fog: { color: lerpColor(a.fog.color, b.fog.color, k), density: n(a.fog.density, b.fog.density) },
    haze: n(a.haze, b.haze),
    bloom: n(a.bloom, b.bloom),
    lamps: n(a.lamps, b.lamps),
  };
}
