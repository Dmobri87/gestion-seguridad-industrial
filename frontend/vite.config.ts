import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Dividir el bundle en chunks para carga paralela
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor core — React
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          // Vendor UI — Ant Design (el más pesado)
          'vendor-antd': ['antd', '@ant-design/icons'],
          // Vendor charts
          'vendor-charts': ['@ant-design/charts'],
          // Vendor utils
          'vendor-utils': ['axios', 'dayjs', 'zustand'],
        },
      },
    },
    // Umbral de advertencia de chunks (kb)
    chunkSizeWarningLimit: 800,
    // Minificación con esbuild (por defecto, más rápido)
    minify: 'esbuild',
    // Source maps en producción desactivados (seguridad)
    sourcemap: false,
    // Comprimir assets
    assetsInlineLimit: 4096,
  },
})
