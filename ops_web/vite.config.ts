import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/ops/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/ops/api': {
        target: 'http://127.0.0.1:8444',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
  },
})
