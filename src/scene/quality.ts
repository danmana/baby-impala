// Device tier detection and adaptive quality.
export type Tier = 'low' | 'medium' | 'high';
/** 'auto' follows the detected tier (and the frame governor); a tier is a user override */
export type QualityMode = 'auto' | Tier;

export interface Quality {
  tier: Tier;
  pixelRatio: number;
  shadows: boolean;
  shadowMapSize: number;
  reflectionScale: number; // planar reflection resolution relative to canvas (0 = off)
  bloom: boolean;
  particles: number; // multiplier for particle counts
  msaa: number;
  volumetrics: boolean;
}

export const reducedMotion = (): boolean =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export const isTouch = (): boolean =>
  typeof window !== 'undefined' && window.matchMedia('(pointer: coarse)').matches;

function gpuString(): string {
  try {
    const c = document.createElement('canvas');
    const gl = c.getContext('webgl2') || c.getContext('webgl');
    if (!gl) return '';
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    const s = ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
    return String(s || '');
  } catch {
    return '';
  }
}

export function detectTier(): Tier {
  const q = new URLSearchParams(location.search).get('quality');
  if (q === 'low' || q === 'medium' || q === 'high') return q;
  const gpu = gpuString().toLowerCase();
  const cores = navigator.hardwareConcurrency || 4;
  const mem = (navigator as Navigator & { deviceMemory?: number }).deviceMemory || 4;
  const mobile = isTouch() && Math.min(screen.width, screen.height) < 900;
  const weakGpu = /(mali-[gt]?[0-7]\d|adreno \(tm\) [1-5]\d\d|powervr|intel\(r\) (hd|uhd) graphics [2-6]\d\d|swiftshader|llvmpipe)/.test(gpu);
  if (weakGpu || cores <= 2 || mem <= 2) return 'low';
  if (mobile) return 'medium';
  if (/apple m\d|rtx|radeon rx|geforce gtx 1[0-9]|apple gpu/.test(gpu) || cores >= 8) return 'high';
  return 'medium';
}

export function qualityFor(tier: Tier): Quality {
  const dpr = window.devicePixelRatio || 1;
  switch (tier) {
    case 'high':
      return { tier, pixelRatio: Math.min(dpr, 1.25), shadows: true, shadowMapSize: 2048, reflectionScale: 0.4, bloom: true, particles: 1, msaa: 4, volumetrics: true };
    case 'medium':
      return { tier, pixelRatio: Math.min(dpr, 1.25), shadows: true, shadowMapSize: 1024, reflectionScale: 0.3, bloom: true, particles: 0.6, msaa: 2, volumetrics: true };
    default:
      return { tier, pixelRatio: Math.min(dpr, 0.75), shadows: false, shadowMapSize: 512, reflectionScale: 0.25, bloom: false, particles: 0.3, msaa: 0, volumetrics: false };
  }
}

const ORDER: Tier[] = ['low', 'medium', 'high'];

/** the level one step up (+1) or down (-1) from `t`, or null past either end */
export function stepTier(t: Tier, dir: 1 | -1): Tier | null {
  return ORDER[ORDER.indexOf(t) + dir] ?? null;
}

// median frame time that counts as room to spare: holding about 55 fps
const HEADROOM_MS = 18;

/**
 * Watches frame times in auto mode and moves one level at a time: down when
 * the target can't be held, up when there's clearly room to spare. A step up
 * that has to be undone soon after is not retried for a while (45 s, then
 * 90 s, …), so the level never flip-flops.
 */
export class FrameGovernor {
  private samples: number[] = [];
  private cooldown = 9; // let the intro and first shader compiles settle
  private slow = 0;
  private fast = 0;
  private clock = 0;
  private lastUp = -1e9;
  private upBlockedUntil = 0;
  private backoff = 45;
  /** `step(dir)` changes the level and returns false when there's no level that way */
  constructor(private targetMs: number, private step: (dir: 1 | -1) => boolean) {}
  /** start watching afresh (after the quality level changed) */
  reset(settle = 5) {
    this.samples.length = 0;
    this.slow = 0;
    this.fast = 0;
    this.cooldown = settle;
  }
  tick(dt: number) {
    this.clock += dt;
    if (this.cooldown > 0) {
      this.cooldown -= dt;
      return;
    }
    // ignore hitches (tab switches, compiles): only sustained timings count
    if (dt > 0.25) return;
    this.samples.push(dt * 1000);
    if (this.samples.length < 120) return;
    const sorted = [...this.samples].sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)];
    this.samples.length = 0;
    this.slow = median > this.targetMs * 1.3 ? this.slow + 1 : 0;
    this.fast = median < HEADROOM_MS ? this.fast + 1 : 0;
    if (this.slow >= 2) {
      this.slow = 0;
      if (this.clock - this.lastUp < 40) {
        this.upBlockedUntil = this.clock + this.backoff;
        this.backoff *= 2;
      }
      if (this.step(-1)) this.cooldown = 5;
    } else if (this.fast >= 4 && this.clock >= this.upBlockedUntil) {
      this.fast = 0;
      if (this.step(1)) {
        this.lastUp = this.clock;
        this.cooldown = 5;
      }
    }
  }
}
