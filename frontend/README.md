# Frontend Development

This frontend is built with Vite + Svelte 5 and supports Hot Module Replacement (HMR) for development.

## Development Workflow

### Option 1: Development with HMR (Recommended)

Run these two commands in separate terminals:

```bash
# Terminal 1: Vite dev server
just frontend-dev

# Terminal 2: Datasette with HMR enabled
just dev-with-hmr
```

Or use the combined command (requires `watchexec`):

```bash
# Combined: Auto-restart Datasette on Python changes + HMR for frontend
just dev-with-hmr
```

Then open your browser to http://localhost:8004/-/libfec and edit files in `frontend/src/` - changes will hot reload instantly!

### Option 2: Production Build

Build the frontend and run Datasette normally:

```bash
# Build frontend
just frontend

# Run Datasette
just dev
```

## How It Works

### Development Mode (HMR)

When `DATASETTE_LIBFEC_VITE_PATH` environment variable is set, the plugin injects Vite's dev server scripts into the HTML:

```html
<script type="module" src="http://localhost:5177/@vite/client"></script>
<script type="module" src="http://localhost:5177/src/index_view.ts"></script>
```

This enables Hot Module Replacement - as you edit files, Vite will update them in the browser without a full page reload.

### Production Mode

Without the environment variable, the plugin uses Vite's `manifest.json` to load hashed production bundles:

```html
<script type="module" src="/-/static-plugins/datasette_libfec/gen/import-[hash].js"></script>
```

## Scripts

- `npm run dev` - Start Vite dev server (port 5177)
- `npm run build` - Production build (outputs to `../datasette_libfec/`)
- `npm run preview` - Preview production build locally
- `npm run check` - TypeScript type checking

## Type Generation

Generate TypeScript types from the OpenAPI schema:

```bash
just types
```

This will update `frontend/api.d.ts` with type-safe API types for the backend endpoints.

## File Structure

```
frontend/
├── src/
│   ├── LibfecIndex.svelte # Main index page component
│   └── index_view.ts      # Entry point (mounts component)
├── api.d.ts               # Generated OpenAPI types
├── vite.config.ts         # Vite configuration
├── svelte.config.js       # Svelte preprocessor config
├── tsconfig.json          # TypeScript project references
├── tsconfig.app.json      # App code TypeScript config
├── tsconfig.node.json     # Build config TypeScript config
└── package.json           # Dependencies and scripts
```
