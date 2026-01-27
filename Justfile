

types: 
  uv run python -c 'from datasette_libfec import router; import json;print(json.dumps(router.openapi_document_json()))' \
    | npx --prefix frontend openapi-typescript > frontend/api.d.ts

types-watch:
  watchexec \
    -e py \
    --clear -- \
      just types

frontend *flags:
    npm run build --prefix frontend {{flags}}

frontend-dev *flags:
    npm run dev --prefix frontend -- --port 5177 {{flags}}

dev *flags:
  uv run datasette -p 8004 tmp.db {{flags}}

dev-with-hmr *flags:
  DATASETTE_LIBFEC_VITE_PATH=http://localhost:5177/ \
  watchexec \
    --stop-signal SIGKILL \
    -e py,html \
    --ignore '*.db' \
    --restart \
    --clear -- \
    just dev {{flags}}