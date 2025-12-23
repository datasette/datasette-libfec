

types: 
  uv run python -c 'from datasette_libfec import router; import json;print(json.dumps(router.openapi_document_json()))' \
    | npx --prefix frontend openapi-typescript > frontend/api.d.ts

types-watch:
  watchexec \
    -e py \
    --clear -- \
      just types

frontend *flags:
    npx --prefix frontend \
    esbuild \
      --format=esm --bundle --minify \
      --jsx-factory=h \
      --jsx-fragment=Fragment \
      --out-extension:.js=.min.js \
      --out-extension:.css=.min.css \
      --target=safari12 \
      {{flags}} \
      frontend/targets/import.tsx \
      --outdir=datasette_libfec/static

dev *flags:
  uv run datasette -p 8004 tmp.db {{flags}}