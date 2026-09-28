/**
 * Dev only: the shots for the videos, recorded by capture.ts. Each shot sets
 * the scene up (instantly, then `warm` seconds of simulation to settle), then
 * runs `dur` seconds with the camera on a path and cues at set times.
 * The car sits at the origin, nose towards +X, 5.4 m long.
 */
import * as THREE from 'three';

// the page's debug handle (window.__baby): loosely typed on purpose
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Baby = any;
type V3 = [number, number, number];

export interface Shot {
  dur: number;
  warm?: number;
  setup?: (B: Baby) => void | Promise<void>;
  cues?: [number, (B: Baby) => void][];
  /** returns the camera for 0..1 through the shot */
  cam?: (B: Baby) => (u: number) => void;
}

export interface Key { pos: V3; look: V3; fov?: number }

const sine = (t: number) => 0.5 - 0.5 * Math.cos(Math.PI * t);
export const linear = (t: number) => t;

/** a smooth camera move through keys (centripetal Catmull-Rom), eased over the whole shot */
export function path(keys: Key[], ease: (t: number) => number = sine) {
  return (B: Baby) => {
    const cam: THREE.PerspectiveCamera = B.camera;
    const v = (p: V3) => new THREE.Vector3(...p);
    const pos = keys.length > 1 ? new THREE.CatmullRomCurve3(keys.map((k) => v(k.pos)), false, 'centripetal') : null;
    const look = keys.length > 1 ? new THREE.CatmullRomCurve3(keys.map((k) => v(k.look)), false, 'centripetal') : null;
    const fov0 = keys[0].fov ?? 38, fov1 = keys[keys.length - 1].fov ?? fov0;
    const tmp = new THREE.Vector3();
    return (u: number) => {
      const e = ease(u);
      if (pos && look) {
        cam.position.copy(pos.getPoint(e));
        cam.lookAt(look.getPoint(e, tmp));
      } else {
        cam.position.set(...keys[0].pos);
        cam.lookAt(...keys[0].look);
      }
      cam.fov = fov0 + (fov1 - fov0) * e;
      cam.updateProjectionMatrix();
    };
  };
}

/** keys round a circle: from/to in degrees (0 = +X, towards the nose; -90 = the -Z side) */
export function orbit(o: { r: number; y: number; from: number; to: number; look: V3; c?: V3; n?: number; fov?: number; y1?: number; r1?: number }): Key[] {
  const n = o.n ?? 8, c = o.c ?? [0, 0, 0];
  const keys: Key[] = [];
  for (let i = 0; i <= n; i++) {
    const k = i / n;
    const a = THREE.MathUtils.degToRad(o.from + (o.to - o.from) * k);
    const r = o.r + ((o.r1 ?? o.r) - o.r) * k;
    const y = o.y + ((o.y1 ?? o.y) - o.y) * k;
    keys.push({ pos: [c[0] + r * Math.cos(a), y, c[2] + r * Math.sin(a)], look: o.look, fov: o.fov });
  }
  return keys;
}

interface SceneState {
  light?: 'moon' | 'sunrise' | 'day';
  engine?: boolean;
  spots?: boolean;
  rain?: boolean;
  motel?: boolean;
  sigils?: boolean;
  view?: 'normal' | 'exploded' | 'trunk' | 'interior';
}

/** put the scene in a state at once (the shot's warm-up lets lamps and fades settle) */
export function scene(B: Baby, s: SceneState) {
  const st = { light: 'moon', engine: true, spots: false, rain: false, motel: false, sigils: false, view: 'normal', ...s } as Required<SceneState>;
  B.rig.set(st.light, true);
  B.toggle('engine', st.engine);
  B.lights.setHeadlights(st.engine);
  B.toggle('spotlights', st.spots);
  B.toggle('rain', st.rain);
  B.toggle('motel', st.motel);
  B.toggle('sigils', st.sigils);
  if (B.director.view !== st.view) B.setView(st.view);
}

const at = (t: number, f: (B: Baby) => void): [number, (B: Baby) => void] => [t, f];

