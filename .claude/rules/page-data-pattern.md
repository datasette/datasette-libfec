# Page Data Pattern

All pages use a unified template with typed page data passed from Python to Svelte.

## Flow

1. **Python Pydantic model** defines the data shape
2. **Route** renders `libfec_base.html` with `page_data`
3. **Template** embeds data as `<script type="application/json" id="pageData">`
4. **Svelte component** loads and types the data

## Python Route

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

## Svelte Component

```typescript
import type { CandidatePageData } from "./page_data/CandidatePageData.types.ts";
import { loadPageData } from "./page_data/load.ts";

const pageData = loadPageData<CandidatePageData>();
```

## Conventions

- Use snake_case for all property names (Python and JS/TS)
- TypeScript types mirror Pydantic models
- Handle optional fields with `?.` and `??` in templates
- All entry points mount to `#app-root`
