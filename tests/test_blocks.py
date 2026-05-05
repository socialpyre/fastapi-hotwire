"""Tests for ``fastapi_hotwire.blocks``."""

from __future__ import annotations

import pytest
from jinja2 import DictLoader, Environment

from fastapi_hotwire import Jinja2BlockRenderer
from fastapi_hotwire.blocks import BlockNotFoundError


@pytest.fixture
def env():
    return Environment(
        loader=DictLoader(
            {
                "page.html": (
                    "<html>"
                    "{% block hero %}<h1>{{ title }}</h1>{% endblock %}"
                    "{% block body %}<p>{{ body }}</p>{% endblock %}"
                    "</html>"
                ),
                "child.html": (
                    "{% extends 'page.html' %}"
                    "{% block hero %}<h2>child {{ title }}</h2>{% endblock %}"
                ),
            }
        ),
        autoescape=True,
    )


def test_render_named_block_only(env):
    out = Jinja2BlockRenderer(env).render_block(
        "page.html", "hero", {"title": "Hello", "body": "ignored"}
    )
    assert out == "<h1>Hello</h1>"


def test_render_block_uses_inheritance(env):
    out = Jinja2BlockRenderer(env).render_block("child.html", "hero", {"title": "World"})
    assert out == "<h2>child World</h2>"


def test_unknown_block_raises(env):
    with pytest.raises(BlockNotFoundError):
        Jinja2BlockRenderer(env).render_block("page.html", "nonexistent", {})
