import * as THREE from 'three';
import { NOISE } from './glsl';
import { PlanarReflection } from './reflection';

export const GROUND_RADIUS = 12;
const TILE = 2.6; // metres per asphalt texture tile

export interface GroundMaps {
  diff: THREE.Texture;
  nor: THREE.Texture;
  arm: THREE.Texture; // R = ambient occlusion, G = roughness
}

/**
 * A round patch of scanned wet asphalt. Puddles mirror the car through a
 * planar reflection; the damp asphalt around them is darker and slicker with a
 * blurred reflection; rain adds ripples; the patch fades into the backdrop.
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
    uGrid: { value: 0 },
    uBg: { value: new THREE.Color(0x06080c) },
    tPuddle: { value: null as THREE.Texture | null },
  };
  private puddleTarget: THREE.WebGLRenderTarget | null = null;
  private frames = 0;

  constructor(private reflection: PlanarReflection | null, maps: GroundMaps, anisotropy: number) {
    const geo = new THREE.CircleGeometry(GROUND_RADIUS, 128);
    geo.rotateX(-Math.PI / 2);
    const rep = (GROUND_RADIUS * 2) / TILE;
    for (const t of [maps.diff, maps.nor, maps.arm]) {
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.repeat.set(rep, rep);
      t.anisotropy = anisotropy;
      t.needsUpdate = true;
    }
    maps.diff.colorSpace = THREE.SRGBColorSpace;
    const mat = new THREE.MeshStandardMaterial({
      map: maps.diff, normalMap: maps.nor, normalScale: new THREE.Vector2(1.1, 1.1),
      roughnessMap: maps.arm, aoMap: maps.arm, aoMapIntensity: 0.8,
      color: 0xb8b6b2, roughness: 1, metalness: 0, envMapIntensity: 0.55,
    });
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
          uniform float uRadius; uniform float uGrid; uniform vec3 uBg; uniform sampler2D tPuddle;
          varying vec4 vReflCoord; varying vec3 vGPos;
          ${NOISE}
          vec2 rippleNormal(vec2 p, float t) {
            vec2 acc = vec2(0.0);
            vec2 q = p / 0.32;
            vec2 cell = floor(q);
            vec2 f = fract(q);
            for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
              vec2 o = vec2(float(i), float(j));
              vec2 c = cell + o;
              float h = hash12(c * 1.37);
              float ph = fract(t * (0.9 + 0.6 * h) + h * 7.0);
              vec2 d = f - (o + hash22(c));
              float r = length(d);
              float x = r - ph * 0.9;
              float w = exp(-x * x * 180.0) * (1.0 - ph) * (1.0 - ph);
              acc += (d / max(r, 1e-3)) * sin(x * 60.0) * w;
            }
            return acc;
          }
          float carShadow(vec2 p) {
            vec2 d2 = abs(p) - vec2(2.5, 0.84);
            float d = length(max(d2, 0.0)) + min(max(d2.x, d2.y), 0.0) - 0.14;
            float s = smoothstep(-0.3, 0.6, d);
            float w = 1.0;
            vec2 wh[4];
            wh[0] = vec2(1.772, 0.843); wh[1] = vec2(1.772, -0.843);
            wh[2] = vec2(-1.252, 0.843); wh[3] = vec2(-1.252, -0.843);
            for (int i = 0; i < 4; i++) {
              vec2 e = (p - wh[i]) / vec2(0.3, 0.14);
              w *= mix(0.45, 1.0, smoothstep(0.0, 1.3, length(e)));
            }
            return mix(0.45, 1.0, s) * w;
          }`)
        .replace('#include <map_fragment>', `#include <map_fragment>
          vec2 gp = vGPos.xz;
          float pf = texture2D(tPuddle, gp / (2.0 * uRadius) + 0.5).r;
          float puddle = smoothstep(0.64, 0.685, pf);
          float damp = smoothstep(0.50, 0.64, pf);
          // water darkens asphalt; puddles are nearly black with a hint of the grey below
          diffuseColor.rgb *= mix(1.0, 0.55, damp);
          diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * 0.18, puddle);`)
        .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
          roughnessFactor = mix(roughnessFactor * mix(1.0, 0.55, damp), 0.03, puddle);`)
        .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
          {
            vec3 flatN = normalize((viewMatrix * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
            normal = normalize(mix(normal, flatN, puddle * 0.92 + damp * 0.25));
            if (uRain > 0.001) {
              vec2 rN = rippleNormal(gp, uTime) * 0.55 * uRain * (0.35 + 0.65 * puddle);
              normal = normalize(normal + (viewMatrix * vec4(rN.x, 0.0, rN.y, 0.0)).xyz);
            }
          }`)
        .replace('#include <opaque_fragment>', `
          {
            vec3 wn = normalize((inverse(viewMatrix) * vec4(normal, 0.0)).xyz);
            vec2 ruv = vReflCoord.xy / vReflCoord.w + wn.xz * 0.1;
            float lod = mix(4.0, 0.0, puddle);
            vec3 refl = uReflOn > 0.5 ? textureLod(tRefl, ruv, lod).rgb : vec3(0.0);
            vec3 V = normalize(cameraPosition - vGPos);
            float fres = 0.02 + 0.98 * pow(1.0 - clamp(V.y, 0.0, 1.0), 5.0);
            float k = mix(0.16 * damp, 0.9, puddle) * mix(0.3, 1.0, fres);
            outgoingLight = outgoingLight * mix(1.0, 0.4, puddle) + refl * k;
            outgoingLight *= carShadow(gp);
            if (uGrid > 0.001) {
              vec2 g = abs(fract(vGPos.xz * 2.0 + 0.5) - 0.5) / fwidth(vGPos.xz * 2.0);
              float line = 1.0 - min(min(g.x, g.y), 1.0);
              vec2 g2 = abs(fract(vGPos.xz * 0.5 + 0.5) - 0.5) / fwidth(vGPos.xz * 0.5);
              float major = 1.0 - min(min(g2.x, g2.y), 1.0);
              outgoingLight += vec3(0.62, 0.58, 0.5) * (line * 0.05 + major * 0.1) * uGrid;
            }
            float r = length(vGPos.xz);
            float fade = smoothstep(uRadius, uRadius * 0.42, r);
            outgoingLight = mix(uBg, outgoingLight, fade * fade);
          }
          #include <opaque_fragment>`);
    };
    mat.customProgramCacheKey = () => 'wet-asphalt-v3';
    // the ground never occludes anything above it; skipping its depth lets light
    // shafts clip against it analytically instead
    mat.depthWrite = false;
    this.mesh = new THREE.Mesh(geo, mat);
    this.mesh.renderOrder = -1;
    this.mesh.receiveShadow = true;
    this.mesh.name = 'ground';
  }

  /**
   * The puddle layout never changes, so its noise is rendered once into a
   * texture instead of being evaluated for every ground pixel every frame.
   */
  bakePuddles(renderer: THREE.WebGLRenderer) {
    if (this.puddleTarget) return;
    const rt = new THREE.WebGLRenderTarget(1024, 1024, { type: THREE.HalfFloatType, depthBuffer: false });
    const mat = new THREE.ShaderMaterial({
      uniforms: { uRadius: { value: GROUND_RADIUS } },
      vertexShader: `varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
      fragmentShader: `uniform float uRadius; varying vec2 vUv;
        ${NOISE}
        void main() {
          vec2 p = (vUv * 2.0 - 1.0) * uRadius;
          float n = fbm(p * 0.36 + vec2(3.1, 7.7));
          n += 0.12 * fbm(p * 2.1);
          // a few art-directed pools where the camera looks across the ground
          n += 0.20 * exp(-dot(p - vec2(3.9, -2.0), p - vec2(3.9, -2.0)) * 0.55);
          n += 0.16 * exp(-dot(p - vec2(-1.4, -2.7), p - vec2(-1.4, -2.7)) * 0.7);
          n += 0.14 * exp(-dot(p - vec2(-4.2, 1.5), p - vec2(-4.2, 1.5)) * 0.8);
          gl_FragColor = vec4(n, 0.0, 0.0, 1.0);
        }`,
      depthTest: false, depthWrite: false,
    });
    const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat);
    quad.frustumCulled = false;
    const scene = new THREE.Scene();
    scene.add(quad);
    const prev = renderer.getRenderTarget();
    renderer.setRenderTarget(rt);
    renderer.render(scene, new THREE.OrthographicCamera());
    renderer.setRenderTarget(prev);
    quad.geometry.dispose();
    mat.dispose();
    this.puddleTarget = rt;
    this.uniforms.tPuddle.value = rt.texture;
  }

  update(renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.PerspectiveCamera, hide: THREE.Object3D[], t: number, bg: THREE.Color) {
    this.bakePuddles(renderer);
    this.uniforms.uTime.value = t;
    this.uniforms.uBg.value.copy(bg);
    // the reflection pass reuses the main pass's shadow maps, so wait until those exist
    if (this.frames++ < 2) {
      this.uniforms.uReflOn.value = 0;
      return;
    }
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
