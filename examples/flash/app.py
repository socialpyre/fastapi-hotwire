"""fastapi-hotwire flash demo: session-backed flash + Hotwire-native variant.

Run with::

    uv run uvicorn app:app --reload

Then open http://127.0.0.1:8000.

This example demonstrates two flash flows:

1. **PRG flash** — POST form, redirect with flash queued in the session,
   GET serves the page with the flash rendered into the layout.
2. **Hotwire-native flash** — POST returns a turbo-stream that appends
   the flash partial to the ``#flash`` region without a redirect.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from fastapi_hotwire import HotwireTemplates, flash

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="example-secret-do-not-use-in-prod")

templates = HotwireTemplates(directory=str(Path(__file__).parent / "templates"))


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/save-redirect")
def save_with_redirect(request: Request):
    flash(request, "Saved (via redirect)", category="success")
    return RedirectResponse("/", status_code=303)


@app.post("/save-stream")
def save_with_stream(request: Request):
    return flash.stream(
        request,
        "Saved (via turbo-stream — no redirect)",
        category="success",
    )


@app.post("/error-stream")
def error_with_stream(request: Request):
    return flash.stream(
        request,
        "Something went wrong",
        category="error",
    )
