import { defineConfig, type Plugin } from 'vite';
import { readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

/**
 * Exposes the byte size of every file in public/ as `virtual:asset-sizes`, so
 * the loader can show honest download progress even when the CDN compresses a
 * response and drops its Content-Length.
 */
function assetSizes(): Plugin {
  const id = 'virtual:asset-sizes';
  const resolved = '\0' + id;
  const walk = (dir: string, root: string, out: Record<string, number>) => {
    for (const name of readdirSync(dir)) {
      const p = join(dir, name);
      const st = statSync(p);
      if (st.isDirectory()) walk(p, root, out);
      else out[relative(root, p).split('\\').join('/')] = st.size;
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
