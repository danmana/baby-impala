import { h, svg, ICONS } from './dom';
import type { Lore } from '../content/lore';

/** Paging through a set of pages (the trunk inventory): ‹ n / total › */
export interface LoreNav {
  index: number;
  total: number;
  prev: () => void;
  next: () => void;
}

const CHEVRON_L = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15.5 4.5 C 12 8, 9.5 10.5, 7.8 12.2 C 9.6 13.8, 12.2 16.4, 15.2 19.6"/></svg>';
const CHEVRON_R = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8.5 4.6 C 12 8.2, 14.4 10.4, 16.2 12.1 C 14.3 13.9, 11.8 16.5, 8.8 19.5"/></svg>';

/** A journal page that slides in from the side (a bottom sheet on phones). */
export class LorePanel {
  readonly el: HTMLElement;
  private body: HTMLElement;
  private isOpen = false;
  onClose: (() => void) | null = null;
  private lastFocus: Element | null = null;
  private nav: LoreNav | null = null;
  private pager: HTMLElement;
  private count: HTMLElement;

  constructor(host: HTMLElement) {
    const close = h('button', { class: 'close', type: 'button', 'aria-label': 'Close page', onclick: () => this.close() });
    close.append(svg(ICONS.close));
    this.body = h('div', { class: 'content' });
    const prev = h('button', { class: 'turn prev', type: 'button', 'aria-label': 'Previous item', onclick: () => this.nav?.prev() });
    prev.innerHTML = CHEVRON_L;
    const next = h('button', { class: 'turn next', type: 'button', 'aria-label': 'Next item', onclick: () => this.nav?.next() });
    next.innerHTML = CHEVRON_R;
    this.count = h('span', { class: 'count' });
    this.pager = h('nav', { class: 'pager', 'aria-label': 'Trunk inventory', hidden: true }, prev, this.count, next);
    this.el = h('aside', { class: 'lore sheet', role: 'dialog', 'aria-modal': 'false', 'aria-label': 'Journal page', tabindex: -1 },
      h('span', { class: 'tape a' }), h('span', { class: 'tape b' }), close, this.body, this.pager);
    host.append(this.el);
    window.addEventListener('keydown', (e) => {
      if (!this.isOpen) return;
      if (e.key === 'Escape') this.close();
      if (this.nav && e.key === 'ArrowLeft') this.nav.prev();
      if (this.nav && e.key === 'ArrowRight') this.nav.next();
    });
    // click outside closes: listen on the canvas and the page, not on UI controls
    document.addEventListener('pointerdown', (e) => {
      if (!this.isOpen) return;
      const t = e.target as HTMLElement;
      if (this.el.contains(t)) return;
      if (t.closest('.hotspot, .tabs, .checklist, .deck, .journal-btn')) return;
      this.pendingOutside = { x: e.clientX, y: e.clientY, shown: this.shown };
    });
    document.addEventListener('pointerup', (e) => {
      const p = this.pendingOutside;
      this.pendingOutside = null;
      // only a click, not an orbit drag, closes the page, and not a click that
      // just opened another page (another piece of gear in the trunk)
      if (p && p.shown === this.shown && Math.hypot(e.clientX - p.x, e.clientY - p.y) < 6) this.close();
    });
  }

  private pendingOutside: { x: number; y: number; shown: number } | null = null;
  /** bumped every time a page is shown */
  private shown = 0;

  get open() { return this.isOpen; }

  show(l: Lore, actions: { label: string; run: () => void }[] = [], nav: LoreNav | null = null) {
    if (!this.isOpen) this.lastFocus = document.activeElement;
    this.shown++;
    this.nav = nav;
    this.pager.hidden = !nav;
    if (nav) this.count.textContent = `${nav.index + 1} / ${nav.total}`;
    const parts: Node[] = [];
    if (l.kicker) parts.push(h('p', { class: 'kicker' }, l.kicker));
    parts.push(h('h2', {}, l.title), ...l.body.map((p) => h('p', {}, p)));
    if (l.note) parts.push(h('p', { class: 'margin-note' }, l.note));
    if (actions.length) {
      parts.push(h('div', { class: 'actions' },
        ...actions.map((a) => h('button', { class: 'stamp', type: 'button', onclick: a.run }, a.label))));
    }
    if (l.refs) parts.push(h('p', { class: 'refs' }, l.refs));
    this.body.replaceChildren(...parts);
    this.body.scrollTop = 0;
    this.el.classList.add('open');
    this.isOpen = true;
    if (!this.el.contains(document.activeElement)) this.el.focus({ preventScroll: true });
  }

  close() {
    if (!this.isOpen) return;
    this.el.classList.remove('open');
    this.isOpen = false;
    this.nav = null;
    this.onClose?.();
    if (this.lastFocus instanceof HTMLElement) this.lastFocus.focus({ preventScroll: true });
  }
}
