import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    // Ensure we use HTTPS in production
    __API_BASE_URL__: JSON.stringify(process.env.VITE_API_BASE_URL)
  },
  server: {
    port: 3000,
    host: '0.0.0.0', // Allow connections from any host
    cors: true,
    hmr: {
      port: 3000,
      host: 'localhost'
    },
    proxy: {
      // Proxy auth requests to the Griot backend
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true // Enable WebSocket proxy for HMR
      },
      // Proxy API requests to the Griot backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true // Enable WebSocket proxy for HMR
      },
      // Proxy MCP requests to the Griot backend
      '/mcp': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true // Enable WebSocket proxy for HMR
      },
      // Proxy Pollinations requests to the Griot backend (routes to /api/v1/pollinations)
      '/pollinations': {
        target: 'http://localhost:8000/api/v1',
        changeOrigin: true,
        secure: false,
        ws: true // Enable WebSocket proxy for HMR
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  },
  resolve: {
    alias: {
      '@': '/src'
    }
  }
})