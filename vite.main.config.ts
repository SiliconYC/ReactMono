import { resolve } from 'node:path';
import { defineConfig } from 'vite';

export default defineConfig({
  root: resolve('site'),
  base: './',
  publicDir: false,
  server: { host: '127.0.0.1', port: 23010, strictPort: true },
  build: {
    outDir: resolve('dist'),
    emptyOutDir: false,
    chunkSizeWarningLimit: 1400,
    rollupOptions: { input: { main: resolve('site/index.html'), visualLab: resolve('site/visual-lab.html') } }
  }
});
