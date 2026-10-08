// @ts-check
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

// https://astro.build/config
export default defineConfig({
  site: "https://www.emmavellard.com",
  integrations: [sitemap()],
  security: {
    // Emits a per-page CSP <meta> with hashes for Astro's inline scripts and styles.
    csp: true,
  },
});
