"""Turbo Stream action builders.

Each builder returns a ``markupsafe.Markup`` string that wraps a single
``<turbo-stream>`` element. Pass one to :class:`TurboStreamResponse`,
or pass a list to combine actions in one response.

Trust contract for the ``html`` argument
----------------------------------------

The ``html`` you pass is interpolated **verbatim** into the
``<template>`` envelope. The browser-side Turbo parser requires raw
markup, so callers own the safety of that string:

- Jinja2 output with autoescape on (the default in
  :class:`Jinja2Templates` and required by
  :class:`HotwireTemplates`) is safe.
- Static, hand-written HTML is safe.
- A user-controlled string interpolated without escaping is **not**
  safe — ``streams.append(user_input, target="chat")`` is an XSS.

Attribute values (``target=``, ``targets=``, ``request-id=``) are
escaped automatically.
"""

from __future__ import annotations

from markupsafe import Markup, escape

__all__ = [
    "after",
    "append",
    "before",
    "prepend",
    "refresh",
    "remove",
    "replace",
    "update",
]


def after(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Insert ``html`` immediately after the targeted element(s)."""
    return _stream("after", target=target, targets=targets, html=html)


def append(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Insert ``html`` as the last child of the targeted element(s)."""
    return _stream("append", target=target, targets=targets, html=html)


def before(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Insert ``html`` immediately before the targeted element(s)."""
    return _stream("before", target=target, targets=targets, html=html)


def prepend(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Insert ``html`` as the first child of the targeted element(s)."""
    return _stream("prepend", target=target, targets=targets, html=html)


def refresh(*, request_id: str | None = None) -> Markup:
    """Trigger a Turbo 8 page refresh, optionally tagged with ``request_id``."""
    if request_id is None:
        return Markup('<turbo-stream action="refresh"></turbo-stream>')
    return Markup(
        f'<turbo-stream action="refresh" request-id="{escape(request_id)}"></turbo-stream>'
    )


def remove(*, target: str | None = None, targets: str | None = None) -> Markup:
    """Remove the targeted element(s)."""
    return _stream("remove", target=target, targets=targets, html=None)


def replace(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Replace the targeted element(s) — including the element itself — with ``html``."""
    return _stream("replace", target=target, targets=targets, html=html)


def update(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Replace the *contents* of the targeted element(s) with ``html``."""
    return _stream("update", target=target, targets=targets, html=html)


def _stream(
    action: str,
    *,
    target: str | None,
    targets: str | None,
    html: str | None,
) -> Markup:
    if target is not None and targets is not None:
        raise ValueError("pass either target= or targets=, not both")
    if target is None and targets is None:
        raise ValueError(f"action={action!r} requires target= or targets=")

    if target is not None:
        selector_attr = f'target="{escape(target)}"'
    else:
        selector_attr = f'targets="{escape(targets)}"'

    if html is None:
        return Markup(f'<turbo-stream action="{action}" {selector_attr}></turbo-stream>')
    return Markup(
        f'<turbo-stream action="{action}" {selector_attr}>'
        f"<template>{html}</template>"
        f"</turbo-stream>"
    )
