"""Tests for ``fastapi_hotwire.responses``."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_hotwire import TurboStreamResponse


def test_media_type_set_on_class():
    assert TurboStreamResponse.media_type == "text/vnd.turbo-stream.html"


def test_string_content_passes_through():
    resp = TurboStreamResponse('<turbo-stream action="remove" target="x"></turbo-stream>')
    assert resp.body == b'<turbo-stream action="remove" target="x"></turbo-stream>'


def test_iterable_content_is_joined_without_separator():
    parts = ["<a></a>", "<b></b>"]
    resp = TurboStreamResponse(parts)
    assert resp.body == b"<a></a><b></b>"


def test_none_content_yields_empty_body():
    resp = TurboStreamResponse(None)
    assert resp.body == b""


def test_bytes_content_passes_through():
    resp = TurboStreamResponse(b"<x/>")
    assert resp.body == b"<x/>"


def test_response_class_sets_content_type_header_on_endpoint():
    app = FastAPI()

    @app.get("/", response_class=TurboStreamResponse)
    def root() -> TurboStreamResponse:
        return TurboStreamResponse('<turbo-stream action="remove" target="x"></turbo-stream>')

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/vnd.turbo-stream.html")
