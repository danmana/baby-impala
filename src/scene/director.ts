import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export type ViewName = 'normal' | 'exploded' | 'trunk' | 'interior';

interface ViewDef {
  pos: THREE.Vector3;
  target: THREE.Vector3;
  minDist: number;
  maxDist: number;
  minPolar: number;
  maxPolar: number;
  pan: boolean;
  /** extra positions the camera passes through on its way in (e.g. through a window) */
  via?: THREE.Vector3[];
}

const V = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);
const deg = THREE.MathUtils.degToRad;

export const VIEWS: Record<ViewName, ViewDef> = {
  normal: { pos: V(5.35, 1.02, -4.35), target: V(0.25, 0.62, 0), minDist: 3.2, maxDist: 9.5, minPolar: deg(52), maxPolar: deg(88), pan: false },
  exploded: { pos: V(8.2, 3.6, -7.6), target: V(0, 0.95, 0), minDist: 5, maxDist: 15, minPolar: deg(25), maxPolar: deg(86), pan: false },
  trunk: { pos: V(-4.85, 2.25, 0.55), target: V(-2.05, 1.05, 0), minDist: 0.9, maxDist: 6.5, minPolar: deg(20), maxPolar: deg(88), pan: true },
  interior: {
    // mid-cabin, just behind the front bench: look around from here
    pos: V(-0.28, 1.265, 0.0), target: V(0.72, 1.06, 0.0), minDist: 0.25, maxDist: 0.75,
    minPolar: deg(55), maxPolar: deg(120), pan: false,
    via: [V(-0.3, 1.2, -2.3), V(-0.35, 1.17, -1.0)],
  },
};

const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

/**
 * Owns the camera: orbit controls per view, smooth glides between views
 * (arcing around the car, never through it), the opening cinematic, and the
 * motel wall the camera must not pass.
 */
export class Director {
  readonly controls: OrbitControls;
  view: ViewName = 'normal';
  private tween: {
    curve: THREE.CatmullRomCurve3; target0: THREE.Vector3; target1: THREE.Vector3; t: number; dur: number;
    done?: () => void;
  } | null = null;
  reduced = false;
  wallZ: number | null = null;
  onInteract: (() => void) | null = null;
  private intro = false;

  // interior look-around (the camera stays put, you turn your head)
  private yaw = 0;
  private pitch = 0;
  private lookZoom = 0.6;
  private drag: { x: number; y: number; id: number } | null = null;
  private pinch = 0;
  private pointers = new Map<number, { x: number; y: number }>();

  get lookMode() { return this.view === 'interior' && !this.tween; }

  private installLook(dom: HTMLElement) {
    dom.addEventListener('pointerdown', (e) => {
      if (!this.lookMode) return;
      this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (this.pointers.size === 1) this.drag = { x: e.clientX, y: e.clientY, id: e.pointerId };
      this.onInteract?.();
    });
    dom.addEventListener('pointermove', (e) => {
      if (!this.lookMode || !this.pointers.has(e.pointerId)) return;
      this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (this.pointers.size === 2) {
        const [a, b] = [...this.pointers.values()];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (this.pinch) this.lookZoom = THREE.MathUtils.clamp(this.lookZoom * (d / this.pinch), 0.55, 2.2);
        this.pinch = d;
        return;
      }
      if (!this.drag || this.drag.id !== e.pointerId) return;
      const k = 0.0042 / this.lookZoom;
      this.yaw += (e.clientX - this.drag.x) * k;
      this.pitch = THREE.MathUtils.clamp(this.pitch + (e.clientY - this.drag.y) * k, -0.95, 0.7);
      this.drag.x = e.clientX;
      this.drag.y = e.clientY;
    });
    const end = (e: PointerEvent) => {
      this.pointers.delete(e.pointerId);
      if (this.pointers.size < 2) this.pinch = 0;
      if (this.drag?.id === e.pointerId) this.drag = null;
    };
    dom.addEventListener('pointerup', end);
    dom.addEventListener('pointercancel', end);
    dom.addEventListener('wheel', (e) => {
      if (!this.lookMode) return;
      e.preventDefault();
      this.lookZoom = THREE.MathUtils.clamp(this.lookZoom * Math.exp(-e.deltaY * 0.0012), 0.55, 2.2);
    }, { passive: false });
  }

  private applyLook() {
    const dir = new THREE.Vector3(Math.cos(this.pitch) * Math.cos(this.yaw), Math.sin(this.pitch), Math.cos(this.pitch) * Math.sin(this.yaw));
    this.controls.target.copy(this.camera.position).add(dir);
    this.camera.lookAt(this.controls.target);
    if (Math.abs(this.camera.zoom - this.lookZoom) > 1e-3) {
      this.camera.zoom += (this.lookZoom - this.camera.zoom) * 0.25;
      this.camera.updateProjectionMatrix();
    }
  }

  constructor(private camera: THREE.PerspectiveCamera, dom: HTMLElement) {
    this.installLook(dom);
    this.controls = new OrbitControls(camera, dom);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.07;
    this.controls.rotateSpeed = 0.6;
    this.controls.zoomSpeed = 0.8;
    this.controls.addEventListener('start', () => this.onInteract?.());
    this.apply(this.fit(VIEWS.normal), true);
  }

  private apply(v: ViewDef, snap: boolean) {
    const c = this.controls;
    c.minDistance = v.minDist;
    c.maxDistance = v.maxDist;
    c.minPolarAngle = v.minPolar;
    c.maxPolarAngle = v.maxPolar;
    c.enablePan = v.pan;
    c.screenSpacePanning = true;
    if (snap) {
      this.camera.position.copy(v.pos);
      c.target.copy(v.target);
      c.update();
    }
  }

