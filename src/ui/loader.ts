import { h, svg, ICONS } from './dom';
import type { Progress } from '../boot/progress';

/**
 * Journal-page loading screen. The pencil line eases towards the real
 * progress (never jumping, never stalling dead), and each checklist line is
 * struck through only when its stage is finished and the bar has reached it.
 */
/**
 * A pen stroke through a checklist line: a fixed, slightly wobbly path that is
 * drawn in from left to right (stroke-dashoffset), so the line never changes
 * angle while it grows.
 */
function strike(seed: number) {
  const j = (k: number) => (((seed * 7 + k * 13) % 10) / 10 - 0.5) * 2.4;
  const y0 = 7 + j(1) * 0.6, y1 = 5.6 + j(2), y2 = 6.4 + j(3), y3 = 4.6 + j(4) * 0.6;
  return svg(`<svg class="strike" viewBox="0 0 200 12" preserveAspectRatio="none" aria-hidden="true">
    <path d="M1 ${y0.toFixed(1)} C 50 ${y1.toFixed(1)}, 110 ${y2.toFixed(1)}, 199 ${y3.toFixed(1)}" pathLength="100"/>
  </svg>`);
}

export class Loader {
  readonly el: HTMLElement;
  private steps: HTMLLIElement[] = [];
  private fill: SVGPathElement;
  private start: HTMLButtonElement;
  private note: HTMLElement;
  private bar: HTMLElement;
  private shown = 0;
  private last = performance.now();
  private raf = 0;
  private isReady = false;
  onReady: (() => void) | null = null;

  constructor(host: HTMLElement, private progress: Progress, onStart: () => void) {
    const fmt = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long' });
    const line = svg(`<svg viewBox="0 0 400 12" preserveAspectRatio="none" aria-hidden="true">
      <path class="track" d="M2 6 C 70 4.5, 150 7.5, 230 5.5 S 340 4.8, 398 6.2" stroke-width="1.4" fill="none" stroke-linecap="round"/>
      <path class="fill" d="M2 6 C 70 4.5, 150 7.5, 230 5.5 S 340 4.8, 398 6.2" stroke-width="3.2" fill="none" stroke-linecap="round" pathLength="1000" stroke-dasharray="1000" stroke-dashoffset="1000"/>
    </svg>`);
    this.fill = line.querySelector('.fill') as SVGPathElement;
    this.start = h('button', { class: 'start', type: 'button', disabled: true, onclick: () => onStart() });
    this.start.append(svg(ICONS.key), 'Start the engine');
    this.note = h('p', { class: 'note' }, 'Sound on. Driver picks the music.');
    this.bar = h('div', { class: 'bar', role: 'progressbar', 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-valuenow': 0, 'aria-label': 'Loading' }, line);
    this.el = h('div', { class: 'loader', role: 'dialog', 'aria-label': 'Loading Baby' },
      h('div', { class: 'page sheet' },
        h('div', { class: 'date' }, `${fmt}, somewhere outside Lawrence, KS`),
        h('h1', {}, 'Baby'),
        h('p', { class: 'sub' }, '1967 Chevrolet Impala, four-door hardtop'),
        h('ol', {}, ...progress.stages.map((s, i) => {
          const li = h('li', {}, s.label, strike(i));
          this.steps.push(li);
          return li;
        })),
        this.bar,
        this.start,
        this.note,
      ),
    );
    host.append(this.el);
    this.tick = this.tick.bind(this);
    this.raf = requestAnimationFrame(this.tick);
  }

  private tick(now: number) {
    const dt = Math.min(0.1, (now - this.last) / 1000);
    this.last = now;
    const target = this.progress.target;
    const gap = target - this.shown;
    if (gap > 0) {
      // ease in proportion to the gap, but never faster than a steady hand
      // (0.55 of the bar per second) nor slower than a slow creep
      const step = Math.min(gap, Math.max(gap * (1 - Math.exp(-dt * 3)), dt * 0.04), dt * 0.55);
      this.shown += step;
    }
    const ends = this.progress.ends;
    this.progress.stages.forEach((s, i) => {
      const struck = s.done && this.shown >= ends[i] - 0.004 && (i === 0 || this.steps[i - 1].classList.contains('done'));
      this.steps[i].classList.toggle('done', struck);
      this.steps[i].classList.toggle('active', !struck && (i === 0 || this.steps[i - 1].classList.contains('done')));
    });
    this.fill.style.strokeDashoffset = String(1000 - this.shown * 1000);
    this.bar.setAttribute('aria-valuenow', String(Math.round(this.shown * 100)));
    if (!this.isReady && this.progress.complete && this.shown >= 0.999) {
      this.isReady = true;
      this.start.disabled = false;
      this.start.classList.add('ready');
      this.start.focus({ preventScroll: true });
      this.onReady?.();
    }
    if (!this.isReady || this.shown < 1) this.raf = requestAnimationFrame(this.tick);
  }

  get ready() {
    return this.isReady;
  }

  fail(msg: string) {
    this.note.textContent = msg;
    this.note.classList.add('error');
  }

  hide() {
    cancelAnimationFrame(this.raf);
    this.el.classList.add('gone');
    setTimeout(() => this.el.remove(), 1600);
  }
}
