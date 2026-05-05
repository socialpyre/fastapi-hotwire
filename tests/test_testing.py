"""Tests for ``fastapi_hotwire.testing``."""

from __future__ import annotations

import re

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

from fastapi_hotwire import TurboStreamResponse, streams
from fastapi_hotwire.testing import (
    StreamAction,
    assert_turbo_frame,
    assert_turbo_stream,
    parse_streams,
    turbo_frame_request,
    turbo_stream_request,
)


def test_assert_turbo_stream_passes_for_correct_content_type():
    app = FastAPI()

    @app.get("/", response_class=TurboStreamResponse)
    def root():
        return TurboStreamResponse(streams.remove(target="x"))

    resp = TestClient(app).get("/")
    assert_turbo_stream(resp)


def test_assert_turbo_stream_fails_for_html():
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    def root():
        return HTMLResponse("<p>x</p>")

    with pytest.raises(AssertionError, match=re.escape("text/vnd.turbo-stream.html")):
        assert_turbo_stream(TestClient(app).get("/"))


def test_parse_streams_single_action():
    app = FastAPI()

    @app.get("/")
    def root():
        return TurboStreamResponse(streams.append("<li>hi</li>", target="list"))

    actions = parse_streams(TestClient(app).get("/"))
    assert actions == [StreamAction("append", "list", None, "<li>hi</li>")]


def test_parse_streams_multiple_actions():
    body = "".join(
        [
            streams.replace("<form>1</form>", target="form"),
            streams.append("<div>2</div>", target="flash"),
            streams.remove(target="banner"),
        ]
    )

    app = FastAPI()

    @app.get("/")
    def root():
        return TurboStreamResponse(body)

    actions = parse_streams(TestClient(app).get("/"))
    assert [a.action for a in actions] == ["replace", "append", "remove"]
    assert [a.target for a in actions] == ["form", "flash", "banner"]
    assert actions[0].content == "<form>1</form>"
    assert actions[2].content == ""


def test_parse_streams_with_targets_selector():
    app = FastAPI()

    @app.get("/")
    def root():
        return TurboStreamResponse(streams.update("<p>hi</p>", targets=".message"))

    actions = parse_streams(TestClient(app).get("/"))
    assert actions[0].target is None
    assert actions[0].targets == ".message"


def test_assert_turbo_frame_finds_match():
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    def root():
        return HTMLResponse('<turbo-frame id="sidebar"><p>hi</p></turbo-frame>')

    assert_turbo_frame(TestClient(app).get("/"), frame_id="sidebar")


def test_assert_turbo_frame_fails_when_missing():
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    def root():
        return HTMLResponse('<turbo-frame id="other"></turbo-frame>')

    with pytest.raises(AssertionError, match="sidebar"):
        assert_turbo_frame(TestClient(app).get("/"), frame_id="sidebar")


def test_turbo_frame_request_sets_header():
    app = FastAPI()

    @app.get("/")
    def root(request: Request):
        return {"frame": request.headers.get("turbo-frame")}

    body = turbo_frame_request(TestClient(app), "/", "sidebar").json()
    assert body == {"frame": "sidebar"}


def test_turbo_stream_request_sets_accept():
    app = FastAPI()

    @app.post("/")
    def root(request: Request):
        return {"accept": request.headers.get("accept", "")}

    body = turbo_stream_request(TestClient(app), "/").json()
    assert "text/vnd.turbo-stream.html" in body["accept"]


def test_turbo_stream_request_preserves_existing_accept():
    app = FastAPI()

    @app.post("/")
    def root(request: Request):
        return {"accept": request.headers.get("accept", "")}

    body = turbo_stream_request(TestClient(app), "/", headers={"Accept": "text/html"}).json()
    assert "text/html" in body["accept"]
    assert "text/vnd.turbo-stream.html" in body["accept"]
