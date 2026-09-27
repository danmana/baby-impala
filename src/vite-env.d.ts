/// <reference types="vite/client" />

declare module 'virtual:asset-sizes' {
  /** public/ path -> [bytes, content hash] */
  const assets: Record<string, [number, string]>;
  export default assets;
}