  get busy() { return this.tween !== null; }

  /**
   * The views are composed for a ~16:10 screen, where she spans about two thirds
   * of the width. Narrower screens pull the camera back until she fits across.
   */
  private fit(v: ViewDef): ViewDef {
    if (v === VIEWS.interior) return v;
    const tanH = Math.tan(THREE.MathUtils.degToRad(this.camera.fov / 2)) * this.camera.aspect;
    const s = Math.max(1, 0.4 / tanH);
    if (s === 1) return v;
    const pos = v.target.clone().add(v.pos.clone().sub(v.target).multiplyScalar(s));
    return { ...v, pos, maxDist: v.maxDist * s, minDist: v.minDist * Math.min(s, 1.3) };
  }

  go(view: ViewName, onDone?: () => void) {
    const from = this.view;
    this.view = view;
    this.controls.enabled = view !== 'interior';
    if (from === 'interior') {
      this.camera.zoom = 1;
      this.camera.updateProjectionMatrix();
    }
    if (view === 'interior') this.lookZoom = 0.6;
    const v = this.fit(VIEWS[view]);
    const cam = this.camera;
    const c = this.controls;
    // loosen limits during the glide, set the real ones on arrival
    c.minDistance = 0.1;
    c.maxDistance = 50;
    c.minPolarAngle = 0;
    c.maxPolarAngle = Math.PI;
    const p0 = cam.position.clone();
    const pts = [p0];
    if (from === 'interior' && view !== 'interior') {
      // leave through the window first
      pts.push(...[...(VIEWS.interior.via ?? [])].reverse());
    }
    // arc around the car: a waypoint on a circle between start and end
    if (view !== 'interior' && from !== 'interior') {
      const a0 = Math.atan2(p0.z, p0.x);
      let a1 = Math.atan2(v.pos.z, v.pos.x);
      let da = a1 - a0;
      if (da > Math.PI) da -= Math.PI * 2;
      if (da < -Math.PI) da += Math.PI * 2;
      a1 = a0 + da;
      if (Math.abs(da) > 0.5) {
        const r0 = Math.hypot(p0.x, p0.z), r1 = Math.hypot(v.pos.x, v.pos.z);
        for (const f of [0.33, 0.66]) {
          const a = a0 + da * f;
          const r = Math.max(4.6, THREE.MathUtils.lerp(r0, r1, f) + 0.6);
          pts.push(V(Math.cos(a) * r, THREE.MathUtils.lerp(p0.y, v.pos.y, f) + 0.25, Math.sin(a) * r));
        }
      }
    }
    if (view === 'interior') pts.push(...(v.via ?? []));
    pts.push(v.pos.clone());
    const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal');
    const len = curve.getLength();
    const dur = this.reduced ? 0.35 : THREE.MathUtils.clamp(len / 3.2, 1.4, 3.2);
    this.tween = {
      curve, target0: c.target.clone(), target1: v.target.clone(), t: 0, dur,
      done: () => {
        this.apply(v, false);
        if (view === 'interior') {
          const d = v.target.clone().sub(v.pos).normalize();
          this.yaw = Math.atan2(d.z, d.x);
          this.pitch = Math.asin(d.y);
        }
        onDone?.();
      },
    };
  }

  /** Low, slow reveal: the camera starts near the ground ahead of her and swings to the hero shot. */
  playIntro(onDone?: () => void) {
    const v = this.fit(VIEWS.normal);
    if (this.reduced) {
      this.apply(v, true);
      onDone?.();
      return;
    }
    this.intro = true;
    this.camera.position.set(9.8, 0.32, 1.4);
    this.controls.target.set(1.6, 0.55, 0);
    const curve = new THREE.CatmullRomCurve3([
      V(9.8, 0.32, 1.4), V(8.4, 0.42, -1.4), V(6.8, 0.7, -3.6), v.pos.clone(),
    ], false, 'centripetal');
    this.controls.enabled = false;
    this.tween = {
      curve, target0: V(1.6, 0.55, 0), target1: v.target.clone(), t: 0, dur: 8.5,
      done: () => {
        this.intro = false;
        this.controls.enabled = true;
        this.apply(v, false);
        onDone?.();
      },
    };
  }

  get inIntro() { return this.intro; }

  reset() {
    if (this.view === 'interior') {
      const v = VIEWS.interior;
      const d = v.target.clone().sub(v.pos).normalize();
      this.yaw = Math.atan2(d.z, d.x);
      this.pitch = Math.asin(d.y);
      this.lookZoom = 0.6;
      return;
    }
    this.go(this.view);
  }

  update(dt: number) {
    if (this.tween) {
      const tw = this.tween;
      tw.t = Math.min(1, tw.t + dt / tw.dur);
      const k = this.intro ? 1 - Math.pow(1 - tw.t, 2.2) * (1 - tw.t * 0.2) : easeInOut(tw.t);
      this.camera.position.copy(tw.curve.getPoint(k));
      this.controls.target.lerpVectors(tw.target0, tw.target1, this.intro ? easeInOut(tw.t) : k);
      this.camera.lookAt(this.controls.target);
      if (tw.t >= 1) {
        this.tween = null;
        tw.done?.();
        if (this.view !== 'interior') this.controls.update();
      }
      return;
    }
    if (this.lookMode) {
      this.applyLook();
      return;
    }
    this.controls.update();
    // the motel wall is solid
    if (this.wallZ !== null && this.camera.position.z > this.wallZ - 0.5) {
      this.camera.position.z = this.wallZ - 0.5;
    }
    if (this.camera.position.y < 0.12) this.camera.position.y = 0.12;
  }
}
