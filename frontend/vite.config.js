import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Das Frontend ruft das Backend immer unter /api auf. Der Dev-Server leitet das an das Backend weiter
// und entfernt dabei das Präfix: /api/books -> http://localhost:8000/books
// Vorteil: ein Ursprung, kein CORS.
const target = process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
