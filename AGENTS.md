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

**Background Tasks:**
- RSS watcher runs as asyncio task, checking FEC RSS feed at configurable intervals
- Supports state filtering (e.g., "CA" for California only)
- Cover-only mode for faster imports
- Configurable check interval (default: 60 seconds)

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

**Vite Config:**
- Entry: `src/index_view.ts`
- Output: `../datasette_libfec/static/gen/` + `manifest.json`
- Dev server: Port 5177 with CORS for localhost:8004
- Plugin: @sveltejs/vite-plugin-svelte

## Development Workflow

**With HMR (Recommended):**
```bash
# Terminal 1: Vite dev server
just frontend-dev

# Terminal 2: Datasette with HMR
just dev-with-hmr
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
- `datasette_libfec/manifest.json` - Generated Vite manifest (gitignored)
- `datasette_libfec/static/gen/` - Generated frontend assets (gitignored)

## How Vite Integration Works

### Development Mode
When `DATASETTE_LIBFEC_VITE_PATH=http://localhost:5177/` is set:
```html
<script type="module" src="http://localhost:5177/@vite/client"></script>
<script type="module" src="http://localhost:5177/src/import.tsx"></script>
```
Changes to frontend files hot reload without page refresh.

### Production Mode
Without env var, reads `manifest.json` to inject hashed bundles:
```html
<link rel="stylesheet" href="/-/static-plugins/datasette_libfec/gen/import-[hash].css">
<script type="module" src="/-/static-plugins/datasette_libfec/gen/import-[hash].js"></script>
```

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

## Page Data Pattern

All pages use a single unified template (`libfec_base.html`) with typed page data:

**1. Python Pydantic model** (`datasette_libfec/page_data.py`):
```python
class CandidatePageData(BaseModel):
    candidate_id: str
    cycle: int
    candidate: Candidate | None = None
    filings: list[Filing] = []
    error: str | None = None
```

**2. Route uses unified template** (`routes_pages.py`):
```python
page_data = CandidatePageData(candidate_id=candidate_id, ...)
return Response.html(
    await datasette.render_template(
        "libfec_base.html",
        {
            "page_title": f"{candidate_name} - Candidate",
            "entrypoint": "src/candidate_view.ts",
            "page_data": page_data.model_dump(),
        }
    )
)
```

**3. Unified template** (`templates/libfec_base.html`):
```html
{% extends "base.html" %}
{% block title %}{{ page_title }}{% endblock %}
{% block extra_head %}
{{ datasette_libfec_vite_entry(entrypoint) | safe }}
<script type="application/json" id="pageData">{{ page_data | tojson }}</script>
{% endblock %}
{% block content %}
<div id="app-root"></div>
{% endblock %}
```

**4. TypeScript types** (`frontend/src/page_data/CandidatePageData.types.ts`):
```typescript
export interface CandidatePageData {
  candidate_id: string;
  cycle: number;
  candidate?: Candidate | null;
  ...
}
```

**5. Shared loader** (`frontend/src/page_data/load.ts`):
```typescript
export function loadPageData<T>(): T {
  const script = document.querySelector<HTMLScriptElement>('#pageData');
  return JSON.parse(script.textContent || '{}') as T;
}
```

**6. Svelte component** (`Candidate.svelte`):
```typescript
import type { CandidatePageData } from "./page_data/CandidatePageData.types.ts";
import { loadPageData } from "./page_data/load.ts";

const pageData = loadPageData<CandidatePageData>();
```

**7. Entry point** (`candidate_view.ts`):
```typescript
const app = mount(Candidate, {
  target: document.getElementById('app-root')!,
})
```

**Key conventions:**
- All pages use `libfec_base.html` template
- Page data is embedded as `<script type="application/json" id="pageData">`
- All entry points mount to `#app-root`
- Use snake_case for all property names (Python and JS/TS)
- TypeScript types mirror Pydantic models
- Handle optional fields with `?.` and `??` in Svelte templates
- Run `npm run check` to verify TypeScript correctness

## Testing

Run tests with:
```bash
pytest
```

Test file: `tests/test_libfec.py`

## UI Patterns

### Page Layout

All entity pages (Candidate, Committee, Contest) follow this structure:

```
1. Breadcrumb (FEC Data → Contest → Entity)
2. Title row: h1 with name + badge | FEC.gov link (right-aligned)
3. Subtitle: one-line description
4. Main content (filings table)
5. Footer info (address, related entities) - gray text, border-top separator
```

Keep layouts flat - avoid nested boxes/sections.

### Svelte 5 Patterns

```typescript
// Props
let { formData, filingId }: Props = $props();

// State
let loading = $state(true);

// Derived
const total = $derived(items.reduce(...));

// Stores - use get() for one-time reads, $ prefix for reactive
import { get } from 'svelte/store';
const dbName = get(databaseName);  // one-time
$: reactiveValue = $storeName;     // reactive
```

### Database Name Store

For client-side SQL queries, use the store from `stores.ts`:

```typescript
// Parent sets it from pageData
import { databaseName as databaseNameStore } from './stores';
databaseNameStore.set(pageData.database_name);

// Child reads it
import { get } from 'svelte/store';
import { databaseName } from '../../stores';
import { query } from '../../api';
const dbName = get(databaseName);
const results = await query(dbName, 'SELECT * FROM ...');
```

### Component Organization

For complex forms, use subdirectories:

```
forms/
├── F3/
│   ├── F3.svelte           # Main component
│   ├── StateContributors.svelte
│   └── TopPayees.svelte
├── F1.svelte
```

Import: `import F3 from './forms/F3/F3.svelte';`

## Backend Patterns

### Background Task Lazy Init

Don't start tasks in startup hook - event loop may not be ready. Start on first HTTP request:

```python
# startup hook - just store config
rss_watcher.set_config(interval)

# route handler - actually start
def ensure_started(self):
    if self._initialized:
        return
    loop = asyncio.get_running_loop()
    self._task = loop.create_task(self._run_loop())
```

### Response JSON

Use `model.model_dump()` not `model.model_dump_json()` with `Response.json()` to avoid double encoding.

## Frontend Patterns

### Database Queries

**Always use the `query()` function from `api.ts` for database queries.** Never use direct `fetch()` calls for SQL queries.

```typescript
// ✅ Correct - use api.ts
import { query } from '../../api';
const results = await query(dbName, 'SELECT * FROM table WHERE id = ?');

// ❌ Wrong - direct fetch
const response = await fetch(`/${dbName}.json?sql=${encodeURIComponent(sql)}&_shape=array`);
const results = await response.json();
```

The `query()` function:
- Handles URL encoding and query parameters
- Returns properly typed results
- Provides a consistent interface across the codebase
