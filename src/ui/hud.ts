import { h, svg, ICONS, checkboxSvg } from './dom';
import type { ViewName } from '../scene/director';
import type { PresetName } from '../scene/lighting';
import { isTouch } from '../scene/quality';

export interface HudHandlers {
  view: (v: ViewName) => void;
  toggle: (key: ToggleKey, on: boolean) => void;
  flipPlates: () => void;
  reset: () => void;
  volume: (v: number) => void;
  mute: (m: boolean) => void;
  title: () => void;
  light: (p: PresetName) => void;
}

export type ToggleKey = 'engine' | 'spotlights' | 'rain' | 'motel' | 'sigils';

const TOGGLES: { key: ToggleKey; label: string }[] = [
  { key: 'engine', label: 'Engine running' },
  { key: 'spotlights', label: 'Spotlights' },
  { key: 'rain', label: 'Rain' },
  { key: 'motel', label: 'Motel' },
  { key: 'sigils', label: 'Show sigils' },
];

const TABS: { view: ViewName; label: string }[] = [
  { view: 'normal', label: 'Normal' },
  { view: 'exploded', label: 'Exploded' },
  { view: 'trunk', label: 'Trunk' },
  { view: 'interior', label: 'Interior' },
];

/** Journal-style controls: index tabs, a taped checklist, stamps, the hint and the footer. */
export class Hud {
  readonly root: HTMLElement;
  private tabs = new Map<ViewName, HTMLButtonElement>();
  private checks = new Map<ToggleKey, HTMLButtonElement>();
  private hint: HTMLElement;
  private muteBtn: HTMLButtonElement;
  private slider: HTMLInputElement;
  private checklist: HTMLElement;
  private lightBtns = new Map<PresetName, HTMLButtonElement>();
  readonly trunkNote: HTMLElement;
  private hintDone = false;

