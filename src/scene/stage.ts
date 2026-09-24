import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import type { Quality } from './quality';

/** Film grain + vignette, applied after tone mapping. */
const GrainShader = {
  uniforms: { tDiffuse: { value: null }, uTime: { value: 0 }, uAmount: { value: 0.045 }, uVignette: { value: 1.0 } },
  vertexShader: /* glsl */ `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: /* glsl */ `
    uniform sampler2D tDiffuse; uniform float uTime; uniform float uAmount; uniform float uVignette;
    varying vec2 vUv;
    float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
    void main(){
      vec4 c = texture2D(tDiffuse, vUv);
      vec2 d = vUv - 0.5;
      float v = smoothstep(0.85, 0.2, length(d * vec2(1.0, 0.8)));
      c.rgb *= mix(1.0, v, 0.75 * uVignette);
      float n = h(vUv * 1000.0 + fract(uTime) * 91.7) - 0.5;
      c.rgb += n * uAmount * (0.35 + 0.65 * (1.0 - dot(c.rgb, vec3(0.333))));
      gl_FragColor = c;
    }`,
};

export class Stage {
  readonly renderer: THREE.WebGLRenderer;
  readonly scene = new THREE.Scene();
  readonly camera: THREE.PerspectiveCamera;
  composer!: EffectComposer;
  bloom: UnrealBloomPass | null = null;
  grain!: ShaderPass;
  private renderPass!: RenderPass;

  constructor(private host: HTMLElement, public quality: Quality) {
    this.renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance', stencil: false });
    this.renderer.setPixelRatio(quality.pixelRatio);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    this.renderer.shadowMap.enabled = quality.shadows;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    host.appendChild(this.renderer.domElement);
    this.renderer.domElement.setAttribute('aria-label', 'Interactive 3D view of Baby, the 1967 Chevrolet Impala');
    this.renderer.domElement.setAttribute('role', 'img');
    this.scene.background = new THREE.Color(0x000000);
    this.scene.fog = new THREE.FogExp2(0x020203, 0.045);
    this.camera = new THREE.PerspectiveCamera(38, 1, 0.05, 80);
    RectAreaLightUniformsLib.init();
    this.buildComposer();
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  buildComposer() {
    if (this.composer) this.composer.dispose();
    const size = this.renderer.getDrawingBufferSize(new THREE.Vector2());
    const rt = new THREE.WebGLRenderTarget(Math.max(1, size.x), Math.max(1, size.y), {
      type: THREE.HalfFloatType,
      samples: this.quality.msaa,
    });
    this.composer = new EffectComposer(this.renderer, rt);
    this.renderPass = new RenderPass(this.scene, this.camera);
    this.composer.addPass(this.renderPass);
    if (this.quality.bloom) {
      this.bloom = new UnrealBloomPass(new THREE.Vector2(size.x, size.y), 0.5, 0.5, 0.9);
      this.composer.addPass(this.bloom);
    } else {
      this.bloom = null;
    }
    this.composer.addPass(new OutputPass());
    this.grain = new ShaderPass(GrainShader);
    this.composer.addPass(this.grain);
  }

  setQuality(q: Quality) {
    const shadowsChanged = this.renderer.shadowMap.enabled !== q.shadows;
    this.quality = q;
    this.renderer.setPixelRatio(q.pixelRatio);
    this.renderer.shadowMap.enabled = q.shadows;
    if (shadowsChanged) {
      // programs compiled with shadow samplers must be rebuilt
      this.scene.traverse((o) => {
        const m = (o as THREE.Mesh).material as THREE.Material | THREE.Material[] | undefined;
        if (!m) return;
        (Array.isArray(m) ? m : [m]).forEach((x) => (x.needsUpdate = true));
      });
    }
    this.buildComposer();
    this.resize();
  }

  resize() {
    const w = this.host.clientWidth || window.innerWidth;
    const h = this.host.clientHeight || window.innerHeight;
    this.camera.aspect = w / h;
    // keep Baby filling the frame on tall phone screens
    this.camera.fov = w / h < 0.8 ? 52 : w / h < 1.2 ? 44 : 38;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
    this.composer.setSize(w, h);
    this.composer.setPixelRatio(this.renderer.getPixelRatio());
  }

  render(t: number) {
    this.grain.uniforms.uTime.value = t;
    this.composer.render();
  }
}
