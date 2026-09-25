import * as THREE from 'three';
import { NOISE } from './glsl';

/** A light beam the atmosphere reacts to (headlights and spotlights). */
export interface Beam {
  origin: THREE.Vector3;
  dir: THREE.Vector3;
  cos: number;      // cosine of the half angle
  range: number;
  intensity: number;
  color: THREE.Color;
}

const MAX_BEAMS = 4;

function beamUniforms() {
  return {
    uBeamO: { value: Array.from({ length: MAX_BEAMS }, () => new THREE.Vector3()) },
    uBeamD: { value: Array.from({ length: MAX_BEAMS }, () => new THREE.Vector3(1, 0, 0)) },
    uBeamP: { value: Array.from({ length: MAX_BEAMS }, () => new THREE.Vector4(0.9, 10, 0, 0)) },
    uBeamC: { value: Array.from({ length: MAX_BEAMS }, () => new THREE.Color()) },
  };
}

const BEAM_GLSL = /* glsl */ `
  uniform vec3 uBeamO[${MAX_BEAMS}];
  uniform vec3 uBeamD[${MAX_BEAMS}];
  uniform vec4 uBeamP[${MAX_BEAMS}]; // cos, range, intensity, -
  uniform vec3 uBeamC[${MAX_BEAMS}];
  vec3 beamLight(vec3 p) {
    vec3 acc = vec3(0.0);
    for (int i = 0; i < ${MAX_BEAMS}; i++) {
      if (uBeamP[i].z <= 0.0) continue;
      vec3 v = p - uBeamO[i];
      float d = length(v);
      float c = dot(v / max(d, 1e-4), uBeamD[i]);
      float cone = smoothstep(uBeamP[i].x, mix(uBeamP[i].x, 1.0, 0.55), c);
      float fall = 1.0 / (1.0 + d * d * 0.08) * smoothstep(uBeamP[i].y, uBeamP[i].y * 0.4, d);
      acc += uBeamC[i] * cone * fall * uBeamP[i].z;
    }
    return acc;
  }
`;

/**
 * Single-scattering light shaft. The cone's back faces are drawn; for each
 * pixel the view ray is intersected with the cone analytically, clipped by the
 * ground and the beam's reach, and marched to accumulate in-scattered light
 * (noisy haze density, soft edge, distance falloff, forward-scattering phase).
 */
const SHAFT_VERT = /* glsl */ `
  varying vec3 vW;
  void main() {
    vec4 w = modelMatrix * vec4(position, 1.0);
    vW = w.xyz;
    gl_Position = projectionMatrix * viewMatrix * w;
  }`;

const shaftFrag = (steps: number) => /* glsl */ `
  uniform vec3 uO; uniform vec3 uD; uniform float uCos; uniform float uLen;
  uniform float uI; uniform vec3 uC; uniform float uHaze; uniform float uTime; uniform float uG;
  varying vec3 vW;
  ${NOISE}
  float hg(float c, float g) {
    float g2 = g * g;
    return (1.0 - g2) / pow(1.0 + g2 - 2.0 * g * c, 1.5);
  }
  void main() {
    vec3 ro = cameraPosition;
    vec3 rd = normalize(vW - ro);
    float tMax = length(vW - ro);
    // stop at the ground
    if (rd.y < -1e-4) tMax = min(tMax, -ro.y / rd.y);
    float c2 = uCos * uCos;
    vec3 co = ro - uO;
    float dv = dot(rd, uD), cv = dot(co, uD);
    float a = dv * dv - c2;
    float b = 2.0 * (dv * cv - c2 * dot(rd, co));
    float cc = cv * cv - c2 * dot(co, co);
    float tIn = 0.0;
    bool inside = cv > 0.0 && cc >= 0.0;
    if (!inside) {
      float disc = b * b - 4.0 * a * cc;
      if (disc < 0.0) discard;
      float sq = sqrt(disc);
      float r0 = (-b - sq) / (2.0 * a), r1 = (-b + sq) / (2.0 * a);
      float lo = min(r0, r1), hi = max(r0, r1);
      // first crossing on the forward nappe
      tIn = hi;
      if (lo > 0.0 && dot(ro + rd * lo - uO, uD) > 0.0) tIn = lo;
    }
    if (tIn >= tMax) discard;
    float dt = (tMax - tIn) / float(${steps});
    float jitter = hash12(gl_FragCoord.xy + fract(uTime) * 61.0);
    float acc = 0.0;
    for (int i = 0; i < ${steps}; i++) {
      float t = tIn + dt * (float(i) + jitter);
      vec3 p = ro + rd * t;
      vec3 v = p - uO;
      float h = dot(v, uD);
      if (h <= 0.0 || h > uLen) continue;
      float d = length(v);
      float ca = h / max(d, 1e-4);
      float edge = smoothstep(uCos, mix(uCos, 1.0, 0.7), ca);
      float fall = 1.0 / (1.0 + h * h * 0.06) * smoothstep(uLen, uLen * 0.45, h) * smoothstep(0.0, 0.25, h);
      float n = fbm3(p * vec3(1.4, 2.2, 1.4) + vec3(uTime * 0.07, uTime * 0.02, -uTime * 0.05));
      float dens = 0.35 + 1.15 * n * n;
      acc += edge * fall * dens;
    }
    float phase = mix(1.0, hg(dot(uD, -rd), uG), 0.85);
    vec3 col = uC * acc * dt * uI * uHaze * phase * 0.05;
    gl_FragColor = vec4(col, 1.0);
  }`;

