# fastapi-hotwire

Hotwire ([Turbo](https://turbo.hotwired.dev/)) integration for FastAPI — turbo-stream responses, frame detection, block rendering, flash messages, and pytest helpers.

[![PyPI version](https://img.shields.io/pypi/v/fastapi-hotwire.svg)](https://pypi.org/project/fastapi-hotwire/)
[![Python versions](https://img.shields.io/pypi/pyversions/fastapi-hotwire.svg)](https://pypi.org/project/fastapi-hotwire/)
[![CI](https://github.com/danethurber/fastapi-hotwire/actions/workflows/ci.yml/badge.svg)](https://github.com/danethurber/fastapi-hotwire/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

`fastapi-hotwire` is to FastAPI what [`turbo-flask`](https://github.com/miguelgrinberg/turbo-flask) is to Flask: a small, focused library for building server-rendered apps with Hotwire, without giving up FastAPI's async/dependency-injection story or pulling in a SPA framework.

It's intentionally a thin layer. Each piece (responses, streams, templates, flash, csrf, forms, testing) is independently usable, and every integration seam — template engine, session backend — is behind a `Protocol` so you can swap it out.

## Install

```bash
pip install fastapi-hotwire
# or
uv add fastapi-hotwire
```

For the Pydantic-backed validation-error stream:

```bash
pip install "fastapi-hotwire[forms]"
```

## Quickstart

```python
from fastapi import FastAPI, Form, Request
from fastapi_hotwire import HotwireTemplates, TurboStreamResponse, streams

app = FastAPI()
templates = HotwireTemplates(directory="templates", flashes=False)
todos: list[dict] = []


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"todos": todos})


@app.post("/todos")
def create(request: Request, text: str = Form(...)):
    todo = {"id": len(todos) + 1, "text": text}
    todos.append(todo)
    return templates.render_stream(
        request, "index.html", "todo_row",
        action="append", target="todos", todo=todo,
    )


@app.post("/todos/{todo_id}/delete")
def delete(todo_id: int):
    todos[:] = [t for t in todos if t["id"] != todo_id]
    return TurboStreamResponse(streams.remove(target=f"todo-{todo_id}"))
```

A complete runnable version of this example lives in [`examples/minimal/`](examples/minimal).

## What's in the box

| Module | What it does |
| --- | --- |
| [`TurboStreamResponse`](#turbostreamresponse) | A `Response` subclass with `Content-Type: text/vnd.turbo-stream.html`. |
| [`streams`](#streams) | Pure-function builders for `<turbo-stream>` actions (`append`, `prepend`, `replace`, `update`, `remove`, `before`, `after`, `refresh`). |
| [`TurboContext`](#turbocontext) | A FastAPI dependency that summarizes how the current request relates to Turbo (frame? stream? top-level visit?). |
| [`HotwireTemplates`](#hotwiretemplates) | A `Jinja2Templates` wrapper that adds `render_block(...)` and `render_stream(...)`, plus an automatic `flashes` context processor. |
| [`flash` / `get_flashed`](#flash) | Session-backed flash messages with both a redirect-style and a Hotwire-native turbo-stream flow. |
| [`forms`](#forms) | An HMAC time-trap form token (anti-bot tripwire) and a Pydantic `ValidationError` → turbo-stream renderer. |
| [`csrf`](#csrf) | An origin/referer-checking dependency factory with per-DNS-label wildcards. |
| [`testing`](#testing) | pytest assertions and request helpers (`assert_turbo_stream`, `parse_streams`, `assert_turbo_frame`, `turbo_frame_request`, `turbo_stream_request`). |

## TurboStreamResponse

```python
from fastapi_hotwire import TurboStreamResponse, streams

@app.post("/items")
def create():
    return TurboStreamResponse([
        streams.append(item_html, target="items"),
        streams.update(counter_html, target="item-count"),
    ])
```

Pass a single string, a list of strings, or `None`. The class also works as `response_class=TurboStreamResponse` so OpenAPI documents the media type.

## streams

Each builder returns a `markupsafe.Markup` so it composes safely with Jinja templates:

```python
from fastapi_hotwire import streams

streams.append("<li>...</li>", target="todos")
streams.replace(form_html, target="contact-form")
streams.remove(target="todo-42")
streams.refresh()  # Turbo 8 page-refresh
```

The `html` argument is interpolated **verbatim** into the `<template>` envelope. It must be safe HTML (Jinja autoescaped output is safe). Attribute values (`target=`, `targets=`) are HTML-escaped automatically.

## TurboContext

```python
from typing import Annotated
from fastapi import Depends
from fastapi_hotwire import TurboContext, turbo_context

@app.post("/items")
async def create(turbo: Annotated[TurboContext, Depends(turbo_context)]):
    if turbo.is_frame:
        return frame_response(...)
    if turbo.accepts_stream:
        return stream_response(...)
    return full_page_response(...)
```

Fields: `is_frame`, `frame_id`, `accepts_stream`, `is_visit`.

## HotwireTemplates

```python
from fastapi_hotwire import HotwireTemplates

templates = HotwireTemplates(directory="templates")

@app.get("/items/{id}")
def item_frame(request: Request, id: int):
    # Render only the {% block item %} of items.html — useful for
    # responding to a <turbo-frame src="..."> request.
    return templates.render_block(request, "items.html", "item", item=load(id))

@app.post("/items")
def create(request: Request, text: str = Form(...)):
    item = save(text)
    # Render the {% block item %} as a turbo-stream that appends to #items.
    return templates.render_stream(
        request, "items.html", "item",
        action="append", target="items", item=item,
    )
```

The `flashes` context processor is registered automatically; pass `flashes=False` to opt out.

## flash

```python
from fastapi_hotwire import flash, get_flashed

# 1. Classic post-redirect-get flow:
@app.post("/save")
def save(request: Request):
    flash(request, "Saved", category="success")
    return RedirectResponse("/", status_code=303)

# 2. Hotwire-native: respond with a stream that appends to #flash without redirecting:
@app.post("/save")
def save(request: Request):
    return flash.stream(request, "Saved", category="success")
```

Templates rendered through `HotwireTemplates` automatically receive the queued `flashes` list.

A complete runnable example lives in [`examples/flash/`](examples/flash).

## forms

```python
from fastapi_hotwire.forms import make_form_token, verify_form_token, validation_error_stream

# In your form-render route, embed a fresh token:
token = make_form_token(SECRET)

# On submit, reject implausibly fast/stale submissions:
if not verify_form_token(submitted_token, SECRET, min_age=3, max_age=3600):
    raise HTTPException(403)

# Render Pydantic validation errors as a turbo-stream that replaces
# only the form's block — no full-page reload, no scroll loss.
try:
    Contact.model_validate(form_data)
except ValidationError as exc:
    return validation_error_stream(
        exc, templates=templates, template="contact.html",
        block="form", target="contact-form", request=request,
    )
```

The form token is an anti-bot tripwire, **not** a CSRF token. Pair it with `csrf.allowed_origin(...)` for state-changing endpoints. See the security note in the module docstring for what it is and isn't sized for.

## csrf

```python
from fastapi import Depends
from fastapi_hotwire import csrf

@router.post(
    "/contact",
    dependencies=[Depends(csrf.allowed_origin(
        "https://example.com",
        "https://*.example.com",   # one DNS label wildcard
    ))],
)
async def contact(...): ...
```

Wildcards consume exactly one DNS label, so `https://*.cloudfront.net` matches `https://dXXX.cloudfront.net` but not `https://evil.dXXX.cloudfront.net`. Origin is checked first, then `Referer` as a fallback.

## testing

```python
from fastapi_hotwire.testing import (
    assert_turbo_stream, parse_streams, assert_turbo_frame,
    turbo_frame_request, turbo_stream_request,
)

def test_create_appends_a_row(client):
    resp = client.post("/todos", data={"text": "ship"})
    assert_turbo_stream(resp)
    actions = parse_streams(resp)
    assert actions[0].action == "append"
    assert actions[0].target == "todos"
```

## Pluggability

`fastapi_hotwire.protocols` defines the integration seams:

- `TemplateRenderer` — anything implementing `render(name, context) -> str`.
- `BlockRenderer` — anything implementing `render_block(name, block, context) -> str`. The default `Jinja2BlockRenderer` is one implementation.
- `SessionLike` — any `MutableMapping[str, Any]` that hangs off `request.session` (Starlette `SessionMiddleware`, `starsessions`, an in-memory `dict`).

You don't need to use the bundled Jinja2 / Starlette code paths to use this library.

## Examples

Two full runnable examples live under [`examples/`](examples):

- [`examples/minimal/`](examples/minimal) — A todo list with turbo-stream append + remove. The simplest possible integration.
- [`examples/flash/`](examples/flash) — Session-backed flash messages, with both a PRG and a Hotwire-native flow.

Run either with `uv run uvicorn app:app --reload` from inside the example directory.

## Non-goals

`fastapi-hotwire` deliberately does **not**:

- Push to clients via WebSocket / SSE — Hotwire's broadcast / `turbo_stream_from` patterns belong in app code with your message bus of choice.
- Bundle a Stimulus JavaScript distribution — load Stimulus the way you load any other JS.
- Inject logging / observability / tracing — those are application concerns, not library concerns.
- Replace `request.url_for(...)` with anything more magical.

This list will not grow.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome — please file an issue first for anything bigger than a typo so we can align on scope.

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md) Code of Conduct.

## License

[MIT](LICENSE) © 2026 Dane Thurber
