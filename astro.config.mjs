import { defineConfig } from 'astro/config';

export default defineConfig({
  // Enable strict mode for better error checking
  vite: {
    ssr: {
      external: []
    }
  }
});
