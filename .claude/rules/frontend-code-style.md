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

```typescript
// Wrong - do not use direct fetch
const response = await fetch(`/${dbName}.json?sql=${encodeURIComponent(sql)}&_shape=array`);
```
