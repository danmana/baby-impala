import * as THREE from 'three';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';
import './styles.css';
import { detectTier, qualityFor, reducedMotion, FrameGovernor, isTouch, type Tier } from './scene/quality';
import { Stage } from './scene/stage';
import { Materials } from './scene/materials';
import { loadCar, type CarParts } from './scene/car';
import { Ground } from './scene/ground';
import { PlanarReflection } from './scene/reflection';
import { Lights } from './scene/lights';
import { Motel, type MotelMaps } from './scene/motel';
import { Atmosphere, addDroplets, type Beam } from './scene/atmosphere';
import { Director, type ViewName } from './scene/director';
import { Exploder } from './scene/explode';
import { TrunkRig } from './scene/trunkview';
import { LightingRig, PRESETS, buildEnv, type PresetName } from './scene/lighting';
import { Sigils } from './scene/sigils';
import { AudioEngine } from './audio/audio';
import { MusicPlayer } from './audio/music';
import { Loader } from './ui/loader';
import { Hud, type ToggleKey } from './ui/hud';
import { LorePanel } from './ui/lore';
import { Deck } from './ui/deck';
import { Overlay } from './ui/overlay';
import { CAR, HOTSPOTS, TRAP, TRUNK_ITEMS, type Hotspot, type HotspotView } from './content/lore';
import { Progress } from './boot/progress';
import { fetchBytes, expectedBytes } from './boot/assets';

const reduced = reducedMotion();
const ui = document.getElementById('ui')!;
const audio = new AudioEngine();
const music = new MusicPlayer(audio);
let started = false;
let startFn: () => void = () => undefined;

const progress = new Progress([
  { id: 'ui', label: 'Salting the doorways', weight: 6 },
  { id: 'car', label: 'Loading the rock salt', weight: 30 },
  { id: 'env', label: 'Waxing the chrome', weight: 20 },
  { id: 'scene', label: 'Checking the Devil’s Trap', weight: 22 },
  { id: 'sfx', label: 'Rewinding the tapes', weight: 6 },
  { id: 'warm', label: 'Warming up the engine', weight: 16 },
]);
const loader = new Loader(ui, progress, () => startFn());

const UI_TEX = ['ui/paper_page.webp', 'ui/paper_manila.webp', 'ui/paper_stains.webp', 'ui/tape.webp'];
const GROUND_TEX = { diff: 'textures/asphalt_diff.webp', nor: 'textures/asphalt_nor.webp', arm: 'textures/asphalt_arm.webp' };
const MOTEL_SETS = ['wall', 'walk', 'door', 'metal', 'roof'] as const;

// never leave the journal page invisible on a slow connection
setTimeout(() => document.documentElement.classList.add('tex-ready'), 2500);

const nextFrame = () => new Promise<void>((r) => requestAnimationFrame(() => r()));

/** Fetch UI textures into blob URLs and hand them to CSS, plus the web fonts. */
async function bootUi() {
  const track = progress.bytes('ui');
  await Promise.all([
    ...UI_TEX.map(async (p) => {
      const buf = await fetchBytes(p, track(p, expectedBytes(p)));
      const url = URL.createObjectURL(new Blob([buf], { type: 'image/webp' }));
      const name = p.split('/').pop()!.replace('.webp', '').replace('_', '-');
      document.documentElement.style.setProperty(`--tex-${name}`, `url("${url}")`);
    }),
    document.fonts.load('40px "League Gothic"'),
    document.fonts.load('16px "Special Elite"'),
    document.fonts.load('24px "Reenie Beanie"'),
  ]).catch(() => undefined);
  document.documentElement.classList.add('tex-ready');
  progress.done('ui');
}

async function loadTexture(path: string, track: ReturnType<Progress['bytes']>) {
  const buf = await fetchBytes(path, track(path, expectedBytes(path)));
  const url = URL.createObjectURL(new Blob([buf], { type: 'image/webp' }));
  const t = await new THREE.TextureLoader().loadAsync(url);
  URL.revokeObjectURL(url);
  return t;
}

