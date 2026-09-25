import * as THREE from 'three';
import type { CarParts } from './car';
import type { Materials } from './materials';

/**
 * Baby's own lamps: headlight beams, the A-pillar spotlights, tail and signal
 * lenses, and a soft fill over the open trunk. (Sun, moon and sky light live in
 * the lighting rig.) Every light costs every lit pixel, so glows that don't
 * need to light anything (dash, plate lamp) are emissive only.
 */
export class Lights {
  readonly group = new THREE.Group();
  readonly heads: THREE.SpotLight[] = [];
  readonly spots: THREE.SpotLight[] = [];
  readonly spotPivots: THREE.Object3D[] = [];
  readonly cabin: THREE.PointLight;
  cabinTarget = 0;
  static readonly TRUNK = new THREE.Vector3(-2.05, 1.25, 0);
  headOn = 0; // 0..1 animated
  spotOn = 0;
  /** how strongly lamps glow for the current lighting preset */
  lampScale = 1;
  private headTarget = 0;
  private spotTarget = 0;
  private flicker = 0;

  constructor(car: CarParts, private mats: Materials) {
    // headlights: one beam per side, from between the two lamps
    for (const side of ['l', 'r']) {
      const a = car.byName.get(`anchor_headlamp_${side}0`);
      const b = car.byName.get(`anchor_headlamp_${side}1`);
      const pa = new THREE.Vector3(), pb = new THREE.Vector3();
      a?.getWorldPosition(pa);
      b?.getWorldPosition(pb);
      const p = pa.add(pb).multiplyScalar(0.5);
      const s = new THREE.SpotLight(0xffe6c0, 0, 40, 0.42, 0.55, 1.4);
      s.position.copy(p);
      s.target.position.copy(p).add(new THREE.Vector3(10, -0.9, side === 'l' ? -0.8 : 0.8));
      s.castShadow = false;
      this.group.add(s, s.target);
      this.heads.push(s);
    }

    // A-pillar spotlights: a tight beam that follows each lamp's orientation
    for (const side of ['l', 'r']) {
      const lamp = car.byName.get(`spotlight_${side}`);
      if (!lamp) continue;
      const s = new THREE.SpotLight(0xfff0d8, 0, 60, 0.075, 0.45, 1.25);
      s.position.set(0.04, 0, 0);
      const tgt = new THREE.Object3D();
      tgt.position.set(5, 0, 0);
      lamp.add(s, tgt);
      s.target = tgt;
      this.spots.push(s);
      this.spotPivots.push(lamp);
    }

    // soft fill over the open trunk (the cabin itself is lit by sky fill only)
    this.cabin = new THREE.PointLight(0xd8d2c6, 0, 4.2, 1.3);
    this.cabin.position.copy(Lights.TRUNK);
    car.root.add(this.cabin);
  }

  setHeadlights(on: boolean) { this.headTarget = on ? 1 : 0; }
  setSpotlights(on: boolean) { this.spotTarget = on ? 1 : 0; }
  get spotlightsOn() { return this.spotTarget > 0.5; }

  update(dt: number, t: number) {
    // lamps warm up rather than snap on (filaments + a flicker on ignition)
    const k = Math.min(1, dt * 3.2);
    this.headOn += (this.headTarget - this.headOn) * k;
    this.spotOn += (this.spotTarget - this.spotOn) * Math.min(1, dt * 4);
    this.flicker = this.headTarget > 0 && this.headOn < 0.9 ? (Math.sin(t * 90) > 0.2 ? 1 : 0.6) : 1;
    const h = this.headOn * this.flicker;
    const ls = this.lampScale;
    for (const s of this.heads) s.intensity = 260 * h;
    this.mats.setLamp('headlamp', 0.5 * h * ls);
    this.mats.setLamp('headlamp_bulb', 2.6 * h * ls);
    this.mats.setLamp('tail', 1.4 * h * ls);
    this.mats.setLamp('signal', 1.2 * h * ls);
    this.mats.setLamp('dial', 1.6 * h);
    this.cabin.intensity += (this.cabinTarget - this.cabin.intensity) * Math.min(1, dt * 3);
    for (const s of this.spots) s.intensity = 1400 * this.spotOn;
    this.mats.setLamp('spot_lens', 3.2 * this.spotOn * ls);
  }
}
