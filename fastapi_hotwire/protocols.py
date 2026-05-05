"""Engine-agnostic Protocols.

These define the integration seams so users can plug in alternative
template engines or session backends without depending on the bundled
Jinja2 / Starlette code paths.

The default implementations in this package use Jinja2 (via
``jinja2-fragments``) and ``starlette.middleware.sessions.SessionMiddleware``,
but anything matching these Protocols will work.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, Protocol, runtime_checkable

__all__ = ["BlockRenderer", "SessionLike", "TemplateRenderer"]


@runtime_checkable
class TemplateRenderer(Protocol):
    """Renders a named template with a context mapping into an HTML string."""

    def render(self, name: str, context: dict[str, Any]) -> str: ...


@runtime_checkable
class BlockRenderer(Protocol):
    """Renders a single named block from a template into an HTML string.

    Hotwire's frame/stream patterns work best when one template can be
    rendered as a full page on a normal request and as a single
    ``<turbo-frame>``/stream-target block on a partial request.
    """

    def render_block(self, name: str, block: str, context: dict[str, Any]) -> str: ...


# ``SessionLike`` is a structural alias rather than a Protocol class
# because :class:`Protocol` can't inherit from a non-Protocol generic.
# Anything that satisfies ``MutableMapping[str, Any]`` — Starlette's
# ``SessionMiddleware``, ``starsessions``, an in-memory ``dict`` —
# works wherever fastapi-hotwire takes a session.
SessionLike = MutableMapping[str, Any]
