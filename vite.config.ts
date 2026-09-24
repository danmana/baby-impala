import { defineConfig } from 'vite';

export default defineConfig({
  server: { host: true, port: 5177 },
  build: {
    target: 'es2022',
    chunkSizeWarningLimit: 1500,
  },
});
