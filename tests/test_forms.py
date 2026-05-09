"""Tests for ``fastapi_hotwire.forms``."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, ValidationError
from starlette.middleware.sessions import SessionMiddleware

from fastapi_hotwire import HotwireTemplates
from fastapi_hotwire.forms import validation_error_stream
from fastapi_hotwire.testing import assert_turbo_stream, parse_streams


class _Form(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=3, pattern=r"^[^@]+@[^@]+$")


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
