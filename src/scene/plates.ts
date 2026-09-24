import * as THREE from 'three';

/** Canvas-drawn licence plates: the original Kansas KAZ 2Y5 and the Ohio CNK 80Q3. */
const W = 1024;
const H = 512;

function outline(ctx: CanvasRenderingContext2D) {
  ctx.beginPath();
  ctx.roundRect(8, 8, W - 16, H - 16, 40);
  ctx.closePath();
}

function base(ctx: CanvasRenderingContext2D) {
  ctx.clearRect(0, 0, W, H);
  outline(ctx);
}

function grime(ctx: CanvasRenderingContext2D, seed: number) {
  let s = seed;
  const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  ctx.save();
  ctx.globalCompositeOperation = 'multiply';
  for (let i = 0; i < 900; i++) {
    const x = rnd() * W, y = rnd() * H, rr = rnd() * 6 + 1;
    ctx.fillStyle = `rgba(${120 + rnd() * 60},${110 + rnd() * 50},${90 + rnd() * 40},${0.08 + rnd() * 0.12})`;
    ctx.beginPath();
    ctx.arc(x, y, rr, 0, Math.PI * 2);
    ctx.fill();
  }
  const g = ctx.createLinearGradient(0, H * 0.6, 0, H);
  g.addColorStop(0, 'rgba(90,80,60,0)');
  g.addColorStop(1, 'rgba(90,80,60,0.35)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

function bolts(ctx: CanvasRenderingContext2D) {
  for (const [x, y] of [[150, 64], [W - 150, 64], [150, H - 64], [W - 150, H - 64]]) {
    const g = ctx.createRadialGradient(x - 4, y - 4, 2, x, y, 18);
    g.addColorStop(0, '#f2f2f2');
    g.addColorStop(1, '#6f6f6f');
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(x, y, 16, 0, Math.PI * 2);
    ctx.fill();
  }
}

function embossed(ctx: CanvasRenderingContext2D, text: string, x: number, y: number, size: number, color: string) {
  ctx.font = `${size}px "League Gothic", "Arial Narrow", sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = 'rgba(0,0,0,0.35)';
  ctx.fillText(text, x + 5, y + 6);
  ctx.fillStyle = 'rgba(255,255,255,0.6)';
  ctx.fillText(text, x - 3, y - 3);
  ctx.fillStyle = color;
  ctx.fillText(text, x, y);
}

export function drawKansas(): HTMLCanvasElement {
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const ctx = c.getContext('2d')!;
  base(ctx);
  ctx.save();
  ctx.clip();
  const sky = ctx.createLinearGradient(0, 0, 0, H);
  sky.addColorStop(0, '#f7f7f2');
  sky.addColorStop(0.55, '#e3eef4');
  sky.addColorStop(0.8, '#a9d3ea');
  sky.addColorStop(1, '#8ec6e6');
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, W, H);
  // wheat band
  ctx.fillStyle = '#e8cf3a';
  ctx.fillRect(0, H - 70, W, 50);
  ctx.fillStyle = '#c9a820';
  for (let i = 0; i < 90; i++) ctx.fillRect(i * 12, H - 78 + (i % 3) * 3, 3, 16);
  // capitol silhouette, faint
  ctx.fillStyle = 'rgba(160,190,205,0.45)';
  ctx.beginPath();
  ctx.ellipse(W * 0.5, H * 0.66, 70, 48, 0, Math.PI, 0);
  ctx.fill();
  ctx.fillRect(W * 0.5 - 120, H * 0.66, 240, 60);
  // header
  ctx.font = '600 84px Georgia, "Times New Roman", serif';
  ctx.textAlign = 'center';
  ctx.fillStyle = '#1b2f6b';
  ctx.fillText('KANSAS', W / 2, 105);
  // county sticker + year sticker
  ctx.fillStyle = '#1d3f8c';
  ctx.fillRect(40, 30, 118, 74);
  ctx.fillStyle = '#fff';
  ctx.font = 'bold 56px Arial, sans-serif';
  ctx.fillText('SG', 99, 88);
  ctx.fillStyle = '#e9b120';
  ctx.fillRect(W - 168, 30, 128, 74);
  ctx.fillStyle = '#1a1a1a';
  ctx.font = 'bold 48px Arial, sans-serif';
  ctx.fillText('05', W - 104, 84);
  embossed(ctx, 'KAZ 2Y5', W / 2, 400, 330, '#15171c');
  grime(ctx, 7);
  ctx.restore();
  bolts(ctx);
  ctx.lineWidth = 10;
  ctx.strokeStyle = '#6d6d6d';
  outline(ctx);
  ctx.stroke();
  return c;
}

export function drawOhio(): HTMLCanvasElement {
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const ctx = c.getContext('2d')!;
  base(ctx);
  ctx.save();
  ctx.clip();
  ctx.fillStyle = '#f4f3ee';
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#cf2a2f';
  ctx.fillRect(0, 22, W, 70);
  ctx.fillStyle = '#233f8f';
  ctx.fillRect(0, H - 96, W, 60);
  // state outline emblem
  ctx.fillStyle = '#f4f3ee';
  ctx.beginPath();
  ctx.moveTo(W / 2 - 40, 30); ctx.lineTo(W / 2 + 36, 34); ctx.lineTo(W / 2 + 44, 70);
  ctx.lineTo(W / 2 + 10, 88); ctx.lineTo(W / 2 - 36, 80);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = '#233f8f';
  ctx.font = 'italic 34px Georgia, serif';
  ctx.textAlign = 'center';
  ctx.fillText('Ohio', W / 2, 70);
  // stickers
  ctx.fillStyle = '#d42424';
  ctx.fillRect(34, H - 118, 120, 90);
  ctx.fillStyle = '#fff';
  ctx.font = 'bold 60px Arial, sans-serif';
  ctx.fillText('25', 94, H - 50);
  ctx.fillStyle = '#39b24a';
  ctx.fillRect(W - 170, H - 118, 136, 90);
  ctx.fillStyle = '#fff';
  ctx.font = 'bold 44px Arial, sans-serif';
  ctx.fillText('07', W - 102, H - 58);
  embossed(ctx, 'CNK 80Q3', W / 2, 392, 320, '#1f2a4a');
  grime(ctx, 11);
  ctx.restore();
  bolts(ctx);
  ctx.lineWidth = 10;
  ctx.strokeStyle = '#6d6d6d';
  outline(ctx);
  ctx.stroke();
  return c;
}

/**
 * A plate that can flip: a thin double-sided slab whose front shows one
 * state and back shows the other. Rotating it 180° about its horizontal axis
 * swaps KAZ 2Y5 for CNK 80Q3.
 */
export class Plate {
  readonly pivot = new THREE.Group();
  private from = 0;
  private target = 0;
  private angle = 0;
  private t = 1;
  ohio = false;

  constructor(kansas: THREE.Texture, ohio: THREE.Texture, env: THREE.Texture | null) {
    const w = 0.305, h = 0.152;
    // reflective plate sheeting: a faint emissive keeps it legible in the dark
    const mk = (tex: THREE.Texture) => new THREE.MeshStandardMaterial({
      map: tex, roughness: 0.5, metalness: 0.1, envMap: env, envMapIntensity: 0.7,
      emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 0.22,
    });
    const front = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mk(kansas));
    front.position.z = 0.0015;
    const back = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mk(ohio));
    back.rotation.x = Math.PI; // readable when the slab is flipped about X
    back.position.z = -0.0015;
    const edge = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.002),
      new THREE.MeshStandardMaterial({ color: 0x777777, metalness: 1, roughness: 0.4, envMap: env }));
    this.pivot.add(front, back, edge);
    front.name = back.name = edge.name = 'plate';
  }

  toggle(instant = false) {
    this.ohio = !this.ohio;
    this.from = this.angle;
    this.target = this.ohio ? Math.PI : 0;
    this.t = instant ? 1 : 0;
    if (instant) this.angle = this.target;
  }

  update(dt: number) {
    if (this.t >= 1) return;
    // a spin with a little overshoot, like a sign on a hinge
    this.t = Math.min(1, this.t + dt / 0.9);
    const c1 = 1.4, c3 = c1 + 1;
    const x = this.t - 1;
    const k = 1 + c3 * x * x * x + c1 * x * x;
    this.angle = this.from + (this.target - this.from) * k;
    this.pivot.rotation.x = this.angle;
  }
}
