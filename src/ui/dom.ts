type Attrs = Record<string, string | number | boolean | undefined | ((e: Event) => void)>;

/** Tiny element builder. */
export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: Attrs = {},
  ...children: (Node | string | null | undefined | false)[]
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === false) continue;
    if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2).toLowerCase(), v as EventListener);
    else if (k === 'class') el.className = String(v);
    else if (k === 'html') el.innerHTML = String(v);
    else el.setAttribute(k, v === true ? '' : String(v));
  }
  for (const c of children) if (c !== null && c !== undefined && c !== false) el.append(c);
  return el;
}

export function svg(markup: string): SVGSVGElement {
  const t = document.createElement('template');
  t.innerHTML = markup.trim();
  return t.content.firstElementChild as SVGSVGElement;
}

export const ICONS = {
  play: '<svg viewBox="0 0 16 16"><path d="M4 2.5v11l9-5.5z"/></svg>',
  pause: '<svg viewBox="0 0 16 16"><path d="M3.5 2.5h3.2v11H3.5zM9.3 2.5h3.2v11H9.3z"/></svg>',
  prev: '<svg viewBox="0 0 16 16"><path d="M2.5 2.5h2v11h-2zM14 2.5v11L5.5 8z"/></svg>',
  next: '<svg viewBox="0 0 16 16"><path d="M11.5 2.5h2v11h-2zM2 2.5v11L10.5 8z"/></svg>',
  eject: '<svg viewBox="0 0 16 16"><path d="M8 2.5l6 7H2zM2 11.5h12v2H2z"/></svg>',
  close: '<svg viewBox="0 0 24 24"><path d="M5 5.5 19 18.6M18.5 5 5.3 19"/></svg>',
  speaker: '<svg viewBox="0 0 24 24"><path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path class="w1" d="M15.5 9c1.2 1.6 1.2 4.4 0 6"/><path class="w2" d="M18 6.5c2.6 3 2.6 8 0 11"/></svg>',
  speakerOff: '<svg viewBox="0 0 24 24"><path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9.5l5 5M20.5 9.5l-5 5"/></svg>',
  journal: '<svg viewBox="0 0 24 24"><path d="M6 3.5h11.5v17H6c-1 0-1.8-.8-1.8-1.8V5.3C4.2 4.3 5 3.5 6 3.5z"/><path d="M8.5 3.5v17M11 8h4.5M11 11h4.5"/></svg>',
  key: '<svg viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="11" cy="18" r="7"/><circle cx="11" cy="18" r="2.2"/><path d="M18 18h15M28 18v5M32 18v4"/></svg>',
};

/** Hand-drawn checkbox + pencil tick. Boxes wobble a little differently each time. */
export function checkboxSvg(seed: number) {
  const j = (n: number) => (Math.sin(seed * 12.9898 + n * 78.233) * 43758.5453) % 1;
  const w = (n: number) => 2 + j(n) * 1.4;
  return `<svg viewBox="0 0 24 24"><path class="box" d="M${w(1)} ${w(2)} L${21 + j(3)} ${2.5 + j(4)} L${21.5 - j(5)} ${21 + j(6)} L${2.5 + j(7)} ${21.5 - j(8)} Z"/><path class="tick" d="M5 12.5 L10 18 L22 1"/></svg>`;
}