export class Atmosphere {
  readonly group = new THREE.Group();
  readonly beams: Beam[] = [];
  private uniforms = {
    ...beamUniforms(),
    uTime: { value: 0 }, uRain: { value: 0 }, uFog: { value: 1 },
    uFogCol: { value: new THREE.Color(0x0a0b0e) },
  };
  private shafts: { mesh: THREE.Mesh; beam: Beam; mat: THREE.ShaderMaterial; parent: THREE.Object3D | null }[] = [];
  private rain: THREE.LineSegments;
  private rainTarget = 0;
  private dust: THREE.Points;
  private steps: number;
  private dustCount: number;
  private dropCount: number;
  /** light shafts are drawn only when the quality level allows them */
  private volumetrics = true;

  constructor(quality: { particles: number; volumetrics: boolean; tier?: string }) {
    this.group.name = 'atmosphere';
    this.steps = quality.tier === 'high' ? 16 : 10;
    const U = this.uniforms;

    // ---------------------------------------------------------------- ground fog
    const fogMat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      uniforms: U,
      vertexShader: /* glsl */ `
        varying vec3 vW;
        void main() {
          vec4 w = modelMatrix * vec4(position, 1.0);
          vW = w.xyz;
          gl_Position = projectionMatrix * viewMatrix * w;
        }`,
      fragmentShader: /* glsl */ `
        uniform float uTime; uniform float uFog; uniform vec3 uFogCol;
        varying vec3 vW;
        ${NOISE}
        ${BEAM_GLSL}
        void main() {
          vec2 p = vW.xz * 0.28;
          float n = fbm(p + vec2(uTime * 0.018, uTime * 0.007));
          n = smoothstep(0.32, 0.85, n + 0.15 * fbm(p * 3.0 - uTime * 0.03));
          float r = length(vW.xz);
          float edge = smoothstep(11.0, 3.0, r);
          vec3 lit = beamLight(vW);
          float a = n * edge * uFog * (0.05 + 0.16 * min(length(lit), 1.2));
          vec3 col = uFogCol * 1.6 + lit * 0.35;
          gl_FragColor = vec4(col, a);
        }`,
    });
    for (const [y, s] of [[0.05, 1], [0.16, 1.25]] as [number, number][]) {
      const plane = new THREE.Mesh(new THREE.PlaneGeometry(26, 26, 1, 1), fogMat);
      plane.rotation.x = -Math.PI / 2;
      plane.position.y = y;
      plane.scale.setScalar(s);
      plane.renderOrder = 5;
      plane.frustumCulled = false;
      plane.raycast = () => undefined;
      this.group.add(plane);
    }

    // ---------------------------------------------------------------- dust in the beams
    // built at full density; the quality level only changes how many are drawn
    const count = (this.dustCount = 2600);
    const pos = new Float32Array(count * 3);
    const seed = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = -3 + Math.random() * 16;
      pos[i * 3 + 1] = Math.random() * 2.6;
      pos[i * 3 + 2] = -5 + Math.random() * 10;
      seed[i] = Math.random();
    }
    const dg = new THREE.BufferGeometry();
    dg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    dg.setAttribute('seed', new THREE.BufferAttribute(seed, 1));
    const dustMat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: U,
      vertexShader: /* glsl */ `
        uniform float uTime; uniform float uFog;
        attribute float seed;
        varying vec3 vLit;
        varying float vA;
        ${BEAM_GLSL}
        void main() {
          vec3 p = position;
          p.x += sin(uTime * 0.13 + seed * 40.0) * 0.4 + uTime * 0.05;
          p.y += sin(uTime * 0.21 + seed * 23.0) * 0.25;
          p.z += cos(uTime * 0.17 + seed * 31.0) * 0.4;
          p.x = mod(p.x + 3.0, 16.0) - 3.0;
          vLit = beamLight(p) * uFog;
          vec4 mv = viewMatrix * vec4(p, 1.0);
          // motes right in front of the lens read as fireflies: fade them out
          vA = (0.5 + 0.5 * sin(uTime * (1.0 + seed * 2.0) + seed * 12.0)) * smoothstep(1.2, 3.0, -mv.z);
          gl_PointSize = min(3.5, (0.7 + seed * 1.1) * (22.0 / -mv.z));
          gl_Position = projectionMatrix * mv;
        }`,
      fragmentShader: /* glsl */ `
        varying vec3 vLit;
        varying float vA;
        void main() {
          vec2 c = gl_PointCoord - 0.5;
          float d = smoothstep(0.5, 0.1, length(c));
          vec3 col = vLit * 0.4;
          gl_FragColor = vec4(col * d * (0.35 + 0.65 * vA), 1.0);
        }`,
    });
    this.dust = new THREE.Points(dg, dustMat);
    this.dust.frustumCulled = false;
    this.dust.raycast = () => undefined;
    this.group.add(this.dust);

    // ---------------------------------------------------------------- rain
    const drops = (this.dropCount = 3200);
    const rp = new Float32Array(drops * 2 * 3);
    const rs = new Float32Array(drops * 2);
    const rend = new Float32Array(drops * 2);
    for (let i = 0; i < drops; i++) {
      const a = Math.random() * Math.PI * 2;
      const r = Math.sqrt(Math.random()) * 9;
      const x = Math.cos(a) * r, z = Math.sin(a) * r, y = Math.random() * 7;
      for (let k = 0; k < 2; k++) {
        rp.set([x, y, z], (i * 2 + k) * 3);
        rs[i * 2 + k] = Math.random();
        rend[i * 2 + k] = k;
      }
    }
    const rg = new THREE.BufferGeometry();
    rg.setAttribute('position', new THREE.BufferAttribute(rp, 3));
    rg.setAttribute('seed', new THREE.BufferAttribute(rs, 1));
    rg.setAttribute('tail', new THREE.BufferAttribute(rend, 1));
    const rainMat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: U,
      vertexShader: /* glsl */ `
        uniform float uTime; uniform float uRain;
        attribute float seed; attribute float tail;
        varying vec3 vLit; varying float vT;
        ${BEAM_GLSL}
        void main() {
          vec3 p = position;
          float speed = 7.5 + seed * 2.5;
          p.y = mod(p.y - uTime * speed, 7.0);
          p.x += p.y * 0.08;
          p.y += tail * (0.18 + seed * 0.12);
          p.x += tail * 0.015;
          vLit = beamLight(p);
          vT = tail;
          gl_Position = projectionMatrix * viewMatrix * vec4(p, 1.0);
        }`,
      fragmentShader: /* glsl */ `
        uniform float uRain; uniform vec3 uFogCol;
        varying vec3 vLit; varying float vT;
        void main() {
          vec3 col = uFogCol * 2.2 + vec3(0.03) + vLit * 0.8;
          gl_FragColor = vec4(col * uRain * (0.4 + 0.6 * vT), 1.0);
        }`,
    });
    this.rain = new THREE.LineSegments(rg, rainMat);
    this.rain.frustumCulled = false;
    this.rain.visible = false;
    this.rain.raycast = () => undefined;
    this.group.add(this.rain);
    this.setQuality(quality);
  }

  /** Switch light shafts and particle density for a quality level, at any time. */
  setQuality(q: { particles: number; volumetrics: boolean }) {
    this.volumetrics = q.volumetrics;
    this.dust.geometry.setDrawRange(0, Math.round(this.dustCount * q.particles));
    // rain streaks are line segments: two vertices each
    this.rain.geometry.setDrawRange(0, 2 * Math.round(this.dropCount * q.particles));
  }

  /**
   * Add a light shaft for a beam. `parent` carries the beam's orientation
   * (+X forward); without one the shaft follows beam.origin/dir each frame.
   */
  addBeam(beam: Beam, parent: THREE.Object3D | null, length: number, g = 0.45) {
    this.beams.push(beam);
    const half = Math.acos(beam.cos);
    const radius = Math.tan(half) * length * 1.08;
    const geo = new THREE.CylinderGeometry(0.02, radius, length, 48, 1, true);
    geo.translate(0, -length / 2, 0);
    geo.rotateZ(Math.PI / 2); // apex at the origin, opening along +X
    const mat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      depthTest: true,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      uniforms: {
        uO: { value: new THREE.Vector3() }, uD: { value: new THREE.Vector3(1, 0, 0) },
        uCos: { value: beam.cos }, uLen: { value: length }, uI: { value: 0 }, uC: { value: beam.color },
        uHaze: { value: 1 }, uTime: this.uniforms.uTime, uG: { value: g },
      },
      vertexShader: SHAFT_VERT,
      fragmentShader: shaftFrag(this.steps),
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.renderOrder = 6;
    mesh.frustumCulled = false;
    mesh.raycast = () => undefined;
    if (parent) parent.add(mesh);
    else this.group.add(mesh);
    this.shafts.push({ mesh, beam, mat, parent });
  }

  setRain(on: boolean) {
    this.rainTarget = on ? 1 : 0;
    if (on) this.rain.visible = true;
  }

  get rainLevel() { return this.uniforms.uRain.value; }

  /** all meshes that should not show up in the puddle reflection */
  get reflectionHidden(): THREE.Object3D[] {
    return [this.group, ...this.shafts.map((s) => s.mesh)];
  }

  update(dt: number, t: number, haze: number, fogColor: THREE.Color) {
    const U = this.uniforms;
    U.uTime.value = t;
    U.uFog.value = haze;
    U.uFogCol.value.copy(fogColor);
    U.uRain.value += (this.rainTarget - U.uRain.value) * Math.min(1, dt * 1.5);
    if (U.uRain.value < 0.01 && this.rainTarget === 0) this.rain.visible = false;
    for (let i = 0; i < MAX_BEAMS; i++) {
      const b = this.beams[i];
      if (!b) {
        U.uBeamP.value[i].z = 0;
        continue;
      }
      U.uBeamO.value[i].copy(b.origin);
      U.uBeamD.value[i].copy(b.dir);
      U.uBeamP.value[i].set(b.cos, b.range, b.intensity, 0);
      U.uBeamC.value[i].copy(b.color);
    }
    for (const s of this.shafts) {
      const on = this.volumetrics && s.beam.intensity > 0.01 && haze > 0.02;
      s.mesh.visible = on;
      if (!on) continue;
      // the beam's world origin/dir are authoritative (the parent only positions the proxy mesh)
      s.mat.uniforms.uO.value.copy(s.beam.origin);
      s.mat.uniforms.uD.value.copy(s.beam.dir);
      s.mat.uniforms.uI.value = s.beam.intensity;
      s.mat.uniforms.uHaze.value = haze * (1 + U.uRain.value * 0.8);
    }
  }
}

