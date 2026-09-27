/** Hand-made canvas textures: the painted Devil's Trap, carved initials, the tape deck dial. */

type Pt = [number, number];

export function rng(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

/** A rough brush stroke along a polyline: several jittered passes, uneven width. */
export function brush(ctx: CanvasRenderingContext2D, pts: Pt[], width: number, rand: () => number, color: string) {
  const passes = 4;
  for (let p = 0; p < passes; p++) {
    ctx.beginPath();
    const j = width * 0.18;
    pts.forEach(([x, y], i) => {
      const jx = (rand() - 0.5) * j, jy = (rand() - 0.5) * j;
      if (i === 0) ctx.moveTo(x + jx, y + jy);
      else ctx.lineTo(x + jx, y + jy);
    });
    ctx.lineWidth = width * (0.55 + rand() * 0.5);
    ctx.globalAlpha = 0.28 + rand() * 0.3;
    ctx.strokeStyle = color;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
  }
  // dry-brush flecks along the stroke
  ctx.globalAlpha = 0.5;
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1], [x1, y1] = pts[i];
    const n = Math.ceil(Math.hypot(x1 - x0, y1 - y0) / 6);
    for (let k = 0; k < n; k++) {
      if (rand() > 0.35) continue;
      const t = k / n;
      ctx.fillStyle = color;
      ctx.fillRect(x0 + (x1 - x0) * t + (rand() - 0.5) * width, y0 + (y1 - y0) * t + (rand() - 0.5) * width, 1.5, 1.5);
    }
  }
  ctx.globalAlpha = 1;
}

export function curve(points: Pt[], steps = 12): Pt[] {
  // Catmull-Rom through points
  const out: Pt[] = [];
  const P = [points[0], ...points, points[points.length - 1]];
  for (let i = 1; i < P.length - 2; i++) {
    for (let s = 0; s < steps; s++) {
      const t = s / steps, t2 = t * t, t3 = t2 * t;
      const f = (a: number, b: number, c: number, d: number) =>
        0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
      out.push([f(P[i - 1][0], P[i][0], P[i + 1][0], P[i + 2][0]), f(P[i - 1][1], P[i][1], P[i + 1][1], P[i + 2][1])]);
    }
  }
  out.push(points[points.length - 1]);
  return out;
}

export function circlePts(cx: number, cy: number, r: number, wobble: number, rand: () => number, n = 90): Pt[] {
  const pts: Pt[] = [];
  const ph = rand() * 6;
  for (let i = 0; i <= n; i++) {
    const a = (i / n) * Math.PI * 2;
    const rr = r * (1 + wobble * Math.sin(a * 3 + ph) + wobble * 0.5 * Math.sin(a * 7 + ph * 2));
    pts.push([cx + rr * Math.cos(a), cy + rr * Math.sin(a)]);
  }
  return pts;
}

// sigils in the five gaps between the star's points, as unit-sized glyph strokes
const SIGILS: Pt[][][] = [
  // top-left: hook + loop
  [[[-0.5, 0.2], [-0.2, -0.1], [0.1, 0.25]], [[0.1, 0.25], [0.3, -0.3], [0.55, -0.1], [0.45, 0.2], [0.2, 0.1]]],
  // top-right: Z with a bar
  [[[-0.5, -0.3], [0.3, -0.3], [-0.3, 0.3], [0.5, 0.3]], [[0.2, 0.05], [0.2, 0.55]], [[0.0, 0.55], [0.4, 0.55]]],
  // right: X with bars
  [[[-0.4, -0.5], [0.4, 0.5]], [[0.4, -0.5], [-0.4, 0.5]], [[-0.55, -0.15], [-0.1, -0.15]], [[0.1, 0.2], [0.55, 0.2]]],
  // bottom: curl + box
  [[[-0.6, 0.1], [-0.4, -0.3], [-0.15, 0.05], [-0.35, 0.3], [-0.55, 0.2]], [[0.0, -0.2], [0.55, -0.2], [0.55, 0.3], [0.0, 0.3], [0.0, -0.2]]],
  // left: forked stem (a trident-like glyph)
  [[[-0.42, -0.5], [-0.36, -0.08], [0.0, 0.04], [0.36, -0.08], [0.42, -0.5]], [[0.0, -0.45], [0.0, 0.6]], [[-0.22, 0.42], [0.22, 0.42]]],
];

