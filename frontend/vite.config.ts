import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

// https://vite.dev/config/
export default defineConfig({
  server: {
    cors: {
      origin: ["http://localhost:8004", "http://127.0.0.1:8004"],
    },
  },
  plugins: [svelte()],
  build: {
    manifest: "manifest.json",
    outDir: "../datasette_libfec",
    assetsDir: "static/gen",
    rollupOptions: {
      input: {
        index: "src/index_view.ts",
        filing_detail: "src/filing_detail_view.ts",
      },
    },
  },
});
