import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,  // Porta do frontend
    proxy: {
      '/api': {
        target: 'http://localhost:5000',  // Backend
        changeOrigin: true,
        secure: false,
      },
    },
  },
});