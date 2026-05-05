"""fastapi-hotwire — Hotwire (Turbo) integration for FastAPI."""

from __future__ import annotations

from .protocols import BlockRenderer, SessionLike, TemplateRenderer

__all__ = [
    "BlockRenderer",
    "SessionLike",
    "TemplateRenderer",
]
