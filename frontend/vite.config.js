import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Production optimizations
    target: 'es2020',
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('@monaco-editor')) return 'editor'
          if (id.includes('recharts')) return 'charts'
          if (id.includes('lucide-react')) return 'icons'
          if (id.includes('node_modules')) return 'vendor'
        },
      },
    },
    // Enable source maps for production error tracking
    sourcemap: mode === 'production' ? 'hidden' : true,
    // Chunk size warnings
    chunkSizeWarningLimit: 500,
    // CSS code splitting
    cssCodeSplit: true,
  },
  // Preview server for local production testing
  preview: {
    port: 3000,
    host: true,
  },
}))