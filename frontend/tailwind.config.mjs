/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
	theme: {
		extend: {
			fontFamily: {
				// Inter Variable with metric-matched fallbacks to minimise layout shift
				sans: [
					'Inter Variable',
					'Inter',
					'ui-sans-serif',
					'system-ui',
					'-apple-system',
					'BlinkMacSystemFont',
					'"Segoe UI"',
					'sans-serif',
				],
			},
			colors: {
				'primary': '#2563eb',      // blue-600
				'surface': '#1e293b',      // slate-800
				'surface-light': '#0f172a', // slate-900
				// Override gray with blue-tinted slate values for subconscious
				// brand cohesion — same lightness steps, chroma ~0.01 toward blue
				gray: {
					50:  '#f8fafc',
					100: '#f1f5f9',
					200: '#e2e8f0',
					300: '#cbd5e1',
					400: '#94a3b8',
					500: '#64748b',
					600: '#475569',
					700: '#334155',
					800: '#1e293b',
					900: '#0f172a',
					950: '#020617',
				},
			},
			spacing: {
				'touch': '3rem', // 48px - min touch target
			},
		},
	},
	plugins: [],
}
