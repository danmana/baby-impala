import * as THREE from 'three';

/**
 * Procedural night environment for reflections. Mostly darkness, with a few
 * soft light shapes so the clear-coat and chrome have something to pick up:
 * a dim overhead glow, a warm sodium strip, a cool strip, a faint horizon.
 * The motel variant adds warm windows and the red neon sign.
 */
export function buildEnvironment(renderer: THREE.WebGLRenderer, motel: boolean): THREE.Texture {
  const scene = new THREE.Scene();
  const sky = new THREE.Mesh(
    new THREE.SphereGeometry(60, 48, 24),
    new THREE.ShaderMaterial({
      side: THREE.BackSide,
      depthWrite: false,
      uniforms: {},
      vertexShader: /* glsl */ `
        varying vec3 vDir;
        void main() {
          vDir = normalize(position);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }`,
      fragmentShader: /* glsl */ `
        varying vec3 vDir;
        void main() {
          float h = vDir.y;
          vec3 top = vec3(0.010, 0.012, 0.018);
          vec3 hor = vec3(0.030, 0.030, 0.036);
          // below the horizon: wet road reflecting the night glow, brighter towards the horizon
          vec3 gnd = vec3(0.05, 0.047, 0.045);
          vec3 c = h > 0.0 ? mix(hor, top, smoothstep(0.0, 0.6, h)) : mix(hor * 1.6, gnd, smoothstep(0.0, 0.45, -h));
          gl_FragColor = vec4(c, 1.0);
        }`,
    }),
  );
  scene.add(sky);

  const add = (w: number, h: number, color: THREE.ColorRepresentation, intensity: number,
    pos: [number, number, number], lookAt: [number, number, number] = [0, 1, 0]) => {
    const m = new THREE.Mesh(
      new THREE.PlaneGeometry(w, h),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(intensity), side: THREE.DoubleSide }),
    );
    m.position.set(...pos);
    m.lookAt(...lookAt);
    scene.add(m);
    return m;
  };

  // soft overhead glow (a parking-lot lamp far above)
  add(26, 10, 0x8fa0b8, 1.1, [2, 22, -2]);
  // long horizontal strips for the classic body-side highlight lines
  add(40, 1.2, 0xffa24a, 3.0, [-6, 5.5, -24]);
  add(40, 0.9, 0x9fb4d0, 2.2, [4, 4.0, 24]);
  add(1.2, 30, 0xb0c0d8, 1.2, [26, 6, 0]);
  add(1.2, 30, 0xffb070, 0.9, [-26, 6, 4]);
  // broad soft panels low on either side: the long highlight down her flanks
  add(18, 3.2, 0xffd9b0, 0.55, [14, 2.6, -13]);
  add(18, 3.2, 0x9fb2d6, 0.45, [-14, 2.6, 13]);
  // a thin overhead tube along the car: a crisp line over the hood and roof
  add(24, 0.35, 0xdfe6f2, 2.4, [0, 11, -1.5]);
  // distant street lamps around the horizon: sparkle in the chrome
  for (let i = 0; i < 9; i++) {
    const a = (i / 9) * Math.PI * 2 + 0.3;
    const warm = i % 3 !== 0;
    add(1.6, 0.9, warm ? 0xffb56a : 0xbfd0ff, warm ? 5 : 3.5, [Math.cos(a) * 30, 2.5 + (i % 2) * 1.8, Math.sin(a) * 30], [0, 2, 0]);
  }
  // wet ground catching the sky glow, just below the horizon
  add(60, 6, 0x3a3634, 0.9, [0, -1.5, -26], [0, -1.5, 0]);
  add(60, 6, 0x2e3440, 0.9, [0, -1.5, 26], [0, -1.5, 0]);
  add(6, 60, 0x3a3634, 0.8, [-26, -1.5, 0], [0, -1.5, 0]);
  add(6, 60, 0x303440, 0.8, [26, -1.5, 0], [0, -1.5, 0]);
  // faint horizon glow ring
  const ring = new THREE.Mesh(
    new THREE.CylinderGeometry(40, 40, 3, 64, 1, true),
    new THREE.MeshBasicMaterial({ color: new THREE.Color(0x1a1c24).multiplyScalar(1.0), side: THREE.BackSide }),
  );
  ring.position.y = 1.0;
  scene.add(ring);

  if (motel) {
    // warm motel windows and the red VACANCY neon behind the car
    for (let i = 0; i < 5; i++) add(2.2, 1.2, 0xffb36b, 0.7, [-9 + i * 4.5, 1.6, 7], [0, 1.6, 0]);
    add(2.8, 0.8, 0xff1a1a, 3.2, [-1.3, 2.8, 3.8], [0, 1, 0]);
    add(30, 6, 0x301816, 0.6, [0, 3, 8], [0, 3, 0]);
  }

  const pmrem = new THREE.PMREMGenerator(renderer);
  const rt = pmrem.fromScene(scene, 0.015, 0.1, 100);
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
