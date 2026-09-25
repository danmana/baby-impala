import * as THREE from 'three';
import { brush, circlePts, curve, rng } from './textures';
import type { Hotspot, HotspotView } from '../content/lore';

type Pt = [number, number];

/**
 * Hand-painted sigils floating at Baby's features, drawn in the same rough
 * cream paint as the Devil's Trap. They live in the 3D scene (depth-tested,
 * fogged, caught by bloom) and breathe slowly like chalk catching light.
 */
function paintSigil(variant: number): HTMLCanvasElement {
  const S = 256;
  const c = document.createElement('canvas');
  c.width = c.height = S;
  const ctx = c.getContext('2d')!;
  const rand = rng(1000 + variant * 77);
  const paint = '#f1e4c6';
  const cx = S / 2, cy = S / 2, R = S * 0.3;
  // soft glow under the paint
  const g = ctx.createRadialGradient(cx, cy, R * 0.2, cx, cy, R * 1.6);
  g.addColorStop(0, 'rgba(255,214,160,0.20)');
  g.addColorStop(1, 'rgba(255,214,160,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, S, S);
  brush(ctx, circlePts(cx, cy, R, 0.025, rand, 60), 9, rand, paint);
  const strokes: Pt[][] = [];
  if (variant % 3 === 0) {
    // pentagram
    const star: Pt[] = [];
    for (let k = 0; k <= 5; k++) {
      const a = -Math.PI / 2 + (k * 4 * Math.PI) / 5;
      star.push([cx + R * 0.92 * Math.cos(a), cy + R * 0.92 * Math.sin(a)]);
    }
    for (let i = 0; i < 5; i++) strokes.push([star[i], star[i + 1]]);
  } else if (variant % 3 === 1) {
    // sun-rayed cross (anti-possession motif)
    strokes.push([[cx, cy - R * 0.8], [cx, cy + R * 0.8]], [[cx - R * 0.8, cy], [cx + R * 0.8, cy]]);
    for (let k = 0; k < 8; k++) {
      const a = (k / 8) * Math.PI * 2 + Math.PI / 8;
      strokes.push([[cx + Math.cos(a) * R * 1.05, cy + Math.sin(a) * R * 1.05], [cx + Math.cos(a) * R * 1.35, cy + Math.sin(a) * R * 1.35]]);
    }
  } else {
    // hooked glyph
    strokes.push(curve([[cx - R * 0.5, cy + R * 0.5], [cx - R * 0.1, cy - R * 0.6], [cx + R * 0.35, cy - R * 0.2], [cx - R * 0.05, cy + R * 0.15], [cx + R * 0.5, cy + R * 0.55]], 8));
    strokes.push([[cx - R * 0.6, cy - R * 0.05], [cx + R * 0.6, cy - R * 0.05]]);
  }
  for (const s of strokes) brush(ctx, s, 7, rand, paint);
  return c;
}

interface Mark {
  spot: Hotspot;
  sprite: THREE.Sprite;
  mat: THREE.SpriteMaterial;
  phase: number;
  hover: number;
  target: number;
}

export class Sigils {
  readonly group = new THREE.Group();
  private marks: Mark[] = [];
  view: HotspotView | null = null;
  enabled = true;
  hovered: string | null = null;
  reduced = false;
  /**
   * Whether a sigil can be seen from the camera. The sprites ignore the depth
   * buffer (a flat sprite on a curved panel would be cut in half), so hiding
   * them behind the car is decided by this ray test instead.
   */
  visibleTest: (id: string) => boolean = () => true;

  constructor(spots: Hotspot[]) {
    this.group.name = 'sigils';
    const tex = [0, 1, 2].map((v) => {
      const t = new THREE.CanvasTexture(paintSigil(v));
      t.colorSpace = THREE.SRGBColorSpace;
      t.anisotropy = 4;
      return t;
    });
    spots.forEach((spot, i) => {
      const mat = new THREE.SpriteMaterial({
        map: tex[i % 3], color: 0xffffff, transparent: true, opacity: 0,
        depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending, fog: true,
      });
      const sprite = new THREE.Sprite(mat);
      sprite.position.set(...spot.pos);
      sprite.renderOrder = 8;
      sprite.raycast = () => undefined;
      this.group.add(sprite);
      this.marks.push({ spot, sprite, mat, phase: i * 1.37, hover: 0, target: 0 });
    });
  }

  positionOf(id: string) {
    return this.marks.find((m) => m.spot.id === id)?.sprite.position ?? null;
  }

  update(dt: number, t: number, camera: THREE.Camera) {
    const camPos = (camera as THREE.PerspectiveCamera).position;
    for (const m of this.marks) {
      const show = this.enabled && this.view === m.spot.view && this.visibleTest(m.spot.id) ? 1 : 0;
      m.target += (show - m.target) * Math.min(1, dt * 4);
      m.hover += ((this.hovered === m.spot.id ? 1 : 0) - m.hover) * Math.min(1, dt * 10);
      const breathe = this.reduced ? 0.85 : 0.72 + 0.28 * Math.sin(t * 1.6 + m.phase);
      m.mat.opacity = m.target * (breathe * 0.85 + m.hover * 0.6);
      m.sprite.visible = m.mat.opacity > 0.003;
      // constant-ish apparent size, smaller up close (interior)
      const d = camPos.distanceTo(m.sprite.position);
      const base = THREE.MathUtils.clamp(d * 0.028, 0.035, 0.16);
      m.sprite.scale.setScalar(base * (1 + m.hover * 0.35));
    }
  }
}
