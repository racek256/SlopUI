import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import svgr from 'vite-plugin-svgr'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')   // reads root .env (same place envDir points to)

  return {
    envDir: '..',
    define: {
	  'import.meta.env.VITE_DEMO_MODE': JSON.stringify(env.DEMO_MODE === 'true'),
    },
    plugins: [react(), tailwindcss(), svgr()],
    server: {
      allowedHosts: ['dev.racek.xyz'],
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})
