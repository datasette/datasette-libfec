

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

# (Re)build the small demo FEC database the doc screenshots run against.
shots-fixture:
    bash frontend/scripts/build-fixture.sh

# Regenerate committed doc screenshots → docs/screenshots/*.png. Self-contained:
# builds the frontend, boots a throwaway datasette against the fixture db, drives
# Playwright, then tears it down. Run all, or a subset by name:
#   `just shots`  /  `just shots index contest`.
shots *names:
    just frontend
    npm --prefix frontend install
    npm --prefix frontend exec -- playwright install chromium
    node frontend/scripts/screenshots.mjs {{names}}

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
    --with ../datasette-alerts-ntfy \
      datasette \
        -s permissions.datasette_libfec_access true \
        -s permissions.datasette-sidebar-access true \
        -s permissions.datasette_libfec_write true \
        -s permissions.datasette-alerts-access true \
        -s permissions.datasette-cron-access true \
        {{flags}}

dev-with-hmr *flags:
  watchexec \
    --stop-signal SIGKILL \
    -e py,html \
    --ignore '*.db' \
    --restart \
    --clear -- \
    just dev \
      -s plugins.datasette-vite.dev_ports.datasette_libfec {{DEV_PORT}} \
      {{flags}}