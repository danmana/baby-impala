import * as THREE from 'three';
import './styles.css';
import { detectTier, qualityFor, reducedMotion, FrameGovernor, isTouch, type Tier } from './scene/quality';
import { Stage } from './scene/stage';
import { buildEnvironment } from './scene/env';
import { Materials } from './scene/materials';
import { loadCar, type CarParts } from './scene/car';
import { Ground } from './scene/ground';
import { PlanarReflection } from './scene/reflection';
import { Lights } from './scene/lights';
import { Motel } from './scene/motel';
import { Atmosphere, addDroplets, type Beam } from './scene/atmosphere';
import { Director, type ViewName } from './scene/director';
import { Exploder } from './scene/explode';
import { TrunkRig } from './scene/trunkview';
import { AudioEngine } from './audio/audio';
import { MusicPlayer } from './audio/music';
import { Loader } from './ui/loader';
import { Hud, type ToggleKey } from './ui/hud';
import { LorePanel } from './ui/lore';
import { Deck } from './ui/deck';
import { Overlay } from './ui/overlay';
import { CAR, HOTSPOTS, TRAP, TRUNK_ITEMS, type Hotspot, type HotspotView } from './content/lore';

const reduced = reducedMotion();
const ui = document.getElementById('ui')!;
const audio = new AudioEngine();
const music = new MusicPlayer(audio);
let started = false;
let startFn: () => void = () => undefined;
const loader = new Loader(ui, () => startFn());

