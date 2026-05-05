"""Tests for ``fastapi_hotwire.deps``."""

from __future__ import annotations

from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from fastapi_hotwire import TurboContext, turbo_context


@pytest.fixture
def client():
    app = FastAPI()

    @app.get("/")
    async def root(turbo: Annotated[TurboContext, Depends(turbo_context)]):
        return {
            "is_frame": turbo.is_frame,
            "frame_id": turbo.frame_id,
            "accepts_stream": turbo.accepts_stream,
            "is_visit": turbo.is_visit,
        }

    return TestClient(app)


def test_no_hotwire_headers(client):
    body = client.get("/").json()
    assert body == {
        "is_frame": False,
        "frame_id": None,
        "accepts_stream": False,
        "is_visit": False,
    }


def test_turbo_frame_header_marks_frame(client):
    body = client.get("/", headers={"Turbo-Frame": "sidebar"}).json()
    assert body["is_frame"] is True
    assert body["frame_id"] == "sidebar"
    assert body["is_visit"] is False


def test_accepts_stream_via_accept_header(client):
    body = client.get("/", headers={"Accept": "text/vnd.turbo-stream.html"}).json()
    assert body["accepts_stream"] is True


def test_accepts_stream_in_mixed_accept_list(client):
    body = client.get("/", headers={"Accept": "text/html, text/vnd.turbo-stream.html;q=0.9"}).json()
    assert body["accepts_stream"] is True


def test_html_only_accept_does_not_accept_stream(client):
    body = client.get("/", headers={"Accept": "text/html"}).json()
    assert body["accepts_stream"] is False


def test_is_visit_when_navigate_and_no_frame(client):
    body = client.get("/", headers={"Sec-Fetch-Mode": "navigate"}).json()
    assert body["is_visit"] is True
    assert body["is_frame"] is False


def test_is_visit_false_when_frame_present(client):
    body = client.get("/", headers={"Sec-Fetch-Mode": "navigate", "Turbo-Frame": "x"}).json()
    assert body["is_visit"] is False