export function drawDevilsTrap(width = 2048, height = 1408): HTMLCanvasElement {
  const c = document.createElement('canvas');
  c.width = width;
  c.height = height;
  const ctx = c.getContext('2d')!;
  const rand = rng(1967);
  // black underside with dust and scuffs
  ctx.fillStyle = '#0b0b0c';
  ctx.fillRect(0, 0, width, height);
  for (let i = 0; i < 2600; i++) {
    ctx.fillStyle = `rgba(${90 + rand() * 60},${80 + rand() * 50},${70 + rand() * 40},${0.03 + rand() * 0.06})`;
    ctx.fillRect(rand() * width, rand() * height, 1 + rand() * 3, 1 + rand() * 3);
  }
  // seen from behind the open lid the texture is upside down: paint rotated 180°
  ctx.save();
  ctx.translate(width / 2, height / 2);
  ctx.rotate(Math.PI);
  ctx.translate(-width / 2, -height / 2);
  const paint = '#e7dcc2';
  const cx = width * 0.5, cy = height * 0.5, R = height * 0.36;
  brush(ctx, circlePts(cx, cy, R, 0.012, rand), 22, rand, paint);
  // pentagram, point up
  const star: Pt[] = [];
  for (let k = 0; k < 5; k++) {
    const a = -Math.PI / 2 + (k * 4 * Math.PI) / 5;
    star.push([cx + R * 0.97 * Math.cos(a), cy + R * 0.97 * Math.sin(a)]);
  }
  star.push(star[0]);
  for (let i = 0; i < 5; i++) brush(ctx, [star[i], star[i + 1]], 20, rand, paint);
  // sigils between the points
  for (let k = 0; k < 5; k++) {
    const a = -Math.PI / 2 + Math.PI / 5 + (k * 2 * Math.PI) / 5;
    const sx = cx + R * 0.66 * Math.cos(a), sy = cy + R * 0.66 * Math.sin(a);
    const s = R * 0.2;
    for (const stroke of SIGILS[k]) {
      const pts = stroke.map(([x, y]) => [sx + x * s, sy + y * s] as Pt);
      brush(ctx, pts.length > 2 ? curve(pts, 8) : pts, 12, rand, paint);
    }
  }
  // small separate sigils to the left and right
  const side = (x: number) => {
    const s = R * 0.26, y = cy - R * 0.08;
    brush(ctx, circlePts(x, y, s * 0.45, 0.04, rand, 40), 10, rand, paint);
    brush(ctx, [[x - s, y], [x + s, y]], 10, rand, paint);
    brush(ctx, [[x, y - s], [x, y + s * 1.3]], 10, rand, paint);
    for (let k = 0; k < 6; k++) {
      const a = (k / 6) * Math.PI * 2;
      brush(ctx, [[x + Math.cos(a) * s * 0.45, y + Math.sin(a) * s * 0.45], [x + Math.cos(a) * s * 0.75, y + Math.sin(a) * s * 0.75]], 7, rand, paint);
    }
  };
  side(width * 0.12);
  // right-hand one is a stick-like sigil
  {
    const x = width * 0.88, y = cy - R * 0.1, s = R * 0.25;
    brush(ctx, curve([[x - s * 0.2, y - s], [x, y - s * 0.3], [x - s * 0.1, y + s * 0.4], [x + s * 0.1, y + s]], 8), 10, rand, paint);
    brush(ctx, [[x - s * 0.7, y - s * 0.15], [x + s * 0.6, y - s * 0.25]], 10, rand, paint);
    brush(ctx, curve([[x + s * 0.2, y + s * 0.2], [x + s * 0.6, y + s * 0.5], [x + s * 0.4, y + s * 0.9]], 8), 9, rand, paint);
    brush(ctx, [[x - s * 0.55, y + s * 0.5], [x - s * 0.1, y + s * 0.45]], 9, rand, paint);
  }
  ctx.restore();
  // drips and wear
  for (let i = 0; i < 40; i++) {
    const x = rand() * width, y = rand() * height;
    ctx.fillStyle = 'rgba(11,11,12,0.6)';
    ctx.fillRect(x, y, 2 + rand() * 18, 1 + rand() * 3);
  }
  return c;
}

export function drawInitials(width = 1024, height = 96): HTMLCanvasElement {
  const c = document.createElement('canvas');
  c.width = width;
  c.height = height;
  const ctx = c.getContext('2d')!;
  const rand = rng(2005);
  // walnut-ish wood grain
  const g = ctx.createLinearGradient(0, 0, 0, height);
  g.addColorStop(0, '#5a3a1e');
  g.addColorStop(1, '#3e2612');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, width, height);
  for (let i = 0; i < 70; i++) {
    ctx.strokeStyle = `rgba(${30 + rand() * 30},${16 + rand() * 12},${6},${0.25 + rand() * 0.3})`;
    ctx.lineWidth = 0.6 + rand() * 1.4;
    ctx.beginPath();
    const y0 = rand() * height;
    ctx.moveTo(0, y0);
    for (let x = 0; x <= width; x += 32) ctx.lineTo(x, y0 + Math.sin(x * 0.01 + i) * 3 + (rand() - 0.5) * 2);
    ctx.stroke();
  }
  // carved letters: dark cut with a light raw-wood edge
  const carve = (text: string, x: number) => {
    ctx.font = '600 58px "Special Elite", monospace';
    ctx.textBaseline = 'middle';
    ctx.save();
    ctx.translate(x, height / 2 + 2);
    ctx.rotate((rand() - 0.5) * 0.08);
    ctx.fillStyle = 'rgba(214,176,120,0.75)';
    ctx.fillText(text, 1.5, 1.5);
    ctx.fillStyle = '#1b0f06';
    ctx.fillText(text, 0, 0);
    ctx.restore();
  };
  carve('D.W.', width * 0.56);
  carve('S.W.', width * 0.72);
  return c;
}

