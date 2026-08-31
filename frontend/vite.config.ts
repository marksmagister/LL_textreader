import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    // the FastAPI backend; keeps the frontend same-origin in dev
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
