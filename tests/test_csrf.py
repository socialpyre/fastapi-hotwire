"""Tests for ``fastapi_hotwire.csrf``."""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from fastapi_hotwire import csrf


def _app(dep):
    app = FastAPI()

    @app.post("/submit", dependencies=[Depends(dep)])
    def submit():
        return {"ok": True}

    return TestClient(app)


def test_exact_origin_match():
    client = _app(csrf.allowed_origin("https://example.com"))
    resp = client.post("/submit", headers={"Origin": "https://example.com"})
    assert resp.status_code == 200


def test_wrong_scheme_rejected():
    client = _app(csrf.allowed_origin("https://example.com"))
    resp = client.post("/submit", headers={"Origin": "http://example.com"})
    assert resp.status_code == 403


def test_unknown_host_rejected():
    client = _app(csrf.allowed_origin("https://example.com"))
    resp = client.post("/submit", headers={"Origin": "https://evil.com"})
    assert resp.status_code == 403


def test_referer_fallback():
    client = _app(csrf.allowed_origin("https://example.com"))
    resp = client.post("/submit", headers={"Referer": "https://example.com/contact"})
    assert resp.status_code == 200


def test_missing_origin_and_referer_rejected():
    client = _app(csrf.allowed_origin("https://example.com"))
    resp = client.post("/submit")
    assert resp.status_code == 403


def test_wildcard_subdomain_single_label():
    client = _app(csrf.allowed_origin("https://*.cloudfront.net"))
    resp = client.post("/submit", headers={"Origin": "https://d1234.cloudfront.net"})
    assert resp.status_code == 200


def test_wildcard_does_not_cross_dot_boundaries():
    """`*` matches exactly one DNS label. `evil.dXXX.cloudfront.net`
    has 4 labels; `*.cloudfront.net` has 3 — no match."""
    client = _app(csrf.allowed_origin("https://*.cloudfront.net"))
    resp = client.post("/submit", headers={"Origin": "https://evil.dXXX.cloudfront.net"})
    assert resp.status_code == 403


def test_label_count_must_match_for_wildcard():
    """Reject `https://example.com` (2 labels) against `https://*.example.com` (3 labels).
    A wildcard slot must be filled — empty doesn't count."""
    client = _app(csrf.allowed_origin("https://*.example.com"))
    resp = client.post("/submit", headers={"Origin": "https://example.com"})
    assert resp.status_code == 403


def test_wildcard_only_pattern_does_not_swallow_arbitrary_hosts():
    """`https://*.com` has 2 labels and would only match 2-label `.com`
    hosts, never `evil.example.com` (3 labels). This is the protection
    that motivated the per-label match."""
    client = _app(csrf.allowed_origin("https://*.com"))
    resp = client.post("/submit", headers={"Origin": "https://evil.example.com"})
    assert resp.status_code == 403


def test_multiple_patterns_any_match():
    client = _app(
        csrf.allowed_origin(
            "https://prod.example.com",
            "https://staging.example.com",
        )
    )
    assert client.post("/submit", headers={"Origin": "https://prod.example.com"}).status_code == 200
    assert (
        client.post("/submit", headers={"Origin": "https://staging.example.com"}).status_code == 200
    )
    assert (
        client.post("/submit", headers={"Origin": "https://other.example.com"}).status_code == 403
    )


def test_no_patterns_raises_at_construction_time():
    with pytest.raises(ValueError):
        csrf.allowed_origin()


def test_port_must_match_when_specified():
    client = _app(csrf.allowed_origin("http://example.com:8080"))
    assert client.post("/submit", headers={"Origin": "http://example.com:8080"}).status_code == 200
    assert client.post("/submit", headers={"Origin": "http://example.com:9090"}).status_code == 403
    assert client.post("/submit", headers={"Origin": "http://example.com"}).status_code == 403


def test_host_match_is_case_insensitive():
    client = _app(csrf.allowed_origin("https://Example.COM"))
    resp = client.post("/submit", headers={"Origin": "https://example.com"})
    assert resp.status_code == 200