  constructor(host: HTMLElement, on: HudHandlers) {
    this.root = host;
    const title = h('button', { class: 'title-scrap sheet', type: 'button', 'aria-label': 'About Baby', onclick: () => on.title() },
      h('strong', {}, 'Baby'), h('span', {}, '’67 Chevrolet Impala, four-door hardtop'));

    const tabs = h('nav', { class: 'tabs', role: 'tablist', 'aria-label': 'Views' });
    for (const t of TABS) {
      const b = h('button', {
        class: 'tab', type: 'button', role: 'tab', 'aria-selected': t.view === 'normal' ? 'true' : 'false',
        onclick: () => on.view(t.view),
      }, t.label);
      this.tabs.set(t.view, b);
      tabs.append(b);
    }

    this.checklist = h('section', { class: 'checklist sheet', 'aria-label': 'Scene' },
      h('span', { class: 'tape' }), h('h2', {}, 'tonight:'));
    const lightRow = h('div', { class: 'light-row', role: 'radiogroup', 'aria-label': 'Light' });
    (['moon', 'sunset', 'day'] as PresetName[]).forEach((p, i) => {
      const b = h('button', { class: 'light', type: 'button', role: 'radio', 'aria-checked': p === 'moon' ? 'true' : 'false' });
      b.innerHTML = `<svg viewBox="0 0 30 30" preserveAspectRatio="none" aria-hidden="true"><path class="ring" pathLength="100" d="M${25 - i} ${9 + i * 0.5} C ${21 + i} ${2.5}, ${5 - i * 0.5} ${3 + i * 0.4}, ${2.5} ${14 + i * 0.3} C ${1 + i * 0.5} ${25}, ${24 - i} ${28 - i * 0.4}, ${27.5} ${16 - i * 0.4} C ${28.5} ${11}, ${24} ${6}, ${17 + i} ${4.5}"/></svg>`;
      b.append(h('span', {}, p === 'moon' ? 'Moon' : p === 'sunset' ? 'Sunset' : 'Day'));
      b.addEventListener('click', () => {
        this.setLight(p);
        on.light(p);
      });
      this.lightBtns.set(p, b);
      lightRow.append(b);
    });
    this.checklist.append(lightRow);
    TOGGLES.forEach((t, i) => {
      const b = h('button', { class: 'check', type: 'button', role: 'switch', 'aria-checked': 'false', 'data-key': t.key });
      b.innerHTML = checkboxSvg(i + 1);
      b.append(h('span', {}, t.label));
      b.addEventListener('click', () => {
        const next = b.getAttribute('aria-checked') !== 'true';
        this.setToggle(t.key, next);
        on.toggle(t.key, next);
      });
      this.checks.set(t.key, b);
      this.checklist.append(b);
    });
    this.slider = h('input', { type: 'range', min: 0, max: 100, value: 80, 'aria-label': 'Volume' });
    this.slider.addEventListener('input', () => on.volume(Number(this.slider.value) / 100));
    this.muteBtn = h('button', { class: 'mute', type: 'button', 'aria-label': 'Mute', 'aria-pressed': 'false' });
    this.muteBtn.append(svg(ICONS.speaker));
    this.muteBtn.addEventListener('click', () => {
      const m = this.muteBtn.getAttribute('aria-pressed') !== 'true';
      this.setMuted(m);
      on.mute(m);
    });
    this.checklist.append(
      h('div', { class: 'volume' }, this.muteBtn, this.slider),
      h('div', { class: 'stamps' },
        h('button', { class: 'stamp', type: 'button', onclick: () => on.flipPlates() }, 'Swap plates'),
        h('button', { class: 'stamp', type: 'button', onclick: () => on.reset() }, 'Reset view'),
      ),
    );

    const journalBtn = h('button', { class: 'journal-btn sheet', type: 'button', 'aria-label': 'Scene controls', 'aria-expanded': 'false' });
    journalBtn.append(svg(ICONS.journal));
    journalBtn.addEventListener('click', () => {
      const open = !this.checklist.classList.contains('open');
      this.checklist.classList.toggle('open', open);
      journalBtn.setAttribute('aria-expanded', String(open));
    });

    this.hint = h('p', { class: 'hint', 'aria-hidden': 'true' },
      isTouch() ? 'drag to rotate · pinch to zoom · tap the sigils' : 'drag to rotate · scroll to zoom · click the sigils');
    this.trunkNote = h('p', { class: 'trunk-note', 'aria-live': 'polite' });

    const footer = h('footer', { class: 'footer' },
      h('div', {}, 'Unofficial fan page'),
      h('div', { html: 'Made by <a href="https://x.com/danmana" target="_blank" rel="noopener">@danmana</a> and <a href="https://www.anthropic.com/claude-opus-5-5" target="_blank" rel="noopener">Opus 5.5</a> · ' }),
    );
    const credits = h('details', {},
      h('summary', {}, 'Credits'),
      h('div', { class: 'credits', html:
        'Base 3D model: <a href="https://sketchfab.com/3d-models/chevrolet-impala-1967-bce35ef0c10d41fdb3f7d8c4225144d2" target="_blank" rel="noopener">“Chevrolet Impala 1967”</a> by <a href="https://sketchfab.com/Eques_inferno" target="_blank" rel="noopener">Eques_inferno</a>, CC BY 4.0, adapted. ' +
        'Music on the local tapes by Kevin MacLeod (<a href="https://incompetech.com" target="_blank" rel="noopener">incompetech.com</a>), CC BY 4.0. ' +
        'HDRIs, textures and trunk props from <a href="https://polyhaven.com" target="_blank" rel="noopener">Poly Haven</a> and <a href="https://ambientcg.com" target="_blank" rel="noopener">ambientCG</a> (CC0). ' +
        'Engine and door sounds: Joseph Sardin, <a href="https://bigsoundbank.com" target="_blank" rel="noopener">BigSoundBank</a> (CC0); tape deck and creak: PDSounds (public domain). ' +
        'Fonts: League Gothic, Special Elite, Reenie Beanie (OFL / Apache 2.0).' }),
    );
    footer.lastElementChild?.append(credits);

    host.append(title, tabs, this.checklist, journalBtn, this.hint, this.trunkNote, footer);
  }

  show() {
    this.root.classList.add('hud-on');
  }

  setView(v: ViewName) {
    this.tabs.forEach((b, k) => b.setAttribute('aria-selected', String(k === v)));
  }

  setLight(p: PresetName) {
    this.lightBtns.forEach((b, k) => b.setAttribute('aria-checked', String(k === p)));
  }

  setToggle(key: ToggleKey, on: boolean) {
    this.checks.get(key)?.setAttribute('aria-checked', String(on));
  }

  setMuted(m: boolean) {
    this.muteBtn.setAttribute('aria-pressed', String(m));
    this.muteBtn.replaceChildren(svg(m ? ICONS.speakerOff : ICONS.speaker));
    this.muteBtn.setAttribute('aria-label', m ? 'Unmute' : 'Mute');
  }

  showHint() {
    if (this.hintDone) return;
    this.hint.classList.add('show');
    setTimeout(() => this.hideHint(), 9000);
  }

  hideHint() {
    if (this.hintDone) return;
    this.hintDone = true;
    this.hint.classList.remove('show');
  }

  note(text: string | null) {
    if (text) this.trunkNote.textContent = text;
    this.trunkNote.classList.toggle('show', !!text);
  }
}
