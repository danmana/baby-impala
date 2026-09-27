import { defineConfig, type Plugin } from 'vite';
import { createHash } from 'node:crypto';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

/**
 * Exposes the byte size of every file in public/ as `virtual:asset-sizes`, so
 * the loader can show honest download progress even when the CDN compresses a
 * response and drops its Content-Length. A short content hash per file goes
 * into each asset's URL, so a rebuilt model or sound is never served from a
 * browser cache holding the previous one.
 */
function assetSizes(): Plugin {
  const id = 'virtual:asset-sizes';
  const resolved = '\0' + id;
  type Entry = [size: number, hash: string];
  const walk = (dir: string, root: string, out: Record<string, Entry>) => {
    for (const name of readdirSync(dir)) {
      const p = join(dir, name);
      const st = statSync(p);
      if (st.isDirectory()) walk(p, root, out);
      else {
        const hash = createHash('md5').update(readFileSync(p)).digest('hex').slice(0, 10);
        out[relative(root, p).split('\\').join('/')] = [st.size, hash];
      }
    }
    return out;
  };
  return {
    name: 'asset-sizes',
    resolveId: (s) => (s === id ? resolved : undefined),
    load(s) {
      if (s !== resolved) return;
      const root = join(process.cwd(), 'public');
      return `export default ${JSON.stringify(walk(root, root, {}))};`;
    },
  };
}

export default defineConfig({
  plugins: [assetSizes()],
  server: { host: true, port: 5177 },
  build: {
    target: 'es2022',
    chunkSizeWarningLimit: 1500,
    // two pages: the car, and the write-up about how it was built
    rollupOptions: { input: { main: 'index.html', about: 'about.html' } },
  },
});
