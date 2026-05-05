# Minimal example

A todo list with turbo-stream append + remove — the simplest possible `fastapi-hotwire` integration.

## Run

```bash
cd examples/minimal
uv run --with fastapi-hotwire --with uvicorn uvicorn app:app --reload
```

Then open http://127.0.0.1:8000.

## What it shows

- `templates.render_stream(...)` to append a new row without a full-page reload.
- `TurboStreamResponse(streams.remove(target=...))` to remove a row by id.
- `{% block todo_row scoped %}` is reused both as the page-level loop body and as the partial that the stream renders.
