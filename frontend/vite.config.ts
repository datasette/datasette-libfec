import { defineConfig } from "vite";
import preact from "@preact/preset-vite";

// https://vite.dev/config/
export default defineConfig({
  server: {
    cors: {
      origin: ["http://localhost:8004", "http://127.0.0.1:8004"],
    },
  },
  plugins: [preact()],
  build: {
    manifest: "manifest.json",
    outDir: "../datasette_libfec",
    assetsDir: "static/gen",
    rollupOptions: {
      input: {
        import: "src/import.tsx",
      },
    },
  },
});
