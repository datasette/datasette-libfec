# Adding New Pages

Complete checklist for adding a new page to the application:

## 1. Backend (Python)

### page_data.py
- Add a new Pydantic model class (e.g., `MyPageData(BaseModel)`)
- Add the model to the `__exports__` list at the bottom

### routes_pages.py
- Import the new model from `page_data`
- Add a route handler with `@router.GET("/-/libfec/my-page$")`
- Use `@check_permission()` for read-only pages or `@check_write_permission()` for write pages
- Return `Response.html()` with:
  - Template: `"libfec_base.html"`
  - `page_title`: Display title for the page
  - `entrypoint`: Path to TypeScript entry point (e.g., `"src/my_page_view.ts"`)
  - `page_data`: Result of `page_data.model_dump()`

## 2. Frontend (TypeScript/Svelte)

### vite.config.ts
Add entry point to `rollupOptions.input`:
```typescript
my_page: "src/my_page_view.ts",
```

### src/my_page_view.ts (create)
Entry point that mounts the Svelte component:
```typescript
import { mount } from 'svelte';
import MyPage from './MyPage.svelte';

const app = mount(MyPage, {
  target: document.getElementById('app-root')!,
});

export default app;
```

### src/MyPage.svelte (create)
Main component. Use `loadPageData<MyPageData>()` to access page data.

## 3. Build Steps

After making changes:
1. `just types` - Generate TypeScript types from Pydantic models
2. `just frontend` - Build the frontend bundle
3. `just check` - Verify types pass
4. `just format` - Format code