/** night, trunk open, the arsenal up (give it a warm of 6 s) */
const trunkOpen = (B: Baby) => {
  scene(B, { view: 'trunk' });
  B.trunk.open(true);
};

/** the hover glow the site puts round a piece of gear while its page is open */
const glow = (key: string | null) => (B: Baby) => {
  const meshes: THREE.Object3D[] = [];
  if (key) B.car.root.traverse((o: THREE.Object3D) => o.userData?.item === key && (o as THREE.Mesh).isMesh && meshes.push(o));
  B.stage.select(meshes);
};

/** a close-up on a piece of gear, framed left of centre so its journal page fits on the right */
function closeup(key: string, from: V3, to: V3, look: V3, fov = 38): Shot {
  return {
    dur: 6, warm: 6,
    setup: (B) => {
      trunkOpen(B);
      B.stage.select([]);
    },
    cues: [at(0.7, glow(key)), at(5.9, glow(null))],
    cam: path([{ pos: from, look, fov }, { pos: to, look: [look[0], look[1], look[2] - 0.012], fov }]),
  };
}

export const SHOTS: Record<string, Shot> = {
  // ------------------------------------------------------------------ demo
  /** moonlight, engine off: a slow push in on her front three-quarter */
  hero: {
    dur: 5, warm: 3,
    setup: (B) => scene(B, { engine: false }),
    cam: path([
      { pos: [4.9, 0.5, -3.6], look: [0.3, 0.72, 0], fov: 40 },
      { pos: [3.9, 0.46, -2.7], look: [0.4, 0.7, 0], fov: 40 },
    ]),
  },
  /** low at the grille: she starts, the quad lamps come up through the fog */
  start: {
    dur: 4.5, warm: 3,
    setup: (B) => scene(B, { engine: false }),
    cues: [
      at(0.6, (B) => {
        B.toggle('engine', true);
        B.lights.setHeadlights(false);
      }),
      at(1.5, (B) => B.lights.setHeadlights(true)),
    ],
    cam: path([
      { pos: [5.0, 0.42, -2.2], look: [2.4, 0.62, 0.05], fov: 40 },
      { pos: [4.5, 0.45, -1.75], look: [2.4, 0.64, 0.05], fov: 38 },
    ]),
  },
  /** the A-pillar spotlights come on and sweep the fog */
  spots: {
    dur: 5, warm: 3,
    setup: (B) => scene(B, {}),
    cues: [at(0.4, (B) => B.toggle('spotlights', true))],
    cam: path([
      { pos: [7.5, 1.7, -3.2], look: [1.0, 1.0, 0] },
      { pos: [7.0, 1.5, -1.2], look: [1.0, 1.0, 0] },
    ]),
  },
  /** from behind her, towards the east: the moon sets, the sun comes up and climbs */
  sunrise: {
    dur: 8, warm: 3,
    setup: (B) => scene(B, { light: 'moon' }),
    cues: [at(0.5, (B) => B.setLight('sunrise')), at(3.9, (B) => B.setLight('day'))],
    cam: path([
      { pos: [-5.6, 0.85, 6.4], look: [1.5, 1.5, -1.9], fov: 55 },
      { pos: [-5.0, 0.8, 6.8], look: [1.7, 1.5, -2.1], fov: 55 },
    ]),
  },
  /** rain at the motel, neon in the puddles */
  rain: {
    dur: 5, warm: 4,
    setup: (B) => scene(B, { rain: true, motel: true }),
    cam: path(orbit({ r: 6.4, y: 0.6, from: -150, to: -120, look: [0, 0.8, 0], y1: 0.75 })),
  },
  /** the workshop: she comes apart */
  exploded: {
    dur: 6, warm: 4,
    setup: (B) => scene(B, { light: 'day', engine: false }),
    cues: [at(0.3, (B) => B.setView('exploded'))],
    cam: path(orbit({ r: 7.6, y: 2.6, from: -52, to: -22, look: [0, 0.8, 0], r1: 8.4, y1: 3.1 })),
  },
  /** the trunk: lid up, the arsenal rises */
  trunk: {
    dur: 6.5, warm: 4,
    setup: (B) => scene(B, {}),
    cues: [at(0.2, (B) => B.setView('trunk'))],
    cam: path([
      { pos: [-6.6, 1.9, 1.9], look: [-2.0, 1.2, 0] },
      { pos: [-5.3, 2.3, 0.6], look: [-2.0, 1.25, 0] },
    ]),
  },
  /** inside: the dash and the tape deck */
  interior: {
    dur: 5, warm: 3,
    setup: (B) => scene(B, { light: 'sunrise', view: 'interior' }),
    cam: path([
      { pos: [-0.85, 1.36, 0.06], look: [0.9, 0.93, -0.24], fov: 55 },
      { pos: [-0.34, 1.3, -0.08], look: [0.9, 0.95, -0.26], fov: 55 },
    ]),
  },
  // ------------------------------------------------------------------ trunk video
  /** low behind her at night, walking up to the trunk */
  t_approach: {
    dur: 6, warm: 3,
    setup: (B) => scene(B, {}),
    cam: path([
      { pos: [-7.8, 0.5, 2.5], look: [-2.3, 0.8, 0] },
      { pos: [-5.5, 0.72, 1.0], look: [-2.3, 0.82, 0] },
    ]),
  },
  /** the latch, the lid, the board standing up */
  t_open: {
    dur: 8.5, warm: 3,
    setup: (B) => scene(B, {}),
    cues: [at(0.3, (B) => {
      B.setView('trunk');
      B.trunk.open(true);
    })],
    cam: path([
      { pos: [-5.0, 1.4, 1.35], look: [-1.95, 1.05, 0] },
      { pos: [-4.0, 2.0, 0.3], look: [-1.95, 1.12, 0] },
    ]),
  },
  /** the Devil's Trap on the underside of the lid */
  t_trap: {
    dur: 6, warm: 6,
    setup: trunkOpen,
    cam: path([
      { pos: [-3.75, 1.12, 0.88], look: [-1.88, 1.6, 0.44], fov: 44 },
      { pos: [-3.4, 1.18, 0.72], look: [-1.88, 1.62, 0.42], fov: 44 },
    ]),
  },
  /** along the pegboard */
  t_board: {
    dur: 6, warm: 6,
    setup: trunkOpen,
    cam: path([
      { pos: [-2.62, 1.02, -0.72], look: [-1.76, 0.96, -0.6], fov: 44 },
      { pos: [-2.62, 1.0, 0.72], look: [-1.76, 0.96, 0.6], fov: 44 },
    ]),
  },
  t_ruby: closeup('ruby_knife', [-2.38, 0.96, -0.28], [-2.33, 0.95, -0.34], [-1.758, 0.93, -0.15]),
  t_pistol: closeup('pistol', [-2.27, 0.93, 0.47], [-2.22, 0.91, 0.41], [-1.756, 0.885, 0.54]),
  t_colt: closeup('colt', [-2.52, 0.95, 0.16], [-2.44, 0.9, 0.07], [-1.968, 0.475, 0.17], 40),
  t_emf: closeup('emf', [-2.47, 0.8, -0.41], [-2.43, 0.76, -0.47], [-2.18, 0.48, -0.39], 40),
  /** back out: the whole car, trunk up */
  t_out: {
    dur: 8.5, warm: 6,
    setup: trunkOpen,
    cam: path([
      { pos: [-3.5, 1.5, 0.6], look: [-1.95, 1.05, 0] },
      { pos: [-7.2, 1.15, 2.9], look: [-1.1, 0.9, 0] },
    ]),
  },

  /** out: night, everything on, a low slow orbit round her tail */
  finale: {
    dur: 8.5, warm: 3,
    setup: (B) => scene(B, { spots: true }),
    cam: path(orbit({ r: 6.0, y: 0.5, from: -212, to: -150, look: [0, 0.72, 0] })),
  },
};
