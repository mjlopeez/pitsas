import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El proxy evita CORS y deja que el front use rutas relativas:
// asi el mismo build funciona en dev (5173) y servido por FastAPI (8000).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/ingest': 'http://127.0.0.1:8000',
      '/admin': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
