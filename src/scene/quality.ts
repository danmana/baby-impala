// Device tier detection and adaptive quality.
export type Tier = 'low' | 'medium' | 'high';

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
      return { tier, pixelRatio: Math.min(dpr, 2), shadows: true, shadowMapSize: 2048, reflectionScale: 0.5, bloom: true, particles: 1, msaa: 4, volumetrics: true };
    case 'medium':
      return { tier, pixelRatio: Math.min(dpr, 1.5), shadows: true, shadowMapSize: 1024, reflectionScale: 0.35, bloom: true, particles: 0.6, msaa: 2, volumetrics: true };
    default:
      return { tier, pixelRatio: Math.min(dpr, 1), shadows: false, shadowMapSize: 512, reflectionScale: 0.25, bloom: false, particles: 0.3, msaa: 0, volumetrics: false };
  }
}

/** Watches frame times and asks to step down when the target can't be held. */
export class FrameGovernor {
  private samples: number[] = [];
  private cooldown = 9; // let the intro and first shader compiles settle
  private strikes = 0;
  constructor(private targetMs: number, private onDowngrade: () => boolean) {}
  tick(dt: number) {
    if (this.cooldown > 0) {
      this.cooldown -= dt;
      return;
    }
    // ignore hitches (tab switches, compiles): only sustained slowness counts
    if (dt > 0.25) return;
    this.samples.push(dt * 1000);
    if (this.samples.length >= 120) {
      const sorted = [...this.samples].sort((a, b) => a - b);
      const median = sorted[Math.floor(sorted.length / 2)];
      this.samples.length = 0;
      this.strikes = median > this.targetMs * 1.3 ? this.strikes + 1 : 0;
      if (this.strikes >= 2) {
        this.strikes = 0;
        if (this.onDowngrade()) this.cooldown = 5;
        else this.cooldown = 1e9;
      }
    }
  }
}
