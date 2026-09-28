import * as THREE from 'three';

/**
 * On phones GPU memory is the limit, not pixels. At full size the textures
 * take about 660 MB once decoded, enough for iOS to drop the page's WebGL
 * context mid-visit (the scene goes white, and Safari then refuses WebGL to
 * that tab until it's closed). This scales images down before they're
 * uploaded, to at most `capFor(mesh)` pixels on a side; a texture used by
 * several meshes gets the largest of their caps. Long, thin strips (the
 * engraving on a gun slide, the etch on a blade) keep their length. Canvas
 * textures are left alone: they're small, and some are redrawn live.
 */
export async function fitTextures(root: THREE.Object3D, capFor: (o: THREE.Object3D) => number) {
  const caps = new Map<THREE.Texture, number>();
  root.traverse((o) => {
    const m = (o as THREE.Mesh).material as THREE.Material | THREE.Material[] | undefined;
    if (!m) return;
    const cap = capFor(o);
    for (const mat of Array.isArray(m) ? m : [m]) {
      for (const v of Object.values(mat)) {
        if (v instanceof THREE.Texture) caps.set(v, Math.max(caps.get(v) ?? 0, cap));
      }
    }
  });
  let before = 0, after = 0;
  for (const [tex, cap] of caps) {
    const img = tex.image as ImageBitmap | HTMLImageElement | undefined;
    const drawable = (typeof ImageBitmap !== 'undefined' && img instanceof ImageBitmap) || img instanceof HTMLImageElement;
    if (!drawable || !img.width || !img.height) continue;
    let w = img.width, h = img.height;
    before += w * h;
    const long = Math.max(w, h) / Math.min(w, h) >= 2.5;
    const limit = long ? cap * 4 : cap;
    if (Math.max(w, h) <= limit) {
      after += w * h;
      continue;
    }
    // halve step by step: each step averages 2 x 2 pixels, which keeps fine
    // detail better than one big jump
    let src: CanvasImageSource = img;
    while (Math.max(w, h) > limit) {
      w = Math.max(1, w >> 1);
      h = Math.max(1, h >> 1);
      const c = document.createElement('canvas');
      c.width = w;
      c.height = h;
      const ctx = c.getContext('2d')!;
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(src, 0, 0, w, h);
      src = c;
    }
    after += w * h;
    if (img instanceof ImageBitmap) img.close();
    tex.image = src;
    tex.needsUpdate = true;
  }
  const mb = (px: number) => Math.round((px * 4 * 1.33) / 1048576);
  console.info(`[baby] textures fitted for this device: ~${mb(before)} MB → ~${mb(after)} MB`);
}
