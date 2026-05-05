"""Tests for ``fastapi_hotwire.templates``."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from fastapi_hotwire import HotwireTemplates, flash
from fastapi_hotwire.testing import assert_turbo_stream, parse_streams


@pytest.fixture
def templates_dir(tmp_path: Path) -> Path:
    (tmp_path / "page.html").write_text(
        "<html>"
        "{% for f in flashes %}"
        '<div class="flash flash-{{ f.category }}">{{ f.text }}</div>'
        "{% endfor %}"
        "{% block content %}<p>{{ message }}</p>{% endblock %}"
        "</html>"
    )
    (tmp_path / "row.html").write_text(
        '{% block row %}<li id="item-{{ item.id }}">{{ item.name }}</li>{% endblock %}'
    )
    return tmp_path


def test_render_block_renders_only_named_block(templates_dir: Path):
    templates = HotwireTemplates(directory=str(templates_dir))
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")

    @app.get("/")
    def root(request: Request):
        return templates.render_block(request, "row.html", "row", item={"id": 1, "name": "x"})

    body = TestClient(app).get("/").text
    assert body == '<li id="item-1">x</li>'


def test_render_stream_returns_turbo_stream_response(templates_dir: Path):
    templates = HotwireTemplates(directory=str(templates_dir))
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")

    @app.get("/")
    def root(request: Request):
        return templates.render_stream(
            request,
            "row.html",
            "row",
            action="append",
            target="items",
            item={"id": 7, "name": "lucky"},
        )

    resp = TestClient(app).get("/")
    assert_turbo_stream(resp)
    actions = parse_streams(resp)
    assert len(actions) == 1
    assert actions[0].action == "append"
    assert actions[0].target == "items"
    assert actions[0].content == '<li id="item-7">lucky</li>'


def test_flash_context_processor_drains_session(templates_dir: Path):
    templates = HotwireTemplates(directory=str(templates_dir))
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")

    @app.post("/set")
    def setter(request: Request):
        flash(request, "Saved", category="success")
        return {"ok": True}

    @app.get("/")
    def reader(request: Request):
        return templates.TemplateResponse(request, "page.html", {"message": "hi"})

    client = TestClient(app)
    client.post("/set")
    resp = client.get("/")
    body = resp.text
    assert '<div class="flash flash-success">Saved</div>' in body
    # second read drains
    resp2 = client.get("/")
    assert "flash-" not in resp2.text


def test_extra_context_processors_compose(templates_dir: Path):
    def brand_ctx(request: Request) -> dict[str, object]:
        return {"brand": "Hotwire"}

    (templates_dir / "branded.html").write_text("Hello {{ brand }}, {{ message }}.")
    templates = HotwireTemplates(
        directory=str(templates_dir),
        context_processors=[brand_ctx],
    )
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")

    @app.get("/")
    def root(request: Request):
        return templates.TemplateResponse(request, "branded.html", {"message": "world"})

    body = TestClient(app).get("/").text
    assert body == "Hello Hotwire, world."


def test_flashes_off_skips_session_dependency(templates_dir: Path):
    """With flashes=False the templates can render without SessionMiddleware."""
    (templates_dir / "plain.html").write_text("<p>{{ message }}</p>")
    templates = HotwireTemplates(directory=str(templates_dir), flashes=False)

    app = FastAPI()  # no SessionMiddleware

    @app.get("/")
    def root(request: Request):
        return templates.TemplateResponse(request, "plain.html", {"message": "ok"})

    body = TestClient(app).get("/").text
    assert body == "<p>ok</p>"
