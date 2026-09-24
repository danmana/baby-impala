/**
 * Audio graph: master volume + mute, the synthesised V8 (crank, catch, idle
 * burble), the trunk-hinge creak, and a bus the tape deck plays into.
 * Everything is generated with Web Audio so there are no sound files to ship
 * besides the music.
 */
export class AudioEngine {
  ctx: AudioContext | null = null;
  master!: GainNode;
  music!: GainNode;
  sfx!: GainNode;
  private idle: { stop: () => void; setRpm: (rpm: number, t?: number) => void } | null = null;
  private volume = 0.8;
  private muted = false;
  onChange: (() => void) | null = null;

  /** Must be called from a user gesture (the "Start the engine" button). */
  unlock() {
    if (!this.ctx) {
      const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new Ctx();
      this.master = this.ctx.createGain();
      this.master.connect(this.ctx.destination);
      this.music = this.ctx.createGain();
      this.sfx = this.ctx.createGain();
      // the stereo sounds like it lives in a '67 dash: gentle low-mid warmth, rolled-off top
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

  private noiseBuffer(seconds = 2) {
    const ctx = this.ctx!;
    const b = ctx.createBuffer(1, ctx.sampleRate * seconds, ctx.sampleRate);
    const d = b.getChannelData(0);
    let last = 0;
    for (let i = 0; i < d.length; i++) {
      // brown-ish noise
      last = (last + 0.02 * (Math.random() * 2 - 1)) / 1.02;
      d[i] = last * 3.5;
    }
    return b;
  }

  /** Starter crank, the catch, a blip of throttle, then a lumpy idle that keeps running. */
  startEngine(reduced = false) {
    if (!this.ctx) return;
    const ctx = this.ctx;
    const t0 = ctx.currentTime + 0.05;
    const crankDur = reduced ? 0.5 : 1.1;

    // --- starter motor: whirring motor + compression pulses
    const starter = ctx.createOscillator();
    starter.type = 'sawtooth';
    starter.frequency.setValueAtTime(140, t0);
    starter.frequency.linearRampToValueAtTime(190, t0 + crankDur);
    const sf = ctx.createBiquadFilter();
    sf.type = 'bandpass';
    sf.frequency.value = 400;
    sf.Q.value = 1.2;
    const sg = ctx.createGain();
    sg.gain.setValueAtTime(0, t0);
    sg.gain.linearRampToValueAtTime(0.12, t0 + 0.05);
    sg.gain.setValueAtTime(0.12, t0 + crankDur - 0.05);
    sg.gain.linearRampToValueAtTime(0, t0 + crankDur + 0.08);
    // compression strokes chop the starter sound ~11 times a second
    const chop = ctx.createOscillator();
    chop.type = 'square';
    chop.frequency.setValueAtTime(9, t0);
    chop.frequency.linearRampToValueAtTime(13, t0 + crankDur);
    const chopDepth = ctx.createGain();
    chopDepth.gain.value = 0.08;
    chop.connect(chopDepth).connect(sg.gain);
    starter.connect(sf).connect(sg).connect(this.sfx);
    starter.start(t0);
    chop.start(t0);
    starter.stop(t0 + crankDur + 0.2);
    chop.stop(t0 + crankDur + 0.2);

    // --- the engine catches
    this.idle?.stop();
    this.idle = this.v8(t0 + crankDur - 0.05);
    const tc = t0 + crankDur;
    this.idle.setRpm(420, tc - 0.05);
    this.idle.setRpm(reduced ? 1100 : 1900, tc + 0.35);
    this.idle.setRpm(1250, tc + 0.9);
    this.idle.setRpm(720, tc + 2.2);
  }

  stopEngine() {
    this.idle?.stop();
    this.idle = null;
  }

  get engineRunning() { return this.idle !== null; }

  /** V8 burble: a 4-stroke cycle wave rich in the uneven cross-plane harmonics. */
  private v8(start: number) {
    const ctx = this.ctx!;
    const N = 48;
    const real = new Float32Array(N);
    const imag = new Float32Array(N);
    // 8 firings per cycle with slightly uneven spacing and strength
    const firings = [0, 0.118, 0.26, 0.372, 0.5, 0.63, 0.742, 0.87];
    const strength = [1, 0.8, 0.95, 0.7, 1, 0.85, 0.9, 0.75];
    for (let n = 1; n < N; n++) {
      let re = 0, im = 0;
      for (let k = 0; k < 8; k++) {
        const ph = 2 * Math.PI * n * firings[k];
        re += strength[k] * Math.cos(ph);
        im += strength[k] * Math.sin(ph);
      }
      const roll = 1 / (1 + n * 0.08);
      real[n] = re * roll;
      imag[n] = im * roll;
    }
    const wave = ctx.createPeriodicWave(real, imag);
    const osc = ctx.createOscillator();
    osc.setPeriodicWave(wave);
    const shaper = ctx.createWaveShaper();
    const curve = new Float32Array(1024);
    for (let i = 0; i < curve.length; i++) {
      const x = (i / (curve.length - 1)) * 2 - 1;
      curve[i] = Math.tanh(x * 2.2);
    }
    shaper.curve = curve;
    const pre = ctx.createGain();
    pre.gain.value = 0.35;
    const lp = ctx.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.value = 520;
    lp.Q.value = 0.8;
    const body = ctx.createBiquadFilter();
    body.type = 'peaking';
    body.frequency.value = 95;
    body.gain.value = 7;
    // exhaust hiss riding on the pulses
    const noise = ctx.createBufferSource();
    noise.buffer = this.noiseBuffer(3);
    noise.loop = true;
    const nf = ctx.createBiquadFilter();
    nf.type = 'bandpass';
    nf.frequency.value = 260;
    nf.Q.value = 0.7;
    const ng = ctx.createGain();
    ng.gain.value = 0.25;
    const out = ctx.createGain();
    out.gain.setValueAtTime(0, start);
    out.gain.linearRampToValueAtTime(0.55, start + 0.12);
    out.gain.setTargetAtTime(0.32, start + 3.0, 1.5);
    osc.connect(pre).connect(shaper).connect(lp).connect(body).connect(out);
    noise.connect(nf).connect(ng).connect(out);
    // a slow wobble so the idle never sounds like a loop
    const lfo = ctx.createOscillator();
    lfo.frequency.value = 0.7;
    const lfoG = ctx.createGain();
    lfoG.gain.value = 0.25;
    lfo.connect(lfoG).connect(osc.frequency);
    out.connect(this.sfx);
    osc.frequency.setValueAtTime(3, start);
    osc.start(start);
    noise.start(start);
    lfo.start(start);
    const setRpm = (rpm: number, t = ctx.currentTime) => {
      const f = rpm / 60 / 2; // 4-stroke cycle frequency
      osc.frequency.linearRampToValueAtTime(f, t);
      lp.frequency.linearRampToValueAtTime(300 + rpm * 0.35, t);
      ng.gain.linearRampToValueAtTime(0.15 + rpm / 6000, t);
    };
    return {
      setRpm,
      stop: () => {
        const t = ctx.currentTime;
        out.gain.cancelScheduledValues(t);
        out.gain.setTargetAtTime(0, t, 0.25);
        osc.stop(t + 1.5);
        noise.stop(t + 1.5);
        lfo.stop(t + 1.5);
      },
    };
  }

  /** Old hinge: stick-slip squeal gliding down in pitch. */
  creak(duration = 1.1) {
    if (!this.ctx) return;
    const ctx = this.ctx;
    const t0 = ctx.currentTime + 0.02;
    const osc = ctx.createOscillator();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(420, t0);
    osc.frequency.linearRampToValueAtTime(260, t0 + duration * 0.6);
    osc.frequency.linearRampToValueAtTime(330, t0 + duration);
    const bp = ctx.createBiquadFilter();
    bp.type = 'bandpass';
    bp.frequency.value = 900;
    bp.Q.value = 6;
    const g = ctx.createGain();
    g.gain.value = 0;
    // stick-slip: irregular bursts of friction
    let t = t0;
    while (t < t0 + duration) {
      const on = 0.012 + Math.random() * 0.03;
      const amp = 0.06 + Math.random() * 0.1;
      g.gain.setValueAtTime(amp, t);
      g.gain.setValueAtTime(amp * 0.15, t + on);
      t += on + Math.random() * 0.025;
    }
    g.gain.setTargetAtTime(0, t0 + duration, 0.05);
    const thunk = ctx.createOscillator();
    thunk.frequency.setValueAtTime(90, t0);
    thunk.frequency.exponentialRampToValueAtTime(40, t0 + 0.15);
    const tg = ctx.createGain();
    tg.gain.setValueAtTime(0.3, t0);
    tg.gain.exponentialRampToValueAtTime(0.001, t0 + 0.2);
    osc.connect(bp).connect(g).connect(this.sfx);
    thunk.connect(tg).connect(this.sfx);
    osc.start(t0);
    thunk.start(t0);
    osc.stop(t0 + duration + 0.3);
    thunk.stop(t0 + 0.3);
  }
}
