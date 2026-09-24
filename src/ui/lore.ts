import { h, svg, ICONS } from './dom';
import type { Lore } from '../content/lore';

/** A journal page that slides in from the side (a bottom sheet on phones). */
export class LorePanel {
  readonly el: HTMLElement;
  private body: HTMLElement;
  private isOpen = false;
  onClose: (() => void) | null = null;
  private lastFocus: Element | null = null;

  constructor(host: HTMLElement) {
    const close = h('button', { class: 'close', type: 'button', 'aria-label': 'Close page', onclick: () => this.close() });
    close.append(svg(ICONS.close));
    this.body = h('div', {});
    this.el = h('aside', { class: 'lore paper stain', role: 'dialog', 'aria-modal': 'false', 'aria-label': 'Journal page', tabindex: -1 },
      h('span', { class: 'tape a' }), h('span', { class: 'tape b' }), close, this.body);
    host.append(this.el);
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) this.close();
    });
    // click outside closes: listen on the canvas and the page, not on UI controls
    document.addEventListener('pointerdown', (e) => {
      if (!this.isOpen) return;
      const t = e.target as HTMLElement;
      if (this.el.contains(t)) return;
      if (t.closest('.hotspot, .tabs, .checklist, .deck, .journal-btn')) return;
      this.pendingOutside = { x: e.clientX, y: e.clientY };
    });
    document.addEventListener('pointerup', (e) => {
      const p = this.pendingOutside;
      this.pendingOutside = null;
      // only a click, not an orbit drag, closes the page
      if (p && Math.hypot(e.clientX - p.x, e.clientY - p.y) < 6) this.close();
    });
  }

  private pendingOutside: { x: number; y: number } | null = null;

  get open() { return this.isOpen; }

  show(l: Lore, actions: { label: string; run: () => void }[] = []) {
    this.lastFocus = document.activeElement;
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
    this.el.scrollTop = 0;
    this.el.classList.add('open');
    this.isOpen = true;
    this.el.focus({ preventScroll: true });
  }

  close() {
    if (!this.isOpen) return;
    this.el.classList.remove('open');
    this.isOpen = false;
    this.onClose?.();
    if (this.lastFocus instanceof HTMLElement) this.lastFocus.focus({ preventScroll: true });
  }
}
