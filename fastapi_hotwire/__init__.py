"""fastapi-hotwire — Hotwire (Turbo) integration for FastAPI."""

from __future__ import annotations

from . import streams
from .blocks import Jinja2BlockRenderer
from .deps import TurboContext, turbo_context
from .protocols import BlockRenderer, SessionLike, TemplateRenderer
from .responses import TurboStreamResponse

__all__ = [
    "BlockRenderer",
    "Jinja2BlockRenderer",
    "SessionLike",
    "TemplateRenderer",
    "TurboContext",
    "TurboStreamResponse",
    "streams",
    "turbo_context",
]
