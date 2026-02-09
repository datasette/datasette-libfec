# Backend Patterns

## Background Task Lazy Init

Don't start asyncio tasks in startup hook - event loop may not be ready. Start on first HTTP request:

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

## Response JSON

Use `model.model_dump()` not `model.model_dump_json()` with `Response.json()` to avoid double encoding.

```python
# Correct
return Response.json(page_data.model_dump())

# Wrong - double encodes
return Response.json(page_data.model_dump_json())
```
