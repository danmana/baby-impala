/**
 * Dev only (not part of the site's bundle): records clips for the videos.
 *
 * Load it into a running page (?autostart&nointro&quality=high) with
 *   const cap = await import('/src/dev/capture.ts'); await cap.install();
 * and start tools/capture/server.py. Then `cap.record(name)` renders a shot
 * from shots.ts frame by frame on a virtual clock: performance.now and
 * requestAnimationFrame are taken over, so every frame advances exactly
 * 1/fps however long it takes to render, encode and send.
 */
import * as THREE from 'three';
import { SHOTS, type Shot, type Baby } from './shots';

const SINK = 'http://127.0.0.1:8765';

let B: Baby;
let vnow = 0;
const realNow = performance.now.bind(performance);
const queue: FrameRequestCallback[] = [];
/** set while a shot drives the camera: called after the director each frame */
let camera: ((t: number) => void) | null = null;
let shotTime = 0;

export const status = { name: '', frame: 0, total: 0, done: true, error: '', abort: false, ms: { step: 0, encode: 0 } };

/** the size clips are encoded at (rendered larger, then scaled down) */
const OUT_W = 1920, OUT_H = 1080;

export async function install(pixelRatio = 1.5) {
  B = (window as unknown as { __baby: Baby }).__baby;
  vnow = performance.now();
  performance.now = () => vnow;
  window.requestAnimationFrame = (cb) => {
    queue.push(cb);
    return queue.length;
  };
  // the render loop's next real frame hands itself over to the queue
  while (!queue.length) await new Promise((r) => setTimeout(r, 20));
  const director = B.director;
  const update = director.update.bind(director);
  director.update = (dt: number) => {
    update(dt);
    camera?.(shotTime);
  };
  B.audio.setMuted(true);
  B.stage.setQuality({ ...B.stage.quality, pixelRatio });
  step(1 / 60);
  const gl = B.stage.renderer.getContext();
  return { w: gl.drawingBufferWidth, h: gl.drawingBufferHeight };
}

function step(dt: number) {
  vnow += dt * 1000;
  for (const cb of queue.splice(0)) cb(vnow);
}

/** simulate without recording (let transitions settle) */
export function run(seconds: number, fps = 60) {
  for (let i = 0; i < Math.round(seconds * fps); i++) step(1 / fps);
}

/**
 * Record a shot. Frames are scaled down on a 2D canvas right after each
 * render (the WebGL buffer is only readable in the same task) and encoded to
 * H.264 in the page with WebCodecs; only the encoded stream is posted to the
 * server, a few MB at a time. Posting raw frames was slow (and DevTools'
 * network log kept a copy of every one).
 */
export async function record(name: string, opts: { fps?: number } = {}) {
  const shot: Shot = SHOTS[name];
  if (!shot) throw new Error(`no shot ${name}`);
  const fps = opts.fps ?? 60;
  Object.assign(status, { name, frame: 0, total: Math.round(shot.dur * fps), done: false, error: '', abort: false });
  const out = document.createElement('canvas');
  out.width = OUT_W;
  out.height = OUT_H;
  const ctx = out.getContext('2d', { alpha: false })!;
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  const chunks: Uint8Array<ArrayBuffer>[] = [];
  let bytes = 0;
  const encoder = new VideoEncoder({
    output: (chunk) => {
      const b = new Uint8Array(chunk.byteLength);
      chunk.copyTo(b);
      chunks.push(b);
      bytes += b.byteLength;
    },
    error: (e) => (status.error = String(e)),
  });
  const send = async () => {
    if (!chunks.length) return;
    const body = new Blob(chunks.splice(0));
    bytes = 0;
    const r = await fetch(`${SINK}/chunk`, { method: 'POST', body });
    if (!r.ok) throw new Error(await r.text());
  };
  try {
    const config: VideoEncoderConfig = {
      codec: 'avc1.640033', width: OUT_W, height: OUT_H, framerate: fps,
      bitrate: 60_000_000, bitrateMode: 'variable', latencyMode: 'quality',
      hardwareAcceleration: 'prefer-hardware', avc: { format: 'annexb' },
    };
    if (!(await VideoEncoder.isConfigSupported(config)).supported) throw new Error('H.264 encoder config not supported');
    encoder.configure(config);
    camera = null;
    await shot.setup?.(B);
    if (shot.warm) run(shot.warm, fps);
    const cues = [...(shot.cues ?? [])].sort((a, b) => a[0] - b[0]);
    const cam = shot.cam ? shot.cam(B) : null;
    camera = cam ? (t) => cam(THREE.MathUtils.clamp(t / shot.dur, 0, 1)) : null;
    const gl: HTMLCanvasElement = B.stage.renderer.domElement;
    await fetch(`${SINK}/start?name=${name}&fps=${fps}`, { method: 'POST' });
    for (let i = 0; i < status.total; i++) {
      if (status.abort) throw new Error('aborted');
      if (status.error) throw new Error(status.error);
      shotTime = i / fps;
      while (cues.length && cues[0][0] <= shotTime) cues.shift()![1](B);
      const t0 = realNow();
      step(1 / fps);
      ctx.drawImage(gl, 0, 0, OUT_W, OUT_H);
      const t1 = realNow();
      const frame = new VideoFrame(out, { timestamp: Math.round((i * 1e6) / fps), duration: Math.round(1e6 / fps) });
      encoder.encode(frame, { keyFrame: i % fps === 0 });
      frame.close();
      while (encoder.encodeQueueSize > 3) await new Promise((r) => encoder.addEventListener('dequeue', r, { once: true }));
      if (bytes > 4e6) await send();
      const m = status.ms;
      m.step += (t1 - t0 - m.step) * 0.1;
      m.encode += (realNow() - t1 - m.encode) * 0.1;
      status.frame = i + 1;
    }
    await encoder.flush();
    await send();
    await fetch(`${SINK}/end`, { method: 'POST' });
  } catch (e) {
    status.error = String(e);
  } finally {
    if (encoder.state !== 'closed') encoder.close();
    camera = null;
    status.done = true;
    B.stage.resize();
  }
}

/** start a list of shots in the background; poll `status` */
export function recordAll(names: string[]) {
  void (async () => {
    for (const n of names) {
      await record(n);
      if (status.error) break;
    }
  })();
}

/** render one frame of a shot at time t (seconds) without recording, for framing checks */
export async function preview(name: string, t: number) {
  const shot = SHOTS[name];
  camera = null;
  await shot.setup?.(B);
  if (shot.warm) run(shot.warm);
  const cues = [...(shot.cues ?? [])].sort((a, b) => a[0] - b[0]);
  const cam = shot.cam ? shot.cam(B) : null;
  camera = cam ? (x) => cam(THREE.MathUtils.clamp(x / shot.dur, 0, 1)) : null;
  for (let i = 0; i <= Math.round(t * 60); i++) {
    shotTime = i / 60;
    while (cues.length && cues[0][0] <= shotTime) cues.shift()![1](B);
    step(1 / 60);
  }
  // keep the last frame on screen for a screenshot
  camera = null;
}

/** render one frame from a given camera pose, for trying out framings */
export function frameAt(pos: [number, number, number], look: [number, number, number], fov = 38) {
  camera = () => {
    const cam: THREE.PerspectiveCamera = B.camera;
    cam.position.set(...pos);
    cam.lookAt(...look);
    cam.fov = fov;
    cam.updateProjectionMatrix();
  };
  step(1 / 60);
  camera = null;
}
