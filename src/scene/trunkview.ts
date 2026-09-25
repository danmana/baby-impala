import * as THREE from 'three';
import type { CarParts } from './car';

const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

/**
 * The trunk sequence: the lid pops and swings up (hinge creak), the false
 * floor lifts and stands upright, and a work light comes on over the gear.
 */
export class TrunkRig {
  private lid: THREE.Object3D | null;
  private board: THREE.Object3D | null;
  private lidAngle = 0;
  private boardAngle = 0;
  private target = 0;
  private clock = 0;
  readonly lamp2: THREE.SpotLight;
  readonly items: THREE.Mesh[] = [];
  onOpen: (() => void) | null = null;
  onClose: (() => void) | null = null;
  reduced = false;
  private creaked = false;
  // the lid hinges at its top-front edge and swings clear of the rear window;
  // the false floor leans back a little so it clears the open lid
  static LID_OPEN = THREE.MathUtils.degToRad(72);
  static BOARD_OPEN = THREE.MathUtils.degToRad(78);

  constructor(car: CarParts) {
    this.lid = car.byName.get('trunk_lid') ?? null;
    this.board = car.byName.get('false_floor') ?? null;
    car.root.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      // items are named item_<key>; a multi-material item arrives as a group
      // item_<key> holding meshes item_<key>_1, _2…, so the outermost wins
      let key: string | null = null;
      for (let p: THREE.Object3D | null = m; p; p = p.parent) {
        if (p.name.startsWith('item_')) key = p.name.slice(5).replace(/_\d{3}$/, '');
      }
      if (key) {
        m.userData.item = key;
        this.items.push(m);
      }
    });
    // a work light behind the car, aimed into the trunk and up at the painted lid
    this.lamp2 = new THREE.SpotLight(0xffe7c4, 0, 6, 0.75, 0.85, 1.4);
    this.lamp2.position.set(-3.9, 1.35, 0.35);
    this.lamp2.target.position.set(-2.0, 1.15, 0);
    car.root.add(this.lamp2, this.lamp2.target);
  }

  open(on: boolean) {
    if (!on && this.target === 1 && this.clock > 0.3) this.onClose?.();
    this.target = on ? 1 : 0;
    if (on) this.creaked = false;
  }

  get isOpen() { return this.target === 1; }
  /** 0..1 how far the whole sequence has progressed */
  get progress() { return this.clock / 3.4; }

  update(dt: number) {
    const speed = this.reduced ? 4 : 1;
    this.clock = THREE.MathUtils.clamp(this.clock + (this.target ? dt : -dt * 1.4) * speed, 0, 3.4);
    // lid: 0.0 - 1.4s ; floor: 1.3 - 3.0s
    const lidK = ease(THREE.MathUtils.clamp(this.clock / 1.4, 0, 1));
    const boardK = ease(THREE.MathUtils.clamp((this.clock - 1.3) / 1.7, 0, 1));
    if (this.target && this.clock > 0.02 && !this.creaked) {
      this.creaked = true;
      this.onOpen?.();
    }
    this.lidAngle = TrunkRig.LID_OPEN * lidK;
    this.boardAngle = TrunkRig.BOARD_OPEN * boardK;
    // hinge axis is the car's width (three.js Z); rear edges swing up
    if (this.lid) this.lid.rotation.z = -this.lidAngle;
    if (this.board) this.board.rotation.z = -this.boardAngle;
    const light = THREE.MathUtils.clamp((this.clock - 0.6) / 1.2, 0, 1);
    this.lamp2.intensity = 6 * light;
  }
}
