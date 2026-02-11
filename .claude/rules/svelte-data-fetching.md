# Svelte Data Fetching

## Database Queries

Use the `query()` function from `api.ts` for all SQL queries:

```typescript
import { query } from './api.ts';

const results = await query(
  pageData.database_name,
  'SELECT * FROM libfec_candidates WHERE state = :state',
  { state: 'CA' }
);
```

## Async State Management with useQuery

Use `useQuery()` from `useQuery.svelte.ts` for async data:

```typescript
import { useQuery } from './useQuery.svelte.ts';

async function fetchData() {
  return await query(dbName, 'SELECT ...');
}

const result = useQuery(fetchData);

// Access in template:
// result.isLoading - boolean
// result.data - the fetched data
// result.error - error message if failed
// result.refetch?.() - function to refetch
```

## Reactive Refetching

Use `$effect` to refetch when filter state changes:

```typescript
let filterValue = $state('default');

const result = useQuery(fetchData);

$effect(() => {
  // Access reactive variables to track them
  filterValue;

  result.refetch?.();
});
```

## Derived/Computed Data

Use `$derived` for sorted or transformed data:

```typescript
let sortColumn = $state('name');
let sortDirection = $state<'asc' | 'desc'>('asc');

const sortedData = $derived(() => {
  if (!result.data) return [];

  return [...result.data].sort((a, b) => {
    // sorting logic
  });
});

// Use in template as sortedData() - it's a function
{#each sortedData() as item}
```

## Pattern for Filterable Tables

```typescript
// Filter state
let filter1 = $state('');
let filter2 = $state('');

// Sort state
let sortColumn = $state<keyof DataType>('default_column');
let sortDirection = $state<'asc' | 'desc'>('desc');

// Query function that reads filter state
function buildQuery() {
  const params: Record<string, string> = {};
  let sql = 'SELECT ...';

  if (filter1) {
    sql += ' WHERE col1 = :filter1';
    params.filter1 = filter1;
  }

  return { sql, params };
}

async function fetchData() {
  const { sql, params } = buildQuery();
  return await query(dbName, sql, params);
}

const result = useQuery(fetchData);

// Refetch on filter change
$effect(() => {
  filter1;
  filter2;
  result.refetch?.();
});

// Sorted view
const sortedData = $derived(() => {
  // sorting logic
});
```
