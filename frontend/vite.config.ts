import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { readFileSync, writeFileSync } from "fs";
import {compile} from "json-schema-to-typescript";

// https://vite.dev/config/
export default defineConfig({
  server: {
    cors: {
      origin: ["http://localhost:8004", "http://127.0.0.1:8004"],
    },
  },
  plugins: [
    svelte(),
    {
      name: "page-data-types",
      async handleHotUpdate({ file, server }) {
        console.log("File changed:", file);
        if (!file.endsWith("_schema.json")) return;

        const outFile = file.replace("_schema.json", ".types.ts")

      const schema = JSON.parse(readFileSync(file, "utf-8"));
      let ts = await compile(schema, "", undefined);

      writeFileSync(outFile, ts);

      // Tell Vite this file changed → HMR
      const mod = server.moduleGraph.getModuleById(outFile)
      if (mod) {
        server.moduleGraph.invalidateModule(mod)
        return [mod]
      }
      }
    }
  ],
  build: {
    manifest: "manifest.json",
    outDir: "../datasette_libfec",
    assetsDir: "static/gen",
    rollupOptions: {
      input: {
        index: "src/index_view.ts",
        filing_detail: "src/filing_detail_view.ts",
        contest: "src/contest_view.ts",
        candidate: "src/candidate_view.ts",
        committee: "src/committee_view.ts",
      },
    },
  },
});
