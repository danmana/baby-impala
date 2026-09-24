import { h, svg, ICONS } from './dom';
import { LOADING_STEPS } from '../content/lore';

/** Journal-page loading screen with a crossed-off checklist and a "Start the engine" stamp. */
export class Loader {
  readonly el: HTMLElement;
  private steps: HTMLLIElement[] = [];
  private fill: SVGPathElement;
  private start: HTMLButtonElement;
  private note: HTMLElement;

  constructor(host: HTMLElement, onStart: () => void) {
    const date = new Date();
    const fmt = date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long' });
    const bar = svg(`<svg viewBox="0 0 400 10" preserveAspectRatio="none">
      <path class="track" d="M2 5 C 90 3, 200 7, 398 4" stroke-width="2" fill="none" stroke-linecap="round"/>
      <path class="fill" d="M2 5 C 90 3, 200 7, 398 4" stroke-width="3" fill="none" stroke-linecap="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/>
    </svg>`);
    this.fill = bar.querySelector('.fill') as SVGPathElement;
    this.start = h('button', { class: 'start', type: 'button', disabled: true, onclick: () => onStart() });
    this.start.append(svg(ICONS.key), 'Start the engine');
    this.note = h('p', { class: 'note' }, 'Sound on. Driver picks the music.');
    this.el = h('div', { class: 'loader', role: 'dialog', 'aria-label': 'Loading Baby' },
      h('div', { class: 'page paper stain' },
        h('div', { class: 'date' }, `${fmt}, somewhere outside Lawrence, KS`),
        h('h1', {}, 'Baby'),
        h('p', { class: 'sub' }, '1967 Chevrolet Impala, four-door hardtop'),
        h('ol', {}, ...LOADING_STEPS.map((s) => {
          const li = h('li', {}, s);
          this.steps.push(li);
          return li;
        })),
        h('div', { class: 'bar', role: 'progressbar', 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-valuenow': 0 }, bar),
        this.start,
        this.note,
      ),
    );
    host.append(this.el);
  }

  progress(f: number) {
    const p = Math.max(0, Math.min(1, f));
    this.fill.style.strokeDashoffset = String(100 - p * 100);
    this.el.querySelector('.bar')?.setAttribute('aria-valuenow', String(Math.round(p * 100)));
    this.steps.forEach((li, i) => li.classList.toggle('done', p >= (i + 1) / (this.steps.length + 0.2)));
  }

  ready() {
    this.progress(1);
    this.start.disabled = false;
    this.start.classList.add('ready');
    this.start.focus({ preventScroll: true });
  }

  fail(msg: string) {
    this.note.textContent = msg;
    this.note.classList.add('error');
  }

  hide() {
    this.el.classList.add('gone');
    setTimeout(() => this.el.remove(), 1600);
  }
}
