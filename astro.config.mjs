// @ts-check
import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

import preact from '@astrojs/preact';

import cloudflare from '@astrojs/cloudflare';

// https://astro.build/config
export default defineConfig({
  vite: {
    plugins: [tailwindcss()]
  },

  server: {
    proxy: {
      '/music/audio': {
        target: 'http://127.0.0.1:8765',
        changeOrigin: true,
      }
    }
  },

  integrations: [preact()],
  adapter: cloudflare()
});