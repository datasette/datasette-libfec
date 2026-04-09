

types-routes: 
  uv run python -c 'from datasette_libfec import router; import json;print(json.dumps(router.openapi_document_json()))' \
    | npx --prefix frontend openapi-typescript > frontend/api.d.ts

types-pagedata:
  uv run scripts/typegen-pagedata.py

types:
  just types-routes
  just types-pagedata

types-watch:
  watchexec \
    -e py \
    --clear -- \
      just types

DEV_PORT := "5170"

frontend *flags:
    npm run build --prefix frontend {{flags}}

frontend-dev *flags:
    npm run dev --prefix frontend -- --port {{DEV_PORT}} {{flags}}

format-frontend *flags:
    npm run format --prefix frontend {{flags}}

format-frontend-check *flags:
    npm run format:check --prefix frontend {{flags}}

format-backend *flags:
    uv run ruff format {{flags}}

format-backend-check *flags:
    uv run ruff format --check {{flags}}

format:
    just format-backend
    just format-frontend

format-check:
    just format-backend-check
    just format-frontend-check

check-frontend:
    npm run check --prefix frontend

check-backend:
    uvx ty check

check:
    just check-backend
    just check-frontend

test *flags:
    uv run pytest {{flags}}

dev *flags:
  DATASETTE_SECRET=abc123 uv run \
    --no-cache --group alerts \
    --with ../datasette-sidebar \
    --with ../datasette-alerts \
    --with ../datasette-cron \
    --with ../datasette-alerts-discord \
    --with ../datasette-alerts-slack \
    --with ../datasette-alerts-ntfy \
      datasette \
        -s permissions.datasette_libfec_access true \
        -s permissions.datasette-sidebar-access true \
        -s permissions.datasette_libfec_write true \
        -s permissions.datasette-alerts-access true \
        -s permissions.datasette-cron-access true \
        {{flags}}

dev-with-hmr *flags:
  DATASETTE_LIBFEC_VITE_PATH=http://localhost:{{DEV_PORT}}/ \
  watchexec \
    --stop-signal SIGKILL \
    -e py,html \
    --ignore '*.db' \
    --restart \
    --clear -- \
    just dev {{flags}}