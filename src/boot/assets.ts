import sizes from 'virtual:asset-sizes';

/**
 * Streaming downloads with byte-level progress. Everything the page needs is
 * fetched up front (the loading screen stays honest and later toggles are
 * instant): the car, HDRIs, textures, sounds.
 */
export type ProgressFn = (loaded: number, total: number) => void;

const base = import.meta.env.BASE_URL;

export function assetUrl(path: string) {
  return `${base}${path}`;
}

export function expectedBytes(path: string) {
  return (sizes as Record<string, number>)[path] ?? 0;
}

export async function fetchBytes(path: string, onProgress?: ProgressFn): Promise<ArrayBuffer> {
  const res = await fetch(assetUrl(path));
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  // a compressed response's Content-Length is the wire size, not the body size;
  // the build-time size is the size of the decoded body we actually count
  const known = expectedBytes(path);
  const header = Number(res.headers.get('content-length') || 0);
  const encoded = !!res.headers.get('content-encoding');
  const total = known || (!encoded && header) || 0;
  if (!res.body || !onProgress) {
    const buf = await res.arrayBuffer();
    onProgress?.(buf.byteLength, buf.byteLength);
    return buf;
  }
  const reader = res.body.getReader();
  const chunks: Uint8Array[] = [];
  let loaded = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    loaded += value.byteLength;
    onProgress(loaded, Math.max(total, loaded));
  }
  const out = new Uint8Array(loaded);
  let off = 0;
  for (const c of chunks) {
    out.set(c, off);
    off += c.byteLength;
  }
  onProgress(loaded, loaded);
  return out.buffer;
}

/** Decode an image into an ImageBitmap-backed element for THREE textures. */
export async function fetchImage(path: string, onProgress?: ProgressFn): Promise<HTMLImageElement> {
  const buf = await fetchBytes(path, onProgress);
  const type = path.endsWith('.png') ? 'image/png' : path.endsWith('.webp') ? 'image/webp' : 'image/jpeg';
  const url = URL.createObjectURL(new Blob([buf], { type }));
  const img = new Image();
  img.decoding = 'async';
  img.src = url;
  await img.decode();
  return img;
}
