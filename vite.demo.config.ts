import { defineConfig } from 'vite';

export default defineConfig({
  root: 'demo3d',
  base: './',
  server: {
    host: '127.0.0.1',
    port: 4173,
    strictPort: true
  },
  build: {
    outDir: '../dist-3d-demo',
    emptyOutDir: true,
    chunkSizeWarningLimit: 1200
  }
});

