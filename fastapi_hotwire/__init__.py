"""fastapi-hotwire — Hotwire (Turbo) integration for FastAPI."""

from __future__ import annotations

from . import streams, testing
from .blocks import Jinja2BlockRenderer
from .deps import TurboContext, turbo_context
from .flash import FlashMessage, flash, get_flashed
from .protocols import BlockRenderer, SessionLike, TemplateRenderer
from .responses import TurboStreamResponse

__all__ = [
    "BlockRenderer",
    "FlashMessage",
    "Jinja2BlockRenderer",
    "SessionLike",
    "TemplateRenderer",
    "TurboContext",
    "TurboStreamResponse",
    "flash",
    "get_flashed",
    "streams",
    "testing",
    "turbo_context",
]
