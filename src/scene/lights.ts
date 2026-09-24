import * as THREE from 'three';
import type { CarParts } from './car';
import type { Materials } from './materials';

/** Low-key night lighting rig plus the car's own lamps. */
export class Lights {
  readonly group = new THREE.Group();
  readonly key: THREE.SpotLight;
  readonly rim: THREE.SpotLight;
  readonly fill: THREE.SpotLight;
  readonly hemi: THREE.HemisphereLight;
  readonly heads: THREE.SpotLight[] = [];
  readonly spots: THREE.SpotLight[] = [];
  readonly spotPivots: THREE.Object3D[] = [];
  readonly dash: THREE.PointLight;
  readonly plateLamp: THREE.PointLight;
  readonly cabin: THREE.PointLight;
  cabinTarget = 0;
  headOn = 0; // 0..1 animated
  spotOn = 0;
  private headTarget = 0;
  private spotTarget = 0;
  private flicker = 0;

  constructor(car: CarParts, private mats: Materials, shadows: boolean, shadowSize: number) {
    this.hemi = new THREE.HemisphereLight(0x2a3246, 0x050506, 0.08);
    this.group.add(this.hemi);

    this.key = new THREE.SpotLight(0xc8d4ff, 48, 30, 0.62, 0.9, 1.6);
    this.key.position.set(1.2, 9.5, -3.0);
    this.key.target.position.set(0, 0.4, 0);
    this.key.castShadow = shadows;
    this.key.shadow.mapSize.set(shadowSize, shadowSize);
    this.key.shadow.bias = -0.0004;
    this.key.shadow.normalBias = 0.02;
    this.key.shadow.radius = 4;
    this.key.shadow.camera.near = 4;
    this.key.shadow.camera.far = 16;
    this.group.add(this.key, this.key.target);

    this.rim = new THREE.SpotLight(0x7f95c8, 18, 25, 0.5, 1.0, 1.6);
    this.rim.position.set(-7, 2.2, 5.5);
    this.rim.target.position.set(0, 0.7, 0);
    this.group.add(this.rim, this.rim.target);

    this.fill = new THREE.SpotLight(0xffb070, 35, 25, 0.6, 1.0, 1.8);
    this.fill.position.set(7, 2.2, -5.5);
    this.fill.target.position.set(0, 0.5, 0);
    this.group.add(this.fill, this.fill.target);

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

    // A-pillar spotlights: the light follows each lamp's orientation
    for (const side of ['l', 'r']) {
      const lamp = car.byName.get(`spotlight_${side}`);
      if (!lamp) continue;
      const s = new THREE.SpotLight(0xfff2de, 0, 45, 0.11, 0.35, 1.2);
      s.position.set(0.04, 0, 0);
      const tgt = new THREE.Object3D();
      tgt.position.set(5, 0, 0);
      lamp.add(s, tgt);
      s.target = tgt;
      this.spots.push(s);
      this.spotPivots.push(lamp);
    }

    // licence plate lamp above the rear plate
    const pl = car.byName.get('anchor_plate_rear');
    this.plateLamp = new THREE.PointLight(0xfff1d8, 0, 0.8, 2);
    if (pl) pl.getWorldPosition(this.plateLamp.position);
    this.plateLamp.position.add(new THREE.Vector3(-0.08, 0.14, 0));
    car.root.add(this.plateLamp);
    this.dash = new THREE.PointLight(0xffb060, 0, 1.1, 2);
    this.dash.position.set(0.8, 0.86, 0.12);
    car.root.add(this.dash);
    // streetlight spill through the open windows, only when we're inside
    this.cabin = new THREE.PointLight(0xd8d2c6, 0, 3.4, 1.4);
    this.cabin.position.set(-0.45, 1.3, 0.0);
    car.root.add(this.cabin);
  }

  setHeadlights(on: boolean) { this.headTarget = on ? 1 : 0; }
  setSpotlights(on: boolean) { this.spotTarget = on ? 1 : 0; }
  get spotlightsOn() { return this.spotTarget > 0.5; }

  update(dt: number, t: number) {
    // lamps warm up rather than snap on (filaments + a flicker on ignition)
    const k = Math.min(1, dt * 3.2);
    this.headOn += (this.headTarget - this.headOn) * k;
    this.spotOn += (this.spotTarget - this.spotOn) * Math.min(1, dt * 5);
    this.flicker = this.headTarget > 0 && this.headOn < 0.9 ? (Math.sin(t * 90) > 0.2 ? 1 : 0.6) : 1;
    const h = this.headOn * this.flicker;
    for (const s of this.heads) s.intensity = 260 * h;
    this.mats.setLamp('headlamp', 0.9 * h);
    this.mats.setLamp('headlamp_bulb', 2.6 * h);
    this.mats.setLamp('tail', 1.4 * h);
    this.mats.setLamp('signal', 1.2 * h);
    this.mats.setLamp('dial', 1.6 * h);
    this.dash.intensity = 0.45 * h;
    this.plateLamp.intensity = 0.5 * h;
    this.cabin.intensity += (this.cabinTarget - this.cabin.intensity) * Math.min(1, dt * 3);
    for (const s of this.spots) s.intensity = 900 * this.spotOn;
    this.mats.setLamp('spot_lens', 9 * this.spotOn);
  }
}
