/**
 * Loading progress as a set of weighted stages. Stages report a 0..1 fraction
 * (bytes for downloads, finished chunks for shader warm-up). The loading page
 * eases its bar towards the weighted total and crosses each checklist line
 * when its stage is done and the bar has actually reached it.
 */
export interface StageDef {
  id: string;
  label: string;
  weight: number;
}

interface Stage extends StageDef {
  frac: number;
  done: boolean;
}

export class Progress {
  readonly stages: Stage[];
  private total: number;
  onChange: (() => void) | null = null;

  constructor(defs: StageDef[]) {
    this.stages = defs.map((d) => ({ ...d, frac: 0, done: false }));
    this.total = defs.reduce((a, d) => a + d.weight, 0);
  }

  private get(id: string) {
    const s = this.stages.find((x) => x.id === id);
    if (!s) throw new Error(`unknown stage ${id}`);
    return s;
  }

  set(id: string, frac: number) {
    const s = this.get(id);
    s.frac = Math.max(s.frac, Math.min(1, frac));
    this.onChange?.();
  }

  done(id: string) {
    const s = this.get(id);
    s.frac = 1;
    s.done = true;
    this.onChange?.();
  }

  /** Overall 0..1 target. */
  get target() {
    return this.stages.reduce((a, s) => a + s.weight * s.frac, 0) / this.total;
  }

  /** Where each stage ends on the bar (0..1). */
  get ends() {
    let acc = 0;
    return this.stages.map((s) => (acc += s.weight) / this.total);
  }

  get complete() {
    return this.stages.every((s) => s.done);
  }

  /**
   * Byte-weighted tracker for several parallel downloads feeding one stage.
   * Returns a callback factory: `track(key, expected)(loaded, total)`.
   */
  bytes(id: string) {
    const parts = new Map<string, { loaded: number; total: number }>();
    return (key: string, expected: number) => {
      parts.set(key, { loaded: 0, total: Math.max(1, expected) });
      return (loaded: number, total: number) => {
        const p = parts.get(key)!;
        p.loaded = loaded;
        p.total = Math.max(p.total, total, 1);
        let l = 0, t = 0;
        parts.forEach((v) => {
          l += v.loaded;
          t += v.total;
        });
        // downloads are ~85% of a byte stage; decoding/building the rest
        this.set(id, (l / t) * 0.85);
      };
    };
  }
}
