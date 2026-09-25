import { fetchBytes, expectedBytes, type ProgressFn } from '../boot/assets';

/**
 * Audio: recorded V8 start / idle / shut-off (an AC Cobra 427, CC0 from
 * BigSoundBank), the trunk latch, hinge creak and slam, the tape deck's
 * mechanics, and a music bus with a little old-car-stereo colour.
 * Samples are decoded during loading, so nothing waits when you press a button.
 */
export const SFX = {
  engineStart: 'audio/sfx/engine_start.mp3',
  engineIdle: 'audio/sfx/engine_idle.wav',
  engineStop: 'audio/sfx/engine_stop.mp3',
  trunkLatch: 'audio/sfx/trunk_latch.mp3',
  trunkCreak: 'audio/sfx/trunk_creak.mp3',
  trunkClose: 'audio/sfx/trunk_close.mp3',
  tapeInsert: 'audio/sfx/tape_insert.mp3',
  tapeEject: 'audio/sfx/tape_eject.mp3',
  tapeButton: 'audio/sfx/tape_button.mp3',
} as const;
export type SfxName = keyof typeof SFX;

export class AudioEngine {
  ctx: AudioContext | null = null;
  master!: GainNode;
  music!: GainNode;
  sfx!: GainNode;
  private buffers = new Map<SfxName, AudioBuffer>();
  private idle: { src: AudioBufferSourceNode; gain: GainNode; lfo: OscillatorNode } | null = null;
  private volume = 0.8;
  private muted = false;
  onChange: (() => void) | null = null;

  /** Download and decode every sample (no AudioContext needed yet). */
  async preload(track: (key: string, expected: number) => ProgressFn) {
    const decoder = new OfflineAudioContext(1, 1, 44100);
    await Promise.all((Object.keys(SFX) as SfxName[]).map(async (name) => {
      const path = SFX[name];
      const buf = await fetchBytes(path, track(path, expectedBytes(path)));
      this.buffers.set(name, await decoder.decodeAudioData(buf));
    }));
  }

  /** Must be called from a user gesture (the "Start the engine" button). */
  unlock() {
    if (!this.ctx) {
      const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new Ctx();
      this.master = this.ctx.createGain();
      this.master.connect(this.ctx.destination);
      this.music = this.ctx.createGain();
      this.sfx = this.ctx.createGain();
      // the stereo sounds like it lives in a '67 dash: some low-mid warmth, rolled-off top
      const warm = this.ctx.createBiquadFilter();
      warm.type = 'peaking';
      warm.frequency.value = 220;
      warm.gain.value = 2.5;
      const air = this.ctx.createBiquadFilter();
      air.type = 'highshelf';
      air.frequency.value = 9000;
      air.gain.value = -4;
      this.music.connect(warm).connect(air).connect(this.master);
      this.sfx.connect(this.master);
      this.applyVolume();
    }
    if (this.ctx.state === 'suspended') void this.ctx.resume();
  }

  get isMuted() { return this.muted; }
  get level() { return this.volume; }

  setVolume(v: number) {
    this.volume = Math.max(0, Math.min(1, v));
    this.applyVolume();
  }

  setMuted(m: boolean) {
    this.muted = m;
    this.applyVolume();
  }

  private applyVolume() {
    if (!this.ctx) return;
    const g = this.muted ? 0 : this.volume;
    this.master.gain.setTargetAtTime(g * g, this.ctx.currentTime, 0.05);
    this.onChange?.();
  }

  /** One-shot sample. */
  play(name: SfxName, opts: { gain?: number; rate?: number; when?: number } = {}) {
    const buf = this.buffers.get(name);
    if (!this.ctx || !buf) return null;
    const src = this.ctx.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = opts.rate ?? 1;
    const g = this.ctx.createGain();
    g.gain.value = opts.gain ?? 1;
    src.connect(g).connect(this.sfx);
    src.start(this.ctx.currentTime + (opts.when ?? 0));
    return { src, gain: g };
  }

  /** Starter, the catch, a couple of blips, then the idle takes over and keeps running. */
  startEngine() {
    if (!this.ctx) return;
    const ctx = this.ctx;
    this.stopIdle(0.05);
    const start = this.play('engineStart', { gain: 1 });
    const startDur = this.buffers.get('engineStart')?.duration ?? 5.6;
    const handover = startDur - 0.75;
    // idle loop fades in under the tail of the start-up
    const buf = this.buffers.get('engineIdle');
    if (!buf) return;
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.loop = true;
    const gain = ctx.createGain();
    const t0 = ctx.currentTime + handover;
    gain.gain.setValueAtTime(0, ctx.currentTime);
    gain.gain.setValueAtTime(0, t0);
    gain.gain.linearRampToValueAtTime(0.85, t0 + 0.7);
    // a slow drift in rpm so the loop never sounds like a loop
    const lfo = ctx.createOscillator();
    lfo.frequency.value = 0.13;
    const depth = ctx.createGain();
    depth.gain.value = 0.018;
    lfo.connect(depth).connect(src.playbackRate);
    src.connect(gain).connect(this.sfx);
    src.start(t0);
    lfo.start(t0);
    this.idle = { src, gain, lfo };
    void start;
  }

  stopEngine() {
    if (!this.ctx || !this.idle) return;
    this.play('engineStop', { gain: 0.9 });
    this.stopIdle(0.35);
  }

  private stopIdle(fade: number) {
    if (!this.ctx || !this.idle) return;
    const t = this.ctx.currentTime;
    const { src, gain, lfo } = this.idle;
    gain.gain.cancelScheduledValues(t);
    gain.gain.setValueAtTime(gain.gain.value, t);
    gain.gain.linearRampToValueAtTime(0, t + fade);
    src.stop(t + fade + 0.05);
    lfo.stop(t + fade + 0.05);
    this.idle = null;
  }

  get engineRunning() { return this.idle !== null; }

  trunkOpen() {
    this.play('trunkLatch', { gain: 0.7 });
    this.play('trunkCreak', { gain: 0.9, when: 0.18 });
  }

  trunkClose() {
    this.play('trunkClose', { gain: 0.8, when: 0.55 });
  }
}
