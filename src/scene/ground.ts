import * as THREE from 'three';
import { NOISE } from './glsl';
import { PlanarReflection } from './reflection';

export const GROUND_RADIUS = 9;

/**
 * A round patch of wet asphalt with puddles. The puddles mirror the car
 * through a planar reflection; the whole patch is damp (blurred reflection);
 * rain adds ripples. The edges fade to black.
 */
export class Ground {
  readonly mesh: THREE.Mesh;
  readonly uniforms = {
    tRefl: { value: null as THREE.Texture | null },
    uReflMatrix: { value: new THREE.Matrix4() },
    uTime: { value: 0 },
    uRain: { value: 0 },
    uReflOn: { value: 1 },
    uRadius: { value: GROUND_RADIUS },
    uNeon: { value: 0 },
    uGrid: { value: 0 },
  };

  constructor(private reflection: PlanarReflection | null) {
    const geo = new THREE.CircleGeometry(GROUND_RADIUS, 96);
    geo.rotateX(-Math.PI / 2);
    const mat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.6, metalness: 0.0, envMapIntensity: 0.35 });
    const U = this.uniforms;
    mat.onBeforeCompile = (shader) => {
      Object.assign(shader.uniforms, U);
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', `#include <common>
          uniform mat4 uReflMatrix; varying vec4 vReflCoord; varying vec3 vGPos;`)
        .replace('#include <begin_vertex>', `#include <begin_vertex>
          vec4 gw = modelMatrix * vec4(transformed, 1.0);
          vGPos = gw.xyz; vReflCoord = uReflMatrix * gw;`);
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', `#include <common>
          uniform sampler2D tRefl; uniform float uTime; uniform float uRain; uniform float uReflOn;
          uniform float uRadius; uniform float uNeon; uniform float uGrid;
          varying vec4 vReflCoord; varying vec3 vGPos;
          ${NOISE}
          float puddleField(vec2 p) {
            float n = fbm(p * 0.42 + vec2(3.1, 7.7));
            n += 0.10 * fbm(p * 1.9);
            // art-directed pools where the hero camera looks across the ground
            n += 0.22 * exp(-dot(p - vec2(3.6, -2.2), p - vec2(3.6, -2.2)) * 0.35);
            n += 0.18 * exp(-dot(p - vec2(-1.2, -2.6), p - vec2(-1.2, -2.6)) * 0.4);
            n += 0.16 * exp(-dot(p - vec2(-3.9, 1.6), p - vec2(-3.9, 1.6)) * 0.5);
            n += 0.14 * exp(-dot(p - vec2(4.2, 1.9), p - vec2(4.2, 1.9)) * 0.5);
            return n;
          }
          vec2 rippleNormal(vec2 p, float t) {
            vec2 acc = vec2(0.0);
            float sc = 0.32;
            vec2 q = p / sc;
            vec2 cell = floor(q);
            vec2 f = fract(q);
            for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
              vec2 o = vec2(float(i), float(j));
              vec2 c = cell + o;
              float h = hash12(c * 1.37);
              float ph = fract(t * (0.9 + 0.6 * h) + h * 7.0);
              vec2 ctr = o + hash22(c);
              vec2 d = f - ctr;
              float r = length(d);
              float rad = ph * 0.9;
              float x = r - rad;
              float w = exp(-x * x * 180.0) * (1.0 - ph) * (1.0 - ph);
              acc += (d / max(r, 1e-3)) * sin(x * 60.0) * w;
            }
            return acc;
          }
          float carShadow(vec2 p) {
            vec2 b = vec2(2.55, 0.86);
            vec2 d2 = abs(p) - b;
            float d = length(max(d2, 0.0)) + min(max(d2.x, d2.y), 0.0) - 0.14;
            float s = smoothstep(-0.35, 0.75, d);
            float w = 1.0;
            vec2 wh[4];
            wh[0] = vec2(1.8175, 0.794); wh[1] = vec2(1.8175, -0.794);
            wh[2] = vec2(-1.2055, 0.794); wh[3] = vec2(-1.2055, -0.794);
            for (int i = 0; i < 4; i++) {
              vec2 e = (p - wh[i]) / vec2(0.34, 0.16);
              w *= mix(0.25, 1.0, smoothstep(0.0, 1.4, length(e)));
            }
            return mix(0.18, 1.0, s) * w;
          }`)
        .replace('#include <color_fragment>', `#include <color_fragment>
          vec2 gp = vGPos.xz;
          float pf = puddleField(gp);
          float puddle = smoothstep(0.585, 0.64, pf);
          float damp = smoothstep(0.45, 0.6, pf);
          float grain = hash12(floor(gp * 180.0));
          float agg = vnoise(gp * 55.0);
          float patchy = fbm(gp * 0.8);
          vec3 asphalt = vec3(0.045, 0.045, 0.047) * (0.6 + 0.5 * patchy) * (0.8 + 0.35 * agg);
          asphalt += vec3(0.05) * step(0.985, grain);  // light aggregate stones
          asphalt *= mix(0.62, 0.42, damp);            // water darkens the surface
          diffuseColor.rgb = mix(asphalt, vec3(0.012), puddle);
          float gShadow = carShadow(gp);`)
        .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
          roughnessFactor = mix(mix(0.52, 0.30, damp) + 0.18 * agg, 0.035, puddle);`)
        .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
          {
            vec2 gN = vec2(vnoise(gp * 90.0) - 0.5, vnoise(gp * 90.0 + 13.0) - 0.5) * 0.28 * (1.0 - puddle);
            vec2 rN = uRain > 0.001 ? rippleNormal(gp, uTime) * 0.55 * uRain * (0.35 + 0.65 * puddle) : vec2(0.0);
            vec3 wn = normalize(vec3(gN.x + rN.x, 1.0, gN.y + rN.y));
            normal = normalize((viewMatrix * vec4(wn, 0.0)).xyz);
          }`)
        .replace('#include <aomap_fragment>', `#include <aomap_fragment>
          // lamps have no size here: keep point-light glints in the puddles small
          reflectedLight.directSpecular *= mix(0.7, 0.1, puddle);`)
        .replace('#include <opaque_fragment>', `
          {
            vec3 wn = normalize((inverse(viewMatrix) * vec4(normal, 0.0)).xyz);
            vec2 distort = (wn.xz) * 0.12;
            vec2 ruv = vReflCoord.xy / vReflCoord.w + distort;
            float lod = mix(4.5, 0.0, puddle);
            vec3 refl = uReflOn > 0.5 ? textureLod(tRefl, ruv, lod).rgb : vec3(0.0);
            vec3 V = normalize(cameraPosition - vGPos);
            float fres = 0.04 + 0.96 * pow(1.0 - clamp(V.y, 0.0, 1.0), 5.0);
            float k = mix(0.30 * damp + 0.08, 0.92, puddle) * mix(0.35, 1.0, fres);
            outgoingLight = outgoingLight * mix(1.0, 0.35, puddle) + refl * k;
            float r = length(vGPos.xz);
            float fade = smoothstep(uRadius, uRadius * 0.38, r);
            outgoingLight *= fade * fade * gShadow;
            // workshop-manual grid for the exploded view
            if (uGrid > 0.001) {
              vec2 g = abs(fract(vGPos.xz * 2.0 + 0.5) - 0.5) / fwidth(vGPos.xz * 2.0);
              float line = 1.0 - min(min(g.x, g.y), 1.0);
              vec2 g2 = abs(fract(vGPos.xz * 0.5 + 0.5) - 0.5) / fwidth(vGPos.xz * 0.5);
              float major = 1.0 - min(min(g2.x, g2.y), 1.0);
              outgoingLight += vec3(0.62, 0.58, 0.5) * (line * 0.05 + major * 0.1) * uGrid * fade;
            }
          }
          #include <opaque_fragment>`);
    };
    mat.customProgramCacheKey = () => 'wet-asphalt';
    this.mesh = new THREE.Mesh(geo, mat);
    this.mesh.receiveShadow = true;
    this.mesh.name = 'ground';
  }

  update(renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.PerspectiveCamera, hide: THREE.Object3D[], t: number) {
    this.uniforms.uTime.value = t;
    if (this.reflection && this.reflection.scale > 0) {
      this.reflection.render(renderer, scene, camera, [this.mesh, ...hide]);
      this.uniforms.tRefl.value = this.reflection.target.texture;
      this.uniforms.uReflMatrix.value.copy(this.reflection.textureMatrix);
      this.uniforms.uReflOn.value = 1;
    } else {
      this.uniforms.uReflOn.value = 0;
    }
  }
}
