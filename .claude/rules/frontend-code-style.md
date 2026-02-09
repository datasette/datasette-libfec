# Frontend Code Style

## Database Queries

Always use the `query()` function from `src/api.ts` for database queries. Never use direct `fetch()` calls for SQL queries.

```typescript
import { query } from '../../api';

// With parameters (preferred for dynamic values)
const results = await query(
  dbName,
  'SELECT * FROM users WHERE id = :id',
  { id: "123" }
);

// Without parameters
const results = await query(dbName, 'SELECT * FROM users LIMIT 10');
```

Parameters are passed as URL query params and use `:name` syntax in SQL.

## Svelte 5 Runes

```typescript
// Props
let { formData, filingId }: Props = $props();

// State
let loading = $state(true);

// Derived
const total = $derived(items.reduce(...));
```

## Stores

```typescript
// One-time read
import { get } from 'svelte/store';
const dbName = get(databaseName);

// Reactive subscription
$: reactiveValue = $storeName;
```

Parent sets database name from pageData, children read:

```typescript
// Parent
import { databaseName as databaseNameStore } from './stores';
databaseNameStore.set(pageData.database_name);

// Child
import { get } from 'svelte/store';
import { databaseName } from '../../stores';
const dbName = get(databaseName);
```

## Component Organization

Complex forms use subdirectories:

```
forms/
├── F3/
│   ├── F3.svelte
│   ├── StateContributors.svelte
│   └── TopPayees.svelte
├── F1.svelte
```

## Entity Page Layout

All entity pages (Candidate, Committee, Contest) follow this structure:

```
1. Breadcrumb (FEC Data → Contest → Entity)
2. Title row: h1 with name + badge | FEC.gov link (right-aligned)
3. Subtitle: one-line description
4. Main content (filings table)
5. Footer info (address, related entities) - gray text, border-top separator
```

Keep layouts flat - avoid nested boxes/sections.
