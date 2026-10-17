import { defineConfig } from 'vite';

export default defineConfig({
  root: 'demo3d',
  base: './',
  build: {
    outDir: '../dist-3d-demo',
    emptyOutDir: true,
    chunkSizeWarningLimit: 1200
  }
});

