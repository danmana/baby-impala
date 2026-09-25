import * as THREE from 'three';
import type { CarParts } from './car';

interface PartDef {
  label: string;
  /** node names (prefix match) that move together */
  names: string[];
  /** prefixes to leave behind even though they match `names` */
  exclude?: string[];
  /** offset in car space (three.js axes: x forward, y up, z passenger side) */
  offset: [number, number, number];
  delay: number;
  /** where the label sits relative to the part's exploded centre */
  labelOffset?: [number, number, number];
  noLabel?: boolean;
}

const PARTS: PartDef[] = [
  { label: 'Hood', names: ['hood'], offset: [0.35, 1.25, 0], delay: 0.0 },
  { label: 'Trunk lid', names: ['trunk_lid'], offset: [-0.75, 0.95, 0], delay: 0.05, labelOffset: [-0.3, 0.1, 0] },
  { label: 'Front door', names: ['door_fl'], offset: [0.1, 0.1, -1.05], delay: 0.15 },
  { label: 'Rear door', names: ['door_rl'], offset: [-0.1, 0.1, -1.05], delay: 0.22 },
  { label: 'Front door', names: ['door_fr'], offset: [0.1, 0.1, 1.05], delay: 0.18, noLabel: true },
  { label: 'Rear door', names: ['door_rr'], offset: [-0.1, 0.1, 1.05], delay: 0.25, noLabel: true },
  // the engine lifts out of its bay; the bay itself stays in the car
  { label: '327 V8', names: ['engine'], exclude: ['engine_bay'], offset: [0.2, 0.62, 0], delay: 0.4, labelOffset: [0, 0.45, 0] },
  { label: 'Windshield', names: ['FrontGlass_Window', 'FrontChromeglass_Chrome', 'Wcleaner'], offset: [0.55, 0.95, 0], delay: 0.3 },
  { label: 'Rear window', names: ['BackGlass_Window', 'ChromeBackGlass_Chrome'], offset: [-0.35, 1.05, 0], delay: 0.35, labelOffset: [0.1, 0.25, -0.4] },
  { label: 'Front bumper', names: ['FrontBump_Chrome', 'frontBumpTooth_Chrome', 'ColorLamp_FrontChromes', 'anchor_plate_front_holder'], offset: [0.75, -0.02, 0], delay: 0.28, labelOffset: [0.2, -0.15, 0] },
  { label: 'Grille & quad headlamps', names: ['Grill_FrontChromes', 'script_front', 'FrameLapm_FrontChromes', 'LampMirror_FrontChromes', 'LampBulb_FrontChromes', 'GlassLapm_Window', 'FrontCoverLamp_FrontChromes', 'Frontchromemask_Chrome'], offset: [0.5, 0.18, 0], delay: 0.34, labelOffset: [0.15, 0.2, 0] },
  { label: 'Rear bumper', names: ['Backbump_Chrome', 'anchor_plate_rear_holder', 'exhaust'], offset: [-0.8, -0.02, 0], delay: 0.3, labelOffset: [-0.2, -0.15, 0] },
  { label: 'Wheel & tyre', names: ['tire_fl', 'rim_fl', 'drum_fl'], offset: [0.05, 0, -0.85], delay: 0.45, labelOffset: [0, -0.32, 0] },
  { label: 'Wheel', names: ['tire_rl', 'rim_rl', 'drum_rl'], offset: [-0.05, 0, -0.85], delay: 0.5, noLabel: true },
  { label: 'Wheel', names: ['tire_fr', 'rim_fr', 'drum_fr'], offset: [0.05, 0, 0.85], delay: 0.48, noLabel: true },
  { label: 'Wheel', names: ['tire_rr', 'rim_rr', 'drum_rr'], offset: [-0.05, 0, 0.85], delay: 0.53, noLabel: true },
  { label: 'Bench seats', names: ['CouchUP_Indoor', 'CouchDown_Indoor'], offset: [0, 0.95, 0], delay: 0.6, labelOffset: [0, 0.3, 0] },
  { label: 'Dash & tape deck', names: ['Desktop_Indoor', 'BaseClock_Indoor', 'ArrowClock_Indoor', 'tape_deck', 'tape_deck_dial', 'legos', 'defroster_vent'], offset: [0.1, 1.5, 0], delay: 0.66, labelOffset: [0, 0.22, 0] },
  { label: 'Steering wheel', names: ['DonutDrive_Indoor', 'BracketDrive_Indoor', 'BaseDrive_Indoor', 'Leaver_Indoor'], offset: [-0.25, 1.9, -0.25], delay: 0.7, labelOffset: [0, 0.25, 0] },
  { label: 'Spotlight', names: ['spotlight_l', 'spot_mount_l', 'spot_handle_l'], offset: [0.1, 0.35, -0.55], delay: 0.36 },
  { label: 'Spotlight', names: ['spotlight_r', 'spot_mount_r', 'spot_handle_r'], offset: [0.1, 0.35, 0.55], delay: 0.38, noLabel: true },
];

