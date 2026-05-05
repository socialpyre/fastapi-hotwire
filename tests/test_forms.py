"""Tests for ``fastapi_hotwire.forms``."""

from __future__ import annotations

import hashlib
import hmac
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, ValidationError
from starlette.middleware.sessions import SessionMiddleware

from fastapi_hotwire import HotwireTemplates
from fastapi_hotwire.forms import (
    make_form_token,
    validation_error_stream,
    verify_form_token,
)
from fastapi_hotwire.testing import assert_turbo_stream, parse_streams

SECRET = "test-secret"


def _sign_for_test(payload: str) -> str:
    return hmac.new(
        SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16]


class _Form(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=3, pattern=r"^[^@]+@[^@]+$")


def test_token_round_trip():
    token = make_form_token(SECRET, now=1000)
    assert verify_form_token(token, SECRET, now=1010, min_age=3, max_age=3600)


def test_token_too_fresh_rejected():
    token = make_form_token(SECRET, now=1000)
    assert not verify_form_token(token, SECRET, now=1001, min_age=3)


def test_token_too_old_rejected():
    token = make_form_token(SECRET, now=1000)
    assert not verify_form_token(token, SECRET, now=99999, max_age=3600)


def test_forged_signature_rejected():
    token = make_form_token(SECRET, now=1000)
    body, _, _ = token.partition(".")
    forged = f"{body}.0000000000000000"
    assert not verify_form_token(forged, SECRET, now=1010)


def test_malformed_token_rejected():
    assert not verify_form_token("", SECRET)
    assert not verify_form_token("nodot", SECRET)
    assert not verify_form_token("notanint.deadbeefdeadbeef", SECRET)


def test_non_canonical_timestamp_rejected():
    """Signed payloads must be plain digits — no leading sign, no whitespace."""
    for payload in ("+1000", "-1000", " 1000", "1000 ", "1_000"):
        signed = f"{payload}.{_sign_for_test(payload)}"
        assert not verify_form_token(signed, SECRET, now=1010)


def test_token_uses_different_secret():
    token = make_form_token(SECRET, now=1000)
    assert not verify_form_token(token, "different-secret", now=1010)


@pytest.fixture
def templates_dir(tmp_path: Path) -> Path:
    (tmp_path / "form.html").write_text(
        "{% block form %}"
        "<form>"
        '{% if errors.name %}<p class="err name">{{ errors.name }}</p>{% endif %}'
        '{% if errors.email %}<p class="err email">{{ errors.email }}</p>{% endif %}'
        "<input name=\"name\" value=\"{{ form_data.get('name', '') }}\">"
        "<input name=\"email\" value=\"{{ form_data.get('email', '') }}\">"
        "</form>"
        "{% endblock %}"
    )
    return tmp_path


def test_validation_error_stream_renders_block(templates_dir: Path):
    templates = HotwireTemplates(directory=str(templates_dir), flashes=False)
    app = FastAPI()

    @app.post("/submit")
    def submit(request: Request):
        try:
            _Form.model_validate({"name": "", "email": "bad"})
        except ValidationError as exc:
            return validation_error_stream(
                exc,
                templates=templates,
                template="form.html",
                block="form",
                target="contact-form",
                request=request,
            )
        return {"ok": True}

    resp = TestClient(app).post("/submit")
    assert resp.status_code == 422
    assert_turbo_stream(resp)
    actions = parse_streams(resp)
    assert len(actions) == 1
    assert actions[0].action == "replace"
    assert actions[0].target == "contact-form"
    assert "<form>" in actions[0].content
    assert "err name" in actions[0].content
    assert "err email" in actions[0].content


def test_validation_error_stream_preserves_form_data(templates_dir: Path):
    templates = HotwireTemplates(directory=str(templates_dir), flashes=False)
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="x")

    @app.post("/submit")
    def submit(request: Request):
        raw = {"name": "Alice", "email": "bad"}
        try:
            _Form.model_validate(raw)
        except ValidationError as exc:
            return validation_error_stream(
                exc,
                templates=templates,
                template="form.html",
                block="form",
                target="contact-form",
                request=request,
                form_data=raw,
            )
        return {"ok": True}

    actions = parse_streams(TestClient(app).post("/submit"))
    # Even though the *whole submission* fails validation, the input
    # value for valid fields should round-trip back to the form.
    assert 'value="Alice"' in actions[0].content


def test_error_formatter_override(templates_dir: Path):
    templates = HotwireTemplates(directory=str(templates_dir), flashes=False)
    app = FastAPI()

    def my_formatter(exc):
        return {"name": "name is mandatory", "email": "email needs an @ symbol"}

    @app.post("/submit")
    def submit(request: Request):
        try:
            _Form.model_validate({"name": "", "email": "bad"})
        except ValidationError as exc:
            return validation_error_stream(
                exc,
                templates=templates,
                template="form.html",
                block="form",
                target="contact-form",
                request=request,
                error_formatter=my_formatter,
            )
        return {"ok": True}

    actions = parse_streams(TestClient(app).post("/submit"))
    assert "name is mandatory" in actions[0].content
    assert "email needs an @ symbol" in actions[0].content