async function main() {
  let tier: Tier = detectTier();
  let quality = qualityFor(tier);
  const stage = new Stage(document.getElementById('stage')!, quality);
  const { renderer, scene, camera } = stage;
  const maxAniso = renderer.capabilities.getMaxAnisotropy();

  // ---------------------------------------------------------------- downloads, all in parallel
  const uiDone = bootUi();
  const carTrack = progress.bytes('car');
  const carBytes = fetchBytes('models/baby.glb', carTrack('models/baby.glb', expectedBytes('models/baby.glb')));
  const envTrack = progress.bytes('env');
  const hdrBytes = (Object.keys(PRESETS) as PresetName[]).map(async (name) => {
    const path = PRESETS[name].hdri;
    const buf = await fetchBytes(path, envTrack(path, expectedBytes(path)));
    return [name, buf] as const;
  });
  const sceneTrack = progress.bytes('scene');
  const groundTex = Promise.all([loadTexture(GROUND_TEX.diff, sceneTrack), loadTexture(GROUND_TEX.nor, sceneTrack), loadTexture(GROUND_TEX.arm, sceneTrack)]);
  const motelTex = Promise.all(MOTEL_SETS.map(async (k) => {
    const [diff, nor, arm] = await Promise.all(['diff', 'nor', 'arm'].map((m) => loadTexture(`textures/motel_${k}_${m}.webp`, sceneTrack)));
    return [k, { diff, nor, arm }] as const;
  }));
  const sounds = audio.preload(progress.bytes('sfx'));

  // ---------------------------------------------------------------- the car
  const mats = new Materials();
  const car: CarParts = await loadCar(await carBytes, mats);
  scene.add(car.root);
  progress.done('car');

  // ---------------------------------------------------------------- lighting presets and their environments
  const rig = new LightingRig(scene, renderer, quality.shadows, quality.shadowMapSize);
  scene.add(rig.group);
  const hdrLoader = new HDRLoader();
  const envs = {} as Record<PresetName, [THREE.Texture, THREE.Texture]>;
  const devHdr = {} as Record<PresetName, THREE.Texture>;
  for (const entry of hdrBytes) {
    const [name, buf] = await entry;
    const url = URL.createObjectURL(new Blob([buf]));
    const hdr = await hdrLoader.loadAsync(url);
    URL.revokeObjectURL(url);
    envs[name] = [buildEnv(renderer, hdr, PRESETS[name], { motel: false }), buildEnv(renderer, hdr, PRESETS[name], { motel: true })];
    if (import.meta.env.DEV) devHdr[name] = hdr;
    else hdr.dispose();
    progress.set('env', 0.85 + 0.05 * Object.keys(envs).length);
    await nextFrame();
  }
  scene.environment = envs.moon[0];
  progress.done('env');

  // ---------------------------------------------------------------- the rest of the scene
  const [gd, gn, ga] = await groundTex;
  const refl = new PlanarReflection(quality.reflectionScale);
  const ground = new Ground(refl, { diff: gd, nor: gn, arm: ga }, Math.min(8, maxAniso));
  ground.bakePuddles(renderer);
  scene.add(ground.mesh);
  const lights = new Lights(car, mats);
  scene.add(lights.group);
  const motelMaps = Object.fromEntries(await motelTex) as unknown as MotelMaps;
  const motel = new Motel(motelMaps);
  motel.reduced = reduced;
  scene.add(motel.group, motel.lights);
  const atmo = new Atmosphere({ particles: reduced ? quality.particles * 0.4 : quality.particles, volumetrics: quality.volumetrics, tier: quality.tier });
  scene.add(atmo.group);
  const exploder = new Exploder(car);
  exploder.reduced = reduced;
  scene.add(exploder.lines);
  const trunk = new TrunkRig(car);
  trunk.reduced = reduced;
  trunk.onOpen = () => audio.trunkOpen();
  trunk.onClose = () => audio.trunkClose();
  const director = new Director(camera, renderer.domElement);
  director.reduced = reduced;
  const trapSpot: Hotspot = { id: 'trap', label: 'Devil’s Trap', pos: [-2.2, 1.6, 0], view: 'trunk', lore: TRAP };
  const sigils = new Sigils([...HOTSPOTS, trapSpot]);
  sigils.reduced = reduced;
  scene.add(sigils.group);

  // hidden-away parts: the trunk arsenal, the engine and the cabin. They never
  // cast a useful shadow (the body shell already does) and can't be seen in the
  // puddles, and the arsenal is only drawn while the trunk is open
  const HIDDEN_AWAY = /^item_|^false_floor|^engine|^transmission|^radiator|_Indoor|^seat|^dash|^steer|^tape_deck|^ashtray|^army|^lego|^defroster|^initials|^drum/;
  const hiddenAway: THREE.Object3D[] = [];
  car.root.traverse((o) => {
    if ((o as THREE.Mesh).isMesh && HIDDEN_AWAY.test(o.name)) {
      o.castShadow = false;
      hiddenAway.push(o);
    }
  });
  const ARSENAL = /^item_|^false_floor/;
  const arsenal: THREE.Object3D[] = [];
  car.root.traverse((o) => {
    if (ARSENAL.test(o.name) && !(o.parent && ARSENAL.test(o.parent.name))) arsenal.push(o);
  });
  let arsenalShown = true;
  const showArsenal = (on: boolean) => {
    if (on === arsenalShown) return;
    arsenalShown = on;
    arsenal.forEach((o) => (o.visible = on));
  };

  // the sweeping spotlight housings are too small to matter in the shadow map,
  // and keeping them out lets it be rendered only when something big moves
  lights.spotPivots.forEach((p) => p.traverse((o) => (o.castShadow = false)));
  renderer.shadowMap.autoUpdate = false;
  renderer.shadowMap.needsUpdate = true;
  let shadowHold = 1.5;
  const markShadows = (seconds = 1.5) => (shadowHold = Math.max(shadowHold, seconds));

  // rain beads on the glass
  const glass = mats.m.get('__glass') as THREE.MeshPhysicalMaterial | undefined;
  const rainU = { value: 0 };
  const timeU = { value: 0 };
  if (glass) addDroplets(glass, rainU, timeU);

  // light shafts for the headlights and the pillar spotlights
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
    atmo.addBeam(b, holder, 12, quality.volumetrics, 0.35);
  });
  const spotBeams: Beam[] = lights.spotPivots.map((p) => {
    const b: Beam = { origin: new THREE.Vector3(), dir: new THREE.Vector3(1, 0, 0), cos: Math.cos(0.075), range: 30, intensity: 0, color: new THREE.Color(1, 0.95, 0.86) };
    atmo.addBeam(b, p, 22, quality.volumetrics, 0.6);
    return b;
  });
  progress.done('scene');

  // ---------------------------------------------------------------- warm-up: upload textures, compile every shader
  await sounds.catch((e) => console.warn('[baby] sounds', e));
  progress.done('sfx');
  camera.position.set(5.35, 1.02, -4.35);
  camera.lookAt(0.25, 0.62, 0);
  const textures = new Set<THREE.Texture>();
  scene.traverse((o) => {
    const m = (o as THREE.Mesh).material as THREE.Material | THREE.Material[] | undefined;
    if (!m) return;
    for (const mat of Array.isArray(m) ? m : [m]) {
      for (const v of Object.values(mat)) if (v instanceof THREE.Texture) textures.add(v);
    }
  });
  // upload a few textures per frame so the page never freezes mid-bar
  const texList = [...textures];
  for (let i = 0; i < texList.length; i++) {
    renderer.initTexture(texList[i]);
    if (i % 3 === 2) {
      progress.set('warm', 0.15 * ((i + 1) / texList.length));
      await nextFrame();
    }
  }
  progress.set('warm', 0.15);
  // hidden-by-default things must be visible while compiling so the first toggle doesn't stall
  const hidden: THREE.Object3D[] = [];
  scene.traverse((o) => {
    if (!o.visible) {
      hidden.push(o);
      o.visible = true;
    }
  });
  const groups: THREE.Object3D[] = [car.root, ground.mesh, motel.group, atmo.group, sigils.group, exploder.lines, scene];
  for (let i = 0; i < groups.length; i++) {
    try {
      await renderer.compileAsync(groups[i], camera, scene);
    } catch {
      /* best effort */
    }
    progress.set('warm', 0.15 + 0.8 * ((i + 1) / groups.length));
    await nextFrame();
  }
  hidden.forEach((o) => (o.visible = false));
  await uiDone;
  progress.done('warm');

  // ---------------------------------------------------------------- UI
  const lore = new LorePanel(ui);
  const deck = new Deck(ui, music, (n) => audio.play(n, { gain: 0.9 }));
  const overlay = new Overlay(ui, [...HOTSPOTS, trapSpot], (s) => openHotspot(s), () => [car.root], (id) => sigils.positionOf(id));
  overlay.onHover = (id) => (sigils.hovered = id);
  overlay.setExplodedLabels(exploder.labels);
  const trapMarkerPos = sigils.positionOf('trap')!;

  const state: Record<ToggleKey, boolean> = { engine: false, spotlights: false, rain: false, motel: false, sigils: true };
  const hud = new Hud(ui, {
    view: (v) => setView(v),
    toggle: (k, on) => toggle(k, on),
    flipPlates: () => flipPlates(),
    reset: () => director.reset(),
    volume: (v) => audio.setVolume(v),
    mute: (m) => audio.setMuted(m),
    title: () => lore.show(CAR),
    light: (p) => setLight(p),
  });
  hud.setToggle('sigils', true);

  rig.onEnvSwap = (name) => {
    scene.environment = envs[name][state.motel ? 1 : 0];
  };
  function setLight(p: PresetName) {
    rig.set(p, reduced);
    hud.setLight(p);
  }

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
    markShadows();
    car.plateFront.toggle(reduced);
    car.plateRear.toggle(reduced);
  }

  function overlayViewFor(v: ViewName): HotspotView | null {
    if (v === 'interior') return 'interior';
    if (v === 'trunk') return 'trunk';
    if (v === 'normal') return 'exterior';
    return null;
  }

  function setViewMarkers(v: HotspotView | null) {
    overlay.view = v;
    sigils.view = v;
  }

  function setView(v: ViewName) {
    if (director.inIntro) return;
    lore.close();
    overlay.showTag(null);
    const from = director.view;
    hud.setView(v);
    if (from === 'trunk' && v !== 'trunk') trunk.open(false);
    // inside the cabin a point light turns every bit of trim and the mirror into
    // a flare, so the cabin gets sky fill instead; the point light is the trunk lamp
    lights.cabinTarget = v === 'trunk' ? 1.6 : 0;
    lights.cabin.position.copy(Lights.TRUNK);
    rig.cabinTarget = v === 'interior' ? 1 : 0;
    if (from === 'exploded' && v !== 'exploded') exploder.set(false);
    hud.note(null);
    setViewMarkers(null);
    director.go(v, () => {
      setViewMarkers(overlayViewFor(v));
      if (v === 'trunk') {
        trunk.open(true);
        hud.note(isTouch() ? 'Tap the gear to read up on it.' : 'Hover over the gear. Click to read up on it.');
      }
      if (v === 'interior') hud.note('Drag to look around. Look for what the boys left behind.');
    });
    if (v === 'exploded') exploder.set(true);
  }

  function toggle(k: ToggleKey, on: boolean) {
    state[k] = on;
    if (k === 'engine') {
      if (on) {
        audio.unlock();
        audio.startEngine();
        setTimeout(() => lights.setHeadlights(state.engine), reduced ? 300 : 900);
      } else {
        audio.stopEngine();
        lights.setHeadlights(false);
      }
      deck.setLit(on);
    }
    if (k === 'spotlights') lights.setSpotlights(on);
    if (k === 'rain') atmo.setRain(on);
    if (k === 'motel') {
      markShadows(2.5);
      motel.setOn(on);
      scene.environment = envs[rig.current][on ? 1 : 0];
      director.wallZ = on ? motel.wallZ : null;
    }
    if (k === 'sigils') {
      overlay.enabled = on;
      sigils.enabled = on;
    }
  }

  // ---------------------------------------------------------------- picking (trunk gear, plates, the trap)
  const ray = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  const pickSet = new Set<THREE.Object3D>();
  car.root.traverse((o) => {
    if ((o as THREE.Mesh).isMesh && (o.userData.hotspot || o.userData.item || o.name.startsWith('trunk_lid_inner'))) pickSet.add(o);
  });
  const isTrap = (o: THREE.Object3D) => o.name.startsWith('trunk_lid_inner') || o.parent?.name.startsWith('trunk_lid_inner');
  function pick(x: number, y: number): THREE.Object3D | null {
    const r = renderer.domElement.getBoundingClientRect();
    ndc.set(((x - r.left) / r.width) * 2 - 1, -((y - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const hits = ray.intersectObject(car.root, true);
    for (const h of hits) {
      const m = (h.object as THREE.Mesh).material as THREE.Material;
      if (m.transparent && !pickSet.has(h.object)) continue;
      return pickSet.has(h.object) ? h.object : null;
    }
    return null;
  }
  const itemOf = (o: THREE.Object3D | null) => (o?.userData.item as string | undefined) ?? null;
  let down: { x: number; y: number } | null = null;
  let hoverTick = 0;
  const canvas = renderer.domElement;
  canvas.addEventListener('pointerdown', (e) => {
    down = { x: e.clientX, y: e.clientY };
    hud.hideHint();
  });
  canvas.addEventListener('pointerup', (e) => {
    if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 8) return;
    down = null;
    const o = pick(e.clientX, e.clientY);
    if (!o) return;
    const item = itemOf(o);
    if (o.userData.hotspot === 'plates') flipPlates();
    else if (item && director.view === 'trunk') {
      const it = TRUNK_ITEMS[item];
      if (it) lore.show(it.lore);
    } else if (isTrap(o) && director.view === 'trunk') lore.show(TRAP);
  });
  canvas.addEventListener('pointermove', (e) => {
    if (e.pointerType === 'touch' || !started || e.buttons) return;
    if (++hoverTick % 2) return;
    const o = pick(e.clientX, e.clientY);
    const item = itemOf(o);
    let label: string | null = null;
    if (item && director.view === 'trunk' && trunk.progress > 0.5) label = TRUNK_ITEMS[item]?.name ?? null;
    else if (o && isTrap(o) && director.view === 'trunk') label = 'Devil’s Trap';
    else if (o?.userData.hotspot === 'plates') label = car.plateFront.ohio ? 'CNK 80Q3, Ohio' : 'KAZ 2Y5, Kansas';
    overlay.showTag(label, e.clientX, e.clientY);
    canvas.style.cursor = label ? 'pointer' : 'grab';
  });
  canvas.addEventListener('pointerleave', () => overlay.showTag(null));
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
  // step quality down only when it's really struggling (under ~30 fps on a
  // desktop, ~20 on a phone): full quality at 40 fps beats low quality at 60
  const governor = new FrameGovernor(isTouch() ? 40 : 26, () => {
    if (tier === 'low') return false;
    tier = tier === 'high' ? 'medium' : 'low';
    quality = qualityFor(tier);
    stage.setQuality(quality);
    refl.scale = quality.reflectionScale;
    resize();
    rig.sun.castShadow = quality.shadows;
    markShadows();
    console.info(`[baby] quality → ${tier}`);
    return true;
  });

  // ---------------------------------------------------------------- loop
  const timer = new THREE.Timer();
  let t = 0;
  const tmpQ = new THREE.Quaternion();
  const spotSide = lights.spotPivots.map((p) => (p.getWorldPosition(new THREE.Vector3()).z < 0 ? 1 : -1));
  const reflHide: THREE.Object3D[] = [...atmo.reflectionHidden, exploder.lines, sigils.group, ...hiddenAway];
  const lidInner = car.byName.get('trunk_lid_inner');
  let lastX = -1;
  let lastT = -1;
  const box = new THREE.Box3();
  const frame = () => {
    timer.update();
    const dt = Math.min(timer.getDelta(), 0.1);
    t += dt;
    director.update(dt);
    rig.workshop = exploder.progress;
    rig.update(dt);
    const live = rig.live;
    lights.lampScale = live.lamps;
    lights.update(dt, t);
    if (stage.bloom) stage.bloom.strength = live.bloom;
    // spotlights sweep the dark
    lights.spotPivots.forEach((p, i) => {
      // +yaw turns the beam towards -Z, i.e. outward for the lamp on the -Z side
      const side = spotSide[i];
      // sweep outward and stay level-ish: from the A-pillar a downward beam lands on the hood
      const sweep = reduced ? 0.15 : 0.15 + Math.sin(t * 0.35 + i * 1.7) * 0.25;
      p.rotation.set(0, side * sweep, 0.035 + (reduced ? 0 : Math.sin(t * 0.23 + i) * 0.025));
    });
    headBeams.forEach((b) => (b.intensity = lights.headOn * 0.9));
    spotBeams.forEach((b, i) => {
      const p = lights.spotPivots[i];
      p.getWorldPosition(b.origin);
      p.getWorldQuaternion(tmpQ);
      b.dir.set(1, 0, 0).applyQuaternion(tmpQ);
      b.intensity = lights.spotOn * 0.85;
    });
    ground.uniforms.uGrid.value = exploder.progress;
    motel.update(dt, t, live.haze);
    atmo.update(dt, t, live.haze, live.fogColor);
    exploder.update(dt);
    trunk.update(dt);
    showArsenal(trunk.progress > 0.001 || exploder.progress > 0.001 || director.view === 'trunk');
    // the trunk fill comes up as the lid opens, not before
    if (director.view === 'trunk') lights.cabinTarget = 1.6 * THREE.MathUtils.clamp((trunk.progress - 0.25) / 0.5, 0, 1);
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
    sigils.update(dt, t, camera);
    // redraw the sun's shadow map only while something that casts it moves
    if (rig.blending || shadowHold > 0 || Math.abs(exploder.progress - lastX) > 1e-5 || Math.abs(trunk.progress - lastT) > 1e-5) {
      renderer.shadowMap.needsUpdate = true;
    }
    lastX = exploder.progress;
    lastT = trunk.progress;
    shadowHold -= dt;
    ground.update(renderer, scene, camera, reflHide, t, live.background);
    stage.render(t);
    overlay.update(camera, exploder.labels);
    if (started) governor.tick(dt);
  };
  renderer.setAnimationLoop(frame);

  startFn = () => {
    if (started) return;
    started = true;
    audio.unlock();
    loader.hide();
    toggle('engine', true);
    hud.setToggle('engine', true);
    setTimeout(() => void music.play(), reduced ? 400 : 2400);
    director.playIntro(() => {
      hud.show();
      hud.showHint();
      setViewMarkers('exterior');
    });
  };

  // test hooks: ?autostart skips the start button, ?nointro skips the reveal, ?light=sunset|day
  const params = new URLSearchParams(location.search);
  const light = params.get('light');
  if (light === 'sunset' || light === 'day' || light === 'moon') setLight(light);
  if (params.has('nointro')) director.reduced = true;
  if (params.has('autostart')) {
    const go = () => {
      if (loader.ready) {
        startFn();
        if (params.has('nointro')) setTimeout(() => (director.reduced = reduced), 500);
      } else setTimeout(go, 100);
    };
    go();
  }

  (window as unknown as Record<string, unknown>).__baby = {
    stage, car, lights, camera, director, mats, ground, motel, atmo, exploder, trunk, overlay, sigils, rig, envs,
    setView, toggle, setLight, music, audio, THREE, PRESETS,
    /** dev only: patch a preset and rebuild its environment maps live */
    tuneEnv: (name: PresetName, patch: Partial<(typeof PRESETS)['moon']>) => {
      Object.assign(PRESETS[name], patch);
      const hdr = devHdr[name];
      if (hdr) envs[name] = [buildEnv(renderer, hdr, PRESETS[name], { motel: false }), buildEnv(renderer, hdr, PRESETS[name], { motel: true })];
      scene.environment = envs[rig.current][state.motel ? 1 : 0];
      rig.retarget();
    },
  };
}

main().catch((err) => {
  console.error(err);
  loader.fail('Baby wouldn’t start. Reload the page to try again.');
});