export function drawDial(width = 1024, height = 158): HTMLCanvasElement {
  // the deck's dial window, laid out like the one in Baby's dash: FM over AM,
  // a little marker before each band, DX / LOC at the right, the red needle
  const c = document.createElement('canvas');
  c.width = width;
  c.height = height;
  const ctx = c.getContext('2d')!;
  const g = ctx.createLinearGradient(0, 0, 0, height);
  g.addColorStop(0, '#161616');
  g.addColorStop(1, '#0a0a0a');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = 'rgba(210,205,190,0.55)';
  ctx.lineWidth = 3;
  ctx.strokeRect(6, 6, width - 12, height - 12);
  ctx.fillStyle = '#ece6d4';
  ctx.textBaseline = 'middle';
  const big = '44px "League Gothic", "Arial Narrow", sans-serif';
  const small = '30px "League Gothic", "Arial Narrow", sans-serif';
  const rows: [string, number, string[], number[]][] = [
    ['FM', 46, ['88', '94', '98', '103', '106', '108'], [160, 290, 395, 500, 615, 725]],
    ['AM', 110, ['54', '60', '70', '80', '100', '130', '170'], [160, 265, 355, 440, 520, 625, 830]],
  ];
  for (const [band, y, nums, xs] of rows) {
    ctx.fillRect(28, y - 8, 14, 16);
    ctx.beginPath();
    ctx.moveTo(42, y - 8);
    ctx.lineTo(54, y - 14);
    ctx.lineTo(54, y + 14);
    ctx.lineTo(42, y + 8);
    ctx.fill();
    ctx.font = small;
    ctx.fillText(band, 66, y);
    ctx.font = big;
    nums.forEach((t, i) => ctx.fillText(t, xs[i], y));
  }
  ctx.font = small;
  ctx.fillText('DX', 900, 46);
  ctx.fillText('LOC', 900, 110);
  ctx.fillRect(960, 38, 14, 16);
  ctx.fillRect(960, 102, 14, 16);
  // a hairline between the bands and the red needle near 100
  ctx.strokeStyle = 'rgba(236,230,212,0.35)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(150, 79);
  ctx.lineTo(880, 79);
  ctx.stroke();
  ctx.fillStyle = '#d42a1c';
  ctx.fillRect(488, 14, 6, height - 28);
  return c;
}

/** The cassette door under the dial: the flap with its maker's line, and the model block at the right. */
export function drawDeckDoor(width = 1024, height = 168): HTMLCanvasElement {
  const c = document.createElement('canvas');
  c.width = width;
  c.height = height;
  const ctx = c.getContext('2d')!;
  ctx.fillStyle = '#070707';
  ctx.fillRect(0, 0, width, height);
  // the flap: glossy black, a faint edge and the slot line along its top
  const flapW = width * 0.66;
  const g = ctx.createLinearGradient(0, 0, 0, height);
  g.addColorStop(0, '#1c1c1c');
  g.addColorStop(0.5, '#0e0e0e');
  g.addColorStop(1, '#141414');
  ctx.fillStyle = g;
  ctx.fillRect(40, 18, flapW - 40, height - 36);
  ctx.strokeStyle = 'rgba(200,200,200,0.25)';
  ctx.lineWidth = 2;
  ctx.strokeRect(40, 18, flapW - 40, height - 36);
  // "High-Fi CASSETTE" with a little tape mark, the red Rampage script, BY AUDIOVOX under it
  ctx.fillStyle = '#9a9a9a';
  ctx.textBaseline = 'middle';
  ctx.font = '24px Arial, sans-serif';
  ctx.fillText('High-Fi', 70, 64);
  ctx.fillText('CASSETTE', 70, 98);
  ctx.strokeStyle = '#9a9a9a';
  ctx.lineWidth = 2;
  ctx.strokeRect(162, 52, 30, 18);
  ctx.beginPath();
  ctx.arc(171, 61, 3, 0, Math.PI * 2);
  ctx.arc(183, 61, 3, 0, Math.PI * 2);
  ctx.stroke();
  ctx.save();
  ctx.translate(250, 84);
  ctx.transform(1, 0, -0.18, 1, 0, 0);
  ctx.fillStyle = ctx.strokeStyle = '#e0261f';
  ctx.font = 'bold 100px "Reenie Beanie", cursive';
  ctx.lineWidth = 5;
  ctx.strokeText('Rampage', 0, 0);
  ctx.fillText('Rampage', 0, 0);
  ctx.restore();
  ctx.fillStyle = '#c9c9c9';
  ctx.font = 'bold 20px Arial, sans-serif';
  ctx.fillText('BY AUDIOVOX', 372, 126);
  // the model block
  ctx.fillStyle = '#1a1a1a';
  ctx.fillRect(flapW + 16, 18, width - flapW - 34, height - 36);
  ctx.fillStyle = '#8c8c8c';
  ctx.font = 'italic bold 58px Arial, sans-serif';
  ctx.fillText('AV2000', flapW + 60, 92);
  return c;
}