async function main() {
  let tier: Tier = detectTier();
  let quality = qualityFor(tier);
  const stage = new Stage(document.getElementById('stage')!, quality);
  const { renderer, scene, camera } = stage;

  const envPlain = buildEnvironment(renderer, false);
  let envMotel: THREE.Texture | null = null;
  const mats = new Materials(envPlain);
  loader.progress(0.05);
  const car: CarParts = await loadCar(`${import.meta.env.BASE_URL}models/baby.glb`, mats, (f) => loader.progress(0.05 + f * 0.8));
  scene.add(car.root);

  const refl = new PlanarReflection(quality.reflectionScale);
  const ground = new Ground(refl);
  scene.add(ground.mesh);
  const lights = new Lights(car, mats, quality.shadows, quality.shadowMapSize);
  scene.add(lights.group);
  const motel = new Motel(envPlain);
  motel.reduced = reduced;
  scene.add(motel.group);
  const atmo = new Atmosphere({ particles: reduced ? quality.particles * 0.4 : quality.particles, volumetrics: quality.volumetrics });
  scene.add(atmo.group);
  const exploder = new Exploder(car);
  exploder.reduced = reduced;
  scene.add(exploder.lines);
  const trunk = new TrunkRig(car);
  trunk.reduced = reduced;
  trunk.onCreak = () => audio.creak(reduced ? 0.5 : 1.1);
  const director = new Director(camera, renderer.domElement);
  director.reduced = reduced;

  // rain beads on the glass
  const glass = mats.m.get('__glass') as THREE.MeshPhysicalMaterial | undefined;
  const rainU = { value: 0 };
  const timeU = { value: 0 };
  if (glass) addDroplets(glass, rainU, timeU);

  // ---------------------------------------------------------------- beams for the fog, dust and rain
  const headBeams: Beam[] = lights.heads.map((s) => ({
    origin: s.position.clone(),
    dir: s.target.position.clone().sub(s.position).normalize(),
    cos: Math.cos(0.36), range: 14, intensity: 0, color: new THREE.Color(1.0, 0.86, 0.66),
  }));
  headBeams.forEach((b) => {
    const holder = new THREE.Object3D();
    holder.position.copy(b.origin);
    holder.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), b.dir);
    scene.add(holder);
    atmo.addBeam(b, holder, 12, 1.9, quality.volumetrics);
  });
  const spotBeams: Beam[] = lights.spotPivots.map((p) => {
    const b: Beam = { origin: new THREE.Vector3(), dir: new THREE.Vector3(1, 0, 0), cos: Math.cos(0.1), range: 30, intensity: 0, color: new THREE.Color(1, 0.95, 0.85) };
    atmo.addBeam(b, p, 18, 1.2, quality.volumetrics);
    return b;
  });

  // ---------------------------------------------------------------- UI
  const lore = new LorePanel(ui);
  const deck = new Deck(ui, music);
  const trapSpot: Hotspot = { id: 'trap', label: 'Devil’s Trap', pos: [-2.2, 1.6, 0], view: 'trunk', lore: TRAP };
  const overlay = new Overlay(ui, [...HOTSPOTS, trapSpot], (s) => openHotspot(s), () => [car.root]);
  overlay.setExplodedLabels(exploder.labels);
  const trapMarkerPos = overlay.positionOf('trap')!;

  const hud = new Hud(ui, {
    view: (v) => setView(v),
    toggle: (k, on) => toggle(k, on),
    flipPlates: () => flipPlates(),
    reset: () => director.reset(),
    volume: (v) => audio.setVolume(v),
    mute: (m) => audio.setMuted(m),
    title: () => lore.show(CAR),
  });
  hud.setToggle('sigils', true);

  const state: Record<ToggleKey, boolean> = { engine: false, spotlights: false, rain: false, motel: false, sigils: true };

  function openHotspot(s: Hotspot) {
    const actions: { label: string; run: () => void }[] = [];
    if (s.id === 'plates') actions.push({ label: 'Swap plates', run: flipPlates });
    if (s.id === 'spotlights') {
      actions.push({
        label: state.spotlights ? 'Spotlights off' : 'Spotlights on',
        run: () => {
          toggle('spotlights', !state.spotlights);
          hud.setToggle('spotlights', state.spotlights);
          lore.close();
        },
      });
    }
    if (s.id === 'trunk') actions.push({ label: 'Open the trunk', run: () => setView('trunk') });
    if (s.id === 'tape_deck') actions.push({ label: 'Switch tapes', run: () => music.switchTape() });
    if (s.id === 'engine') actions.push({ label: 'Pull it apart', run: () => setView('exploded') });
    lore.show(s.lore, actions);
  }

  function flipPlates() {
    car.plateFront.toggle(reduced);
    car.plateRear.toggle(reduced);
  }

  function overlayViewFor(v: ViewName): HotspotView | null {
    if (v === 'interior') return 'interior';
    if (v === 'trunk') return 'trunk';
    if (v === 'normal') return 'exterior';
    return null;
  }

  function setView(v: ViewName) {
    if (director.inIntro) return;
    lore.close();
    overlay.showTag(null);
    const from = director.view;
    hud.setView(v);
    if (from === 'trunk' && v !== 'trunk') trunk.open(false);
    lights.cabinTarget = v === 'interior' ? 3.2 : 0;
    if (from === 'exploded' && v !== 'exploded') exploder.set(false);
    hud.note(null);
    overlay.view = null;
    director.go(v, () => {
      overlay.view = overlayViewFor(v);
      if (v === 'trunk') {
        trunk.open(true);
        hud.note(isTouch() ? 'Tap the gear to read up on it.' : 'Hover over the gear. Click to read up on it.');
      }
      if (v === 'interior') hud.note('Look for what the boys left behind.');
    });
    if (v === 'exploded') exploder.set(true);
  }

  function toggle(k: ToggleKey, on: boolean) {
    state[k] = on;
    if (k === 'engine') {
      if (on) {
        audio.unlock();
        audio.startEngine(reduced);
        setTimeout(() => lights.setHeadlights(state.engine), reduced ? 300 : 1100);
      } else {
        audio.stopEngine();
        lights.setHeadlights(false);
      }
      deck.setLit(on);
    }
    if (k === 'spotlights') lights.setSpotlights(on);
    if (k === 'rain') atmo.setRain(on);
    if (k === 'motel') {
      motel.setOn(on);
      if (on && !envMotel) envMotel = buildEnvironment(renderer, true);
      mats.setEnv(on ? envMotel! : envPlain);
      director.wallZ = on ? motel.wallZ : null;
    }
    if (k === 'sigils') overlay.enabled = on;
  }

  // ---------------------------------------------------------------- picking
  const ray = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  const pickSet = new Set<THREE.Object3D>();
  car.root.traverse((o) => {
    if ((o as THREE.Mesh).isMesh && (o.userData.hotspot || o.userData.item || o.name.startsWith('trunk_lid_inner'))) pickSet.add(o);
  });
  const isTrap = (o: THREE.Object3D) => o.name.startsWith('trunk_lid_inner');
  function pick(x: number, y: number): THREE.Object3D | null {
    ndc.set((x / window.innerWidth) * 2 - 1, -(y / window.innerHeight) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const hits = ray.intersectObject(car.root, true);
    for (const h of hits) {
      const m = (h.object as THREE.Mesh).material as THREE.Material;
      if (m.transparent) continue;
      return pickSet.has(h.object) ? h.object : null;
    }
    return null;
  }
  let down: { x: number; y: number } | null = null;
  let hoverTick = 0;
  renderer.domElement.addEventListener('pointerdown', (e) => {
    down = { x: e.clientX, y: e.clientY };
    hud.hideHint();
  });
  renderer.domElement.addEventListener('pointerup', (e) => {
    if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 6) return;
    down = null;
    const o = pick(e.clientX, e.clientY);
    if (!o) return;
    if (o.userData.hotspot === 'plates') flipPlates();
    else if (o.userData.item && director.view === 'trunk') {
      const it = TRUNK_ITEMS[o.userData.item];
      if (it) lore.show(it.lore);
    } else if (isTrap(o) && director.view === 'trunk') lore.show(TRAP);
  });
  renderer.domElement.addEventListener('pointermove', (e) => {
    if (e.pointerType === 'touch' || !started) return;
    if (++hoverTick % 2) return;
    const o = pick(e.clientX, e.clientY);
    let label: string | null = null;
    if (o?.userData.item && director.view === 'trunk' && trunk.progress > 0.6) label = TRUNK_ITEMS[o.userData.item]?.name ?? null;
    else if (o && isTrap(o) && director.view === 'trunk') label = 'Devil’s Trap';
    else if (o?.userData.hotspot === 'plates') label = car.plateFront.ohio ? 'CNK 80Q3, Ohio' : 'KAZ 2Y5, Kansas';
    overlay.showTag(label, e.clientX, e.clientY);
    renderer.domElement.style.cursor = label ? 'pointer' : 'grab';
  });
  window.addEventListener('keydown', (e) => {
    if (!started || e.target instanceof HTMLInputElement) return;
    const views: ViewName[] = ['normal', 'exploded', 'trunk', 'interior'];
    const n = Number(e.key);
    if (n >= 1 && n <= 4) setView(views[n - 1]);
  });
  director.onInteract = () => hud.hideHint();

  // ---------------------------------------------------------------- resize, quality
  const resize = () => {
    const size = renderer.getDrawingBufferSize(new THREE.Vector2());
    refl.setSize(size.x, size.y);
  };
  resize();
  window.addEventListener('resize', resize);
  console.info(`[baby] quality tier: ${tier}`);
  const governor = new FrameGovernor(isTouch() ? 34 : 17.5, () => {
    if (tier === 'low') return false;
    tier = tier === 'high' ? 'medium' : 'low';
    quality = qualityFor(tier);
    stage.setQuality(quality);
    refl.scale = quality.reflectionScale;
    resize();
    lights.key.castShadow = quality.shadows;
    console.info(`[baby] quality → ${tier}`);
    return true;
  });

  // ---------------------------------------------------------------- loop
  const timer = new THREE.Timer();
  let t = 0;
  const tmpQ = new THREE.Quaternion();
  const reflHide: THREE.Object3D[] = [atmo.group, exploder.lines];
  const lidInner = car.byName.get('trunk_lid_inner');
  const box = new THREE.Box3();
  const frame = () => {
    timer.update();
    const dt = Math.min(timer.getDelta(), 0.1);
    t += dt;
    director.update(dt);
    lights.update(dt, t);
    // spotlights sweep the dark
    lights.spotPivots.forEach((p, i) => {
      const side = i === 0 ? -1 : 1;
      const sweep = reduced ? 0.2 : 0.2 + Math.sin(t * 0.35 + i * 1.7) * 0.45;
      p.rotation.set(0, side * sweep, -0.06 + (reduced ? 0 : Math.sin(t * 0.23 + i) * 0.05));
    });
    headBeams.forEach((b) => (b.intensity = lights.headOn * 0.9));
    spotBeams.forEach((b, i) => {
      const p = lights.spotPivots[i];
      p.getWorldPosition(b.origin);
      p.getWorldQuaternion(tmpQ);
      b.dir.set(1, 0, 0).applyQuaternion(tmpQ);
      b.intensity = lights.spotOn * 1.2;
    });
    // the exploded view gets brighter, workshop light and a grid on the floor
    const xk = exploder.progress;
    lights.key.intensity = 48 + 70 * xk;
    lights.hemi.intensity = 0.08 + 0.22 * xk;
    ground.uniforms.uGrid.value = xk;
    motel.update(dt, t);
    atmo.update(dt, t);
    exploder.update(dt);
    trunk.update(dt);
    car.plateFront.update(dt);
    car.plateRear.update(dt);
    rainU.value = atmo.rainLevel;
    timeU.value = t;
    ground.uniforms.uRain.value = atmo.rainLevel;
    if (lidInner && director.view === 'trunk') {
      box.setFromObject(lidInner);
      box.getCenter(trapMarkerPos);
      trapMarkerPos.x -= 0.1;
    }
    ground.update(renderer, scene, camera, reflHide, t);
    stage.render(t);
    overlay.update(camera, exploder.labels);
    if (started) governor.tick(dt);
  };

  // warm up shaders before the engine can be started
  loader.progress(0.9);
  try {
    await renderer.compileAsync(scene, camera);
  } catch {
    /* compileAsync is best-effort */
  }
  renderer.setAnimationLoop(frame);
  loader.ready();

  startFn = () => {
    if (started) return;
    started = true;
    audio.unlock();
    loader.hide();
    toggle('engine', true);
    hud.setToggle('engine', true);
    setTimeout(() => void music.play(), reduced ? 400 : 2600);
    director.playIntro(() => {
      hud.show();
      hud.showHint();
      overlay.view = 'exterior';
    });
  };

  // test hooks: ?autostart skips the start button, ?nointro skips the reveal
  const params = new URLSearchParams(location.search);
  if (params.has('nointro')) director.reduced = true;
  if (params.has('autostart')) {
    startFn();
    if (params.has('nointro')) setTimeout(() => (director.reduced = reduced), 500);
  }

  (window as unknown as Record<string, unknown>).__baby = {
    stage, car, lights, camera, director, mats, ground, motel, atmo, exploder, trunk, overlay, setView, toggle, music, THREE,
  };
}

main().catch((err) => {
  console.error(err);
  loader.fail('Baby wouldn’t start. Reload the page to try again.');
});
