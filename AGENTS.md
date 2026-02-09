# datasette-libfec

A Datasette plugin for importing FEC (Federal Election Commission) data using the libfec CLI tool.

## Architecture

**Backend:** Python + Datasette + datasette-plugin-router
**Frontend:** TypeScript + Svelte 5 + Vite (with HMR support)
**Build Tool:** Just (Justfile)

## Backend

**Location:** `datasette_libfec/`

- `__init__.py` - Plugin hooks, Vite manifest integration, template vars
- `routes.py` - API routes (not currently in use, routes defined in `__init__.py`)
- `templates/libfec.html` - Main UI template

**Key Classes:**
- `LibfecClient` - Wrapper for libfec CLI tool
- `RssWatcherState` - State management for background RSS watching
- `ManifestChunk` - Pydantic model for Vite manifest parsing

**API Endpoints:**
- `GET /-/libfec` - Main UI page
- `POST /-/api/libfec` - Import FEC data (accepts committee/candidate/contest + ID + cycle)
- `POST /-/api/libfec/rss/start` - Start RSS watcher (state, cover_only, interval)
- `POST /-/api/libfec/rss/stop` - Stop RSS watcher
- `GET /-/api/libfec/rss/status` - Get RSS watcher status

**Environment Variables:**
- `DATASETTE_LIBFEC_VITE_PATH` - Points to Vite dev server for HMR (e.g., `http://localhost:5177/`)
- `DATASETTE_LIBFEC_BIN_PATH` - Override path to libfec binary (defaults to `<python-executable-dir>/libfec`)

## Frontend

**Location:** `frontend/`

**Tech Stack:**
- Svelte 5 (with runes/signals for reactivity)
- TypeScript with strict mode
- Vite 7 for dev server + bundling
- openapi-fetch for type-safe API calls

**Structure:**
```
frontend/
├── src/
│   ├── LibfecIndex.svelte # Main index page component
│   └── index_view.ts      # Entry point (mounts component)
├── api.d.ts               # Generated OpenAPI types
├── vite.config.ts         # Vite config (builds to ../datasette_libfec/)
├── svelte.config.js       # Svelte preprocessor config
├── tsconfig.json          # TS project references
├── tsconfig.app.json      # App code config
└── package.json           # Scripts: dev, build, preview, check
```

## Development Workflow

**With HMR (Recommended):**
```bash
just frontend-dev  # Terminal 1: Vite dev server
just dev-with-hmr  # Terminal 2: Datasette with HMR
```

**Production Build:**
```bash
just frontend  # Build frontend
just dev       # Run Datasette
```

**Type Generation:**
```bash
just types  # Generate frontend/api.d.ts from OpenAPI schema
```

## Just Commands

| Command | Description |
|---------|-------------|
| `just types` | Generate TypeScript types from OpenAPI schema |
| `just types-watch` | Watch and regenerate types on Python changes |
| `just frontend` | Build production frontend bundle |
| `just frontend-dev` | Start Vite dev server (port 5177) |
| `just dev` | Run Datasette on port 8004 |
| `just dev-with-hmr` | Run Datasette with HMR + auto-restart on file changes |

## Key Files

- `pyproject.toml` - Python package config, dependencies
- `Justfile` - Build commands and workflows
- `frontend/vite.config.ts` - Vite bundler configuration
- `datasette_libfec/__init__.py` - Plugin entry point, Vite integration

## Testing

```bash
pytest
```

Test file: `tests/test_libfec.py`

## Dependencies

**Backend:**
- datasette >= 1.0a23
- datasette-plugin-router
- pydantic >= 2.0
- libfec (external CLI tool, must be in PATH)

**Frontend:**
- svelte ^5.43.8
- vite ^7.2.4
- @sveltejs/vite-plugin-svelte ^6.2.1
- openapi-fetch ^0.15.0
- typescript ~5.9.3
- svelte-check ^4.3.4
