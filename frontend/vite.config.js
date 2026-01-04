import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/detect_image': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/live_feed': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/video_feed': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
