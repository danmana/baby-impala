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

export class Atmosphere {
  readonly group = new THREE.Group();
  readonly beams: Beam[] = [];
  private uniforms = { ...beamUniforms(), uTime: { value: 0 }, uRain: { value: 0 }, uFog: { value: 1 } };
  private cones: { mesh: THREE.Mesh; beam: Beam }[] = [];
  private rain: THREE.LineSegments;
  private rainTarget = 0;
  private dust: THREE.Points;

  constructor(quality: { particles: number; volumetrics: boolean }) {
    this.group.name = 'atmosphere';
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
        uniform float uTime; uniform float uFog;
        varying vec3 vW;
        ${NOISE}
        ${BEAM_GLSL}
        void main() {
          vec2 p = vW.xz * 0.28;
          float n = fbm(p + vec2(uTime * 0.018, uTime * 0.007));
          n = smoothstep(0.32, 0.85, n + 0.15 * fbm(p * 3.0 - uTime * 0.03));
          float r = length(vW.xz);
          float edge = smoothstep(9.5, 3.0, r);
          vec3 lit = beamLight(vW);
          float a = n * edge * uFog * (0.035 + 0.16 * min(length(lit), 1.2));
          vec3 col = vec3(0.045, 0.05, 0.062) + lit * 0.35;
          gl_FragColor = vec4(col, a);
        }`,
    });
    for (const [y, s] of [[0.05, 1], [0.16, 1.25]] as [number, number][]) {
      const plane = new THREE.Mesh(new THREE.PlaneGeometry(22, 22, 1, 1), fogMat);
      plane.rotation.x = -Math.PI / 2;
      plane.position.y = y;
      plane.scale.setScalar(s);
      plane.renderOrder = 5;
      plane.frustumCulled = false;
      this.group.add(plane);
    }

    // ---------------------------------------------------------------- dust in the beams
    const count = Math.round(2600 * quality.particles);
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
        uniform float uTime;
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
          vLit = beamLight(p);
          vA = 0.5 + 0.5 * sin(uTime * (1.0 + seed * 2.0) + seed * 12.0);
          vec4 mv = viewMatrix * vec4(p, 1.0);
          gl_PointSize = min(5.0, (0.8 + seed * 1.4) * (26.0 / -mv.z));
          gl_Position = projectionMatrix * mv;
        }`,
      fragmentShader: /* glsl */ `
        varying vec3 vLit;
        varying float vA;
        void main() {
          vec2 c = gl_PointCoord - 0.5;
          float d = smoothstep(0.5, 0.1, length(c));
          vec3 col = vLit * 0.55;
          gl_FragColor = vec4(col * d * (0.35 + 0.65 * vA), 1.0);
        }`,
    });
    this.dust = new THREE.Points(dg, dustMat);
    this.dust.frustumCulled = false;
    this.group.add(this.dust);

    // ---------------------------------------------------------------- rain
    const drops = Math.round(3200 * quality.particles);
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
        uniform float uRain;
        varying vec3 vLit; varying float vT;
        void main() {
          vec3 col = vec3(0.05, 0.055, 0.065) + vLit * 0.8;
          gl_FragColor = vec4(col * uRain * (0.4 + 0.6 * vT), 1.0);
        }`,
    });
    this.rain = new THREE.LineSegments(rg, rainMat);
    this.rain.frustumCulled = false;
    this.rain.visible = false;
    this.group.add(this.rain);
  }

  /** Add a volumetric cone for a beam. `parent` carries the beam's orientation (+X forward). */
  addBeam(beam: Beam, parent: THREE.Object3D | null, length: number, radius: number, enabled: boolean) {
    this.beams.push(beam);
    if (!enabled) return;
    const geo = new THREE.CylinderGeometry(0.04, radius, length, 40, 1, true); // narrow end at the lamp
    geo.translate(0, -length / 2, 0);
    geo.rotateZ(Math.PI / 2); // tip at the origin, opening along +X
    const mat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      uniforms: { ...this.uniforms, uI: { value: 0 }, uC: { value: beam.color }, uLen: { value: length } },
      vertexShader: /* glsl */ `
        varying vec3 vW; varying vec3 vN; varying float vAx;
        uniform float uLen;
        void main() {
          vec4 w = modelMatrix * vec4(position, 1.0);
          vW = w.xyz;
          vN = normalize(mat3(modelMatrix) * normal);
          vAx = position.x / uLen;
          gl_Position = projectionMatrix * viewMatrix * w;
        }`,
      fragmentShader: /* glsl */ `
        uniform float uTime; uniform float uI; uniform vec3 uC; uniform float uFog;
        varying vec3 vW; varying vec3 vN; varying float vAx;
        ${NOISE}
        void main() {
          vec3 V = normalize(cameraPosition - vW);
          float facing = abs(dot(normalize(vN), V));
          float core = pow(facing, 1.6);
          float along = pow(1.0 - clamp(vAx, 0.0, 1.0), 1.8) * smoothstep(0.0, 0.06, vAx);
          float n = 0.6 + 0.4 * fbm(vW.xz * 1.3 + vec2(uTime * 0.05, -uTime * 0.03) + vW.y);
          float a = core * along * n * uI * (0.5 + 0.5 * uFog);
          gl_FragColor = vec4(uC * a * 0.045, 1.0);
        }`,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.raycast = () => undefined; // light, not matter
    mesh.renderOrder = 6;
    mesh.frustumCulled = false;
    if (parent) parent.add(mesh);
    else this.group.add(mesh);
    this.cones.push({ mesh, beam });
  }

  setRain(on: boolean) {
    this.rainTarget = on ? 1 : 0;
    if (on) this.rain.visible = true;
  }

  get rainLevel() { return this.uniforms.uRain.value; }

  update(dt: number, t: number) {
    const U = this.uniforms;
    U.uTime.value = t;
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
    for (const c of this.cones) {
      (c.mesh.material as THREE.ShaderMaterial).uniforms.uI.value = c.beam.intensity;
      c.mesh.visible = c.beam.intensity > 0.01;
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