const DUR = 2.4;
const ease = (t: number) => (t < 0.5 ? 16 * t ** 5 : 1 - Math.pow(-2 * t + 2, 5) / 2); // quintic: slow, heavy

interface Live {
  def: PartDef;
  objs: THREE.Object3D[];
  base: THREE.Vector3[];
  centre: THREE.Vector3;
  offset: THREE.Vector3;
  line: THREE.Line;
}

/** The blueprint moment: parts drift apart with dotted guide lines and pencilled labels. */
export class Exploder {
  private live: Live[] = [];
  private target = 0;
  private clock = 0;
  readonly lines = new THREE.Group();
  readonly labels: { text: string; pos: THREE.Vector3; alpha: number }[] = [];
  reduced = false;

  constructor(car: CarParts) {
    const lineMat = new THREE.LineDashedMaterial({ color: 0xe9ddbf, dashSize: 0.05, gapSize: 0.04, transparent: true, opacity: 0, depthTest: true });
    for (const def of PARTS) {
      const objs: THREE.Object3D[] = [];
      car.root.traverse((o) => {
        if (def.exclude?.some((x) => o.name.startsWith(x))) return;
        if (def.names.some((n) => o.name === n || (o.name.startsWith(n) && o.parent?.name !== n && !objs.some((p) => isAncestor(p, o))))) {
          if (!objs.some((p) => isAncestor(p, o))) objs.push(o);
        }
      });
      if (!objs.length) continue;
      const box = new THREE.Box3();
      objs.forEach((o) => box.expandByObject(o));
      const centre = box.getCenter(new THREE.Vector3());
      const offset = new THREE.Vector3(...def.offset);
      const geo = new THREE.BufferGeometry().setFromPoints([centre.clone(), centre.clone().add(offset)]);
      const line = new THREE.Line(geo, lineMat.clone());
      line.computeLineDistances();
      this.lines.add(line);
      this.live.push({ def, objs, base: objs.map((o) => o.position.clone()), centre, offset, line });
      if (!def.noLabel) {
        const lo = new THREE.Vector3(...(def.labelOffset ?? [0, 0.18, 0]));
        this.labels.push({ text: def.label, pos: centre.clone().add(offset).add(lo), alpha: 0 });
      }
    }
  }

  set(exploded: boolean) { this.target = exploded ? 1 : 0; }
  /** 0..1 overall progress */
  get progress() { return THREE.MathUtils.clamp(this.clock / (DUR + 0.8), 0, 1); }
  get active() { return this.target > 0 || this.clock > 0; }

  update(dt: number) {
    const total = DUR + 0.8;
    const speed = this.reduced ? 6 : 1;
    this.clock = THREE.MathUtils.clamp(this.clock + (this.target ? dt : -dt) * speed, 0, total);
    let li = 0;
    for (const L of this.live) {
      const local = THREE.MathUtils.clamp((this.clock - L.def.delay) / DUR, 0, 1);
      const k = ease(local);
      L.objs.forEach((o, i) => {
        o.position.copy(L.base[i]).addScaledVector(L.offset, k);
      });
      const m = L.line.material as THREE.LineDashedMaterial;
      m.opacity = Math.min(1, local * 2.5) * 0.75;
      L.line.visible = local > 0.01;
      const end = L.centre.clone().addScaledVector(L.offset, k);
      const pos = L.line.geometry.getAttribute('position') as THREE.BufferAttribute;
      pos.setXYZ(1, end.x, end.y, end.z);
      pos.needsUpdate = true;
      L.line.computeLineDistances();
      if (!L.def.noLabel) {
        const lab = this.labels[li++];
        lab.alpha = THREE.MathUtils.clamp((local - 0.7) / 0.3, 0, 1);
      }
    }
  }
}

function isAncestor(a: THREE.Object3D, b: THREE.Object3D) {
  let p: THREE.Object3D | null = b.parent;
  while (p) {
    if (p === a) return true;
    p = p.parent;
  }
  return false;
}
