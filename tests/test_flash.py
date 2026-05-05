"""Tests for ``fastapi_hotwire.flash``."""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from fastapi_hotwire import FlashMessage, flash, get_flashed
from fastapi_hotwire.testing import assert_turbo_stream, parse_streams


@pytest.fixture
def client_factory():
    def _make():
        app = FastAPI()
        app.add_middleware(SessionMiddleware, secret_key="test")
        return app, TestClient(app)

    return _make


def test_flash_round_trip(client_factory):
    app, client = client_factory()

    @app.post("/enqueue")
    def enqueue(request: Request):
        flash(request, "Hello", category="success")
        return {"ok": True}

    @app.get("/drain")
    def drain(request: Request):
        msgs = get_flashed(request)
        return [{"text": m.text, "category": m.category} for m in msgs]

    client.post("/enqueue")
    body = client.get("/drain").json()
    assert body == [{"text": "Hello", "category": "success"}]


def test_get_flashed_clears_queue(client_factory):
    app, client = client_factory()

    @app.post("/enqueue")
    def enqueue(request: Request):
        flash(request, "x")
        return {"ok": True}

    @app.get("/drain")
    def drain(request: Request):
        return [m.text for m in get_flashed(request)]

    client.post("/enqueue")
    assert client.get("/drain").json() == ["x"]
    assert client.get("/drain").json() == []


def test_multiple_flashes_accumulate(client_factory):
    app, client = client_factory()

    @app.post("/enqueue")
    def enqueue(request: Request):
        flash(request, "one", category="info")
        flash(request, "two", category="warning")
        return {"ok": True}

    @app.get("/drain")
    def drain(request: Request):
        return [(m.text, m.category) for m in get_flashed(request)]

    client.post("/enqueue")
    body = client.get("/drain").json()
    assert body == [["one", "info"], ["two", "warning"]]


def test_flash_stream_returns_turbo_stream_response(client_factory):
    app, client = client_factory()

    @app.post("/notify")
    def notify(request: Request):
        return flash.stream(request, "Saved", category="success")

    resp = client.post("/notify")
    assert_turbo_stream(resp)
    actions = parse_streams(resp)
    assert len(actions) == 1
    assert actions[0].action == "append"
    assert actions[0].target == "flash"
    assert "Saved" in actions[0].content
    assert "flash-success" in actions[0].content


def test_flash_stream_drains_pending_by_default(client_factory):
    app, client = client_factory()

    @app.post("/queue")
    def queue(request: Request):
        flash(request, "earlier", category="info")
        return {"ok": True}

    @app.post("/notify")
    def notify(request: Request):
        return flash.stream(request, "now", category="success")

    client.post("/queue")
    actions = parse_streams(client.post("/notify"))
    assert "earlier" in actions[0].content
    assert "now" in actions[0].content


def test_flash_without_session_middleware_is_clear_error():
    app = FastAPI()
    # No SessionMiddleware on purpose.

    @app.post("/notify")
    def notify(request: Request):
        flash(request, "x")
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=True)
    with pytest.raises(RuntimeError, match="SessionMiddleware"):
        client.post("/notify")


def test_flash_message_dataclass_is_frozen():
    from dataclasses import FrozenInstanceError

    msg = FlashMessage(text="x")
    # ``setattr`` bypasses static type checks; the runtime guard from
    # ``frozen=True`` is what we're verifying here.
    with pytest.raises(FrozenInstanceError):
        setattr(msg, "text", "y")  # noqa: B010 - direct assignment fails type check
