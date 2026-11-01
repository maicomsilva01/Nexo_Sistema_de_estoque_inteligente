import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  root: 'frontend',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    allowedHosts: ['.us1.manus.computer', '.us5.manus.computer', 'localhost', '127.0.0.1'],
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/_app': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: '../frontend/dist',
    emptyOutDir: true,
  },
});
