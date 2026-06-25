import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import fs from 'fs'

/**
 * Vite plugin to fix Rolldown's broken CJS interop for es-toolkit/compat.
 *
 * Rolldown's __commonJSMin wrapper creates self-referencing variable declarations
 * like `var require_isUnsafeProperty = require_isUnsafeProperty()` which throws
 * "r is not a function" at runtime. This plugin redirects es-toolkit/compat/*
 * imports (which are CJS) to their ESM equivalents in dist/compat/.
 */
function esToolkitCompatFix() {
  const compatDir = path.resolve(__dirname, 'node_modules/es-toolkit/dist/compat')
  const compatModules = new Map()

  // Build a map of all compat modules to their ESM paths and export names
  if (fs.existsSync(compatDir)) {
    const categories = fs.readdirSync(compatDir, { withFileTypes: true })
    for (const cat of categories) {
      if (!cat.isDirectory()) continue
      const catDir = path.join(compatDir, cat.name)
      const files = fs.readdirSync(catDir)
      for (const file of files) {
        if (file.endsWith('.mjs')) {
          const modName = file.replace('.mjs', '')
          const fullPath = path.join(catDir, file)
          // Read the file to find the export name
          const content = fs.readFileSync(fullPath, 'utf-8')
          const exportMatch = content.match(/export\s*\{\s*(\w+)/)
          const exportName = exportMatch ? exportMatch[1] : modName
          compatModules.set(modName, { path: fullPath, exportName })
        }
      }
    }
  }

  return {
    name: 'es-toolkit-compat-fix',
    enforce: 'pre',
    resolveId(source) {
      // Intercept es-toolkit/compat/<name> imports
      const match = source.match(/^es-toolkit\/compat\/(\w+)$/)
      if (match && compatModules.has(match[1])) {
        return `es-toolkit-compat-fix:${match[1]}`
      }
      return null
    },
    load(id) {
      if (!id.startsWith('es-toolkit-compat-fix:')) return null
      const modName = id.replace('es-toolkit-compat-fix:', '')
      const mod = compatModules.get(modName)
      if (!mod) return null
      // Create a virtual module that re-exports the named export as default
      return `export { ${mod.exportName} as default } from ${JSON.stringify(mod.path)};\n`
    },
  }
}

export default defineConfig(({ mode }) => ({
  plugins: [
    esToolkitCompatFix(),
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
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
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