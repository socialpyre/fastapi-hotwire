"""Turbo Stream action builders.

Each builder returns a ``<turbo-stream>`` element as a ``markupsafe.Markup``
string. The ``Markup`` wrapper means the result won't be double-escaped
if you happen to interpolate it into a Jinja template; pass it to
``TurboStreamResponse`` directly for the normal use case.

Compose multiple actions by passing a list to ``TurboStreamResponse`` or
by string-concatenating builder return values::

    from fastapi_hotwire import TurboStreamResponse, streams

    return TurboStreamResponse([
        streams.replace(form_html, target="contact-form"),
        streams.append(flash_html, target="flash"),
    ])

The seven content actions mirror Hotwire's spec
(https://turbo.hotwired.dev/handbook/streams). ``refresh`` is the
Turbo 8 page-refresh action.

SECURITY — trust contract for the ``html`` argument
---------------------------------------------------

Each content builder accepts an ``html`` string and inlines it verbatim
into the ``<template>`` envelope **without escaping**. This is by
design: callers pass already-rendered HTML (Jinja output, a Stimulus-
ready partial, etc.) and the protocol requires the browser-side
``<template>`` parser to receive the raw markup.

The contract is therefore: **whatever you pass as ``html`` MUST be
safe to interpolate into the page**. Concretely:

- HTML produced by a Jinja2 environment with autoescape enabled
  (Starlette's :class:`Jinja2Templates` defaults to autoescape on, and
  :class:`fastapi_hotwire.HotwireTemplates` asserts it at construction)
  is safe.
- Static, hand-written HTML is safe.
- A user-controlled string interpolated without escaping is **not**
  safe. ``streams.append(user_input, target="chat")`` is an XSS.

Attribute values (``target=``, ``targets=``, ``request_id=``) are
escaped automatically; only the body content is your responsibility.
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

    # html is treated as already-rendered, safe HTML — never escaped
    # here. Callers must satisfy the trust contract documented at the
    # module level. The <template> wrapper is required by the Turbo
    # Streams spec; the parser pulls children from it before applying
    # the action.
    return Markup(
        f'<turbo-stream action="{action}" {selector_attr}>'
        f"<template>{html}</template>"
        f"</turbo-stream>"
    )


def append(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Insert ``html`` as the last child of the targeted element(s).

    ``html`` is interpolated verbatim — see this module's SECURITY note.
    """
    return _stream("append", target=target, targets=targets, html=html)


def prepend(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Insert ``html`` as the first child of the targeted element(s)."""
    return _stream("prepend", target=target, targets=targets, html=html)


def replace(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Replace the targeted element(s) — including the element itself — with ``html``."""
    return _stream("replace", target=target, targets=targets, html=html)


def update(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Replace the contents of the targeted element(s) with ``html``."""
    return _stream("update", target=target, targets=targets, html=html)


def remove(*, target: str | None = None, targets: str | None = None) -> Markup:
    """Remove the targeted element(s)."""
    return _stream("remove", target=target, targets=targets, html=None)


def before(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Insert ``html`` immediately before the targeted element(s)."""
    return _stream("before", target=target, targets=targets, html=html)


def after(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Insert ``html`` immediately after the targeted element(s)."""
    return _stream("after", target=target, targets=targets, html=html)


def refresh(*, request_id: str | None = None) -> Markup:
    """Trigger a Turbo 8 page refresh.

    ``request_id`` lets the client de-duplicate refreshes triggered by
    the same originating action (e.g. a stream broadcast triggered by
    the same request that initiated it).
    """
    if request_id is None:
        return Markup('<turbo-stream action="refresh"></turbo-stream>')
    return Markup(
        f'<turbo-stream action="refresh" request-id="{escape(request_id)}"></turbo-stream>'
    )
