import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
	plugins: [svelte()],
	server: {
		port: 5173,
		proxy: {
			'/auth': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false
			},
			'/jobs': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false
			},
			'/extract-skills': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false
			},
			'/process-multiple': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false
			},
			'/hybrid-search': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false
			},
			'/process-single': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false
			}
		}
	}
})
