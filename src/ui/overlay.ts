import * as THREE from 'three';
import { h } from './dom';
import type { Hotspot, HotspotView } from '../content/lore';

const SIGIL = `<svg viewBox="0 0 34 34">
  <circle class="ring" cx="17" cy="17" r="11"/>
  <circle class="dot" cx="17" cy="17" r="10.5"/>
  <circle class="sig" cx="17" cy="17" r="9"/>
  <path class="sig" d="M17 9.5 L21.4 22.8 L10.1 14.6 H23.9 L12.6 22.8 Z" stroke-linejoin="round"/>
</svg>`;

interface Marker {
  spot: Hotspot;
  el: HTMLButtonElement;
  pos: THREE.Vector3;
  visible: boolean;
}

/**
 * HTML overlays projected from 3D: pulsing sigil hotspots, the pencilled
 * labels of the exploded view, and the name tag that follows the pointer in
 * the trunk.
 */
export class Overlay {
  readonly root: HTMLElement;
  private markers: Marker[] = [];
  private xlabels: { el: HTMLElement; pos: THREE.Vector3 }[] = [];
  private xroot: HTMLElement;
  readonly tag: HTMLElement;
  private v = new THREE.Vector3();
  private ray = new THREE.Raycaster();
  private frame = 0;
  enabled = true;
  view: HotspotView | null = null;

  constructor(host: HTMLElement, spots: Hotspot[], onPick: (s: Hotspot) => void, private occluders: () => THREE.Object3D[]) {
    this.root = h('div', { class: 'hotspots' });
    for (const s of spots) {
      const el = h('button', { class: 'hotspot hidden', type: 'button', 'aria-label': s.label, html: SIGIL });
      el.append(h('span', { class: 'label' }, s.label));
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        onPick(s);
      });
      this.root.append(el);
      this.markers.push({ spot: s, el, pos: new THREE.Vector3(...s.pos), visible: false });
    }
    this.xroot = h('div', { class: 'xlabels passthrough' });
    this.tag = h('div', { class: 'tag paper' });
    host.append(this.root, this.xroot, this.tag);
  }

  positionOf(id: string): THREE.Vector3 | null {
    return this.markers.find((m) => m.spot.id === id)?.pos ?? null;
  }

  setExplodedLabels(labels: { text: string; pos: THREE.Vector3 }[]) {
    this.xroot.replaceChildren();
    this.xlabels = labels.map((l) => {
      const el = h('div', { class: 'xlabel' }, l.text);
      el.style.transform = `rotate(${(Math.random() - 0.5) * 6}deg)`;
      this.xroot.append(el);
      return { el, pos: l.pos };
    });
  }

  private project(p: THREE.Vector3, cam: THREE.Camera, w: number, hgt: number) {
    this.v.copy(p).project(cam);
    return { x: (this.v.x * 0.5 + 0.5) * w, y: (-this.v.y * 0.5 + 0.5) * hgt, behind: this.v.z > 1 };
  }

  update(cam: THREE.PerspectiveCamera, xl: { alpha: number }[]) {
    const w = window.innerWidth, hgt = window.innerHeight;
    this.frame++;
    const camPos = cam.position;
    for (const m of this.markers) {
      const show = this.enabled && this.view === m.spot.view;
      if (!show) {
        if (m.visible || !m.el.classList.contains('hidden')) m.el.classList.add('hidden');
        m.visible = false;
        continue;
      }
      const p = this.project(m.pos, cam, w, hgt);
      m.el.style.transform = `translate(${p.x.toFixed(1)}px, ${p.y.toFixed(1)}px)`;
      // occlusion test every few frames
      if (this.frame % 5 === 0 || !m.visible) {
        let vis = !p.behind && p.x > -20 && p.x < w + 20 && p.y > -20 && p.y < hgt + 20;
        const dist = camPos.distanceTo(m.pos);
        if (vis && dist > 0.4) {
          this.ray.set(camPos, this.v.copy(m.pos).sub(camPos).normalize());
          this.ray.far = dist - 0.12;
          const hit = this.ray.intersectObjects(this.occluders(), true).find((i) => {
            const mat = (i.object as THREE.Mesh).material as THREE.Material;
            return !mat.transparent;
          });
          vis = !hit;
        }
        m.visible = vis;
        m.el.classList.toggle('hidden', !vis);
      }
    }
    // pencilled labels: project, then push apart any that would overlap
    const placed: { x: number; y: number; w: number; h: number }[] = [];
    const order = this.xlabels.map((l, i) => ({ l, i, p: this.project(l.pos, cam, w, hgt) }))
      .sort((a, b) => a.p.y - b.p.y);
    for (const { l, i, p } of order) {
      const a = xl[i]?.alpha ?? 0;
      if (a <= 0.01 || p.behind) {
        l.el.style.opacity = '0';
        continue;
      }
      const bw = l.el.offsetWidth || 120, bh = 26;
      let y = p.y;
      for (let k = 0; k < 6; k++) {
        const hit = placed.find((q) => p.x < q.x + q.w && p.x + bw > q.x && y < q.y + q.h && y + bh > q.y);
        if (!hit) break;
        y = hit.y + hit.h + 2;
      }
      placed.push({ x: p.x, y, w: bw, h: bh });
      l.el.style.opacity = String(a);
      l.el.style.left = `${p.x}px`;
      l.el.style.top = `${y}px`;
    }
  }

  showTag(text: string | null, x = 0, y = 0) {
    if (!text) {
      this.tag.classList.remove('show');
      return;
    }
    this.tag.textContent = text;
    this.tag.style.transform = `translate(${x + 16}px, ${y - 14}px) rotate(-2deg)`;
    this.tag.classList.add('show');
  }
}
