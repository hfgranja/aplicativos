import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://ms-001-identity:8001',
        changeOrigin: true,
        configure: (proxy, options) => {
          // Route /api/v1/auth → ms-001, rest → api-gateway pattern
        },
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
