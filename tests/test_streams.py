"""Tests for ``fastapi_hotwire.streams``."""

from __future__ import annotations

import pytest
from markupsafe import Markup

from fastapi_hotwire import streams


@pytest.mark.parametrize(
    ("action", "fn"),
    [
        ("append", streams.append),
        ("prepend", streams.prepend),
        ("replace", streams.replace),
        ("update", streams.update),
        ("before", streams.before),
        ("after", streams.after),
    ],
)
def test_content_action_with_target(action, fn):
    out = fn("<p>hi</p>", target="messages")
    assert isinstance(out, Markup)
    expected = (
        f'<turbo-stream action="{action}" target="messages">'
        f"<template><p>hi</p></template>"
        f"</turbo-stream>"
    )
    assert out == expected


@pytest.mark.parametrize(
    ("action", "fn"),
    [
        ("append", streams.append),
        ("prepend", streams.prepend),
        ("replace", streams.replace),
        ("update", streams.update),
        ("before", streams.before),
        ("after", streams.after),
    ],
)
def test_content_action_with_targets(action, fn):
    out = fn("<p>hi</p>", targets=".message")
    expected = (
        f'<turbo-stream action="{action}" targets=".message">'
        f"<template><p>hi</p></template>"
        f"</turbo-stream>"
    )
    assert out == expected


def test_remove_action_has_no_template():
    out = streams.remove(target="msg-1")
    assert out == '<turbo-stream action="remove" target="msg-1"></turbo-stream>'


def test_remove_with_targets():
    out = streams.remove(targets=".dismissed")
    assert out == '<turbo-stream action="remove" targets=".dismissed"></turbo-stream>'


def test_refresh_without_request_id():
    assert streams.refresh() == '<turbo-stream action="refresh"></turbo-stream>'


def test_refresh_with_request_id():
    assert (
        streams.refresh(request_id="abc-123")
        == '<turbo-stream action="refresh" request-id="abc-123"></turbo-stream>'
    )


def test_target_and_targets_together_raises():
    with pytest.raises(ValueError, match="either target= or targets="):
        streams.append("x", target="a", targets=".b")


def test_neither_target_nor_targets_raises():
    with pytest.raises(ValueError, match="requires target= or targets="):
        streams.append("x")


def test_remove_neither_target_nor_targets_raises():
    with pytest.raises(ValueError):
        streams.remove()


def test_target_attribute_is_html_escaped():
    out = streams.append("<p/>", target='evil"x')
    # Quote inside target gets escaped so the attribute isn't broken out of.
    assert 'target="evil&#34;x"' in out


def test_content_is_not_escaped():
    raw = '<div data-foo="bar\'s">x & y</div>'
    out = streams.append(raw, target="t")
    assert raw in out