/** Rain-bead droplets on the glass: procedural, in world space, denser in the rain. */
export function addDroplets(mat: THREE.MeshPhysicalMaterial, rain: { value: number }, time: { value: number }) {
  mat.onBeforeCompile = (s) => {
    s.uniforms.uRain = rain;
    s.uniforms.uTime = time;
    s.vertexShader = s.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vDropW;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvDropW = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    s.fragmentShader = s.fragmentShader
      .replace('#include <common>', `#include <common>
        varying vec3 vDropW; uniform float uRain; uniform float uTime;
        ${NOISE}
        // returns xy = normal tilt, z = coverage
        vec3 drops(vec2 p, float density, float slide) {
          vec3 acc = vec3(0.0);
          for (int layer = 0; layer < 2; layer++) {
            float sc = layer == 0 ? 55.0 : 110.0;
            vec2 q = p * sc;
            q.y += slide * float(layer + 1) * 0.6 * floor(hash12(floor(q)) * 3.0);
            vec2 c = floor(q);
            vec2 f = fract(q) - 0.5;
            float h = hash12(c + float(layer) * 17.0);
            if (h < 1.0 - density) continue;
            vec2 o = (hash22(c) - 0.5) * 0.5;
            float r = 0.12 + 0.22 * hash12(c * 3.1);
            vec2 d = f - o;
            float l = length(d);
            if (l < r) {
              float k = l / r;
              acc.xy += d / r * (1.0 - k * k) * 1.4;
              acc.z = max(acc.z, smoothstep(1.0, 0.6, k));
            }
          }
          return acc;
        }`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
        vec2 dp = vec2(vDropW.z, vDropW.y + vDropW.x * 0.6);
        float slide = uRain * uTime * 0.25;
        vec3 dr = drops(dp, 0.12 + 0.45 * uRain, slide);
        dr *= 0.45 + 0.55 * uRain;
        normal = normalize(normal + (viewMatrix * vec4(dr.x, dr.y, 0.0, 0.0)).xyz * 0.45);`)
      .replace('#include <opaque_fragment>', `
        diffuseColor.a = max(diffuseColor.a, dr.z * 0.35);
        outgoingLight += vec3(0.012) * dr.z;
        #include <opaque_fragment>`);
  };
  mat.customProgramCacheKey = () => 'glass-drops';
  mat.needsUpdate = true;
}
