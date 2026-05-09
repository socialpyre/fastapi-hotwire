"""fastapi-hotwire — Hotwire (Turbo) integration for FastAPI.

Public API:

- :class:`TurboStreamResponse` — ``Response`` with the Turbo Stream media type.
- :mod:`streams` — pure-function builders for ``<turbo-stream>`` actions.
- :class:`TurboContext` + :func:`turbo_context` — request-shape dependency.
- :class:`HotwireTemplates` — ``Jinja2Templates`` with block + stream helpers.
- :func:`flash`, :func:`get_flashed`, :class:`FlashMessage` — session flash.
- :mod:`forms` — Pydantic validation-error → Turbo Stream helper.
- :mod:`csrf` — origin-check dependency factory.
- :mod:`testing` — pytest assertions and request helpers for Hotwire endpoints.

See https://github.com/socialpyre/fastapi-hotwire for the quickstart.
"""

from __future__ import annotations

from . import csrf, forms, streams, testing
from .blocks import BlockRenderer, Jinja2BlockRenderer
from .deps import TurboContext, turbo_context
from .flash import FlashMessage, flash, get_flashed
from .protocols import SessionLike, TemplateRenderer
from .responses import TurboStreamResponse
from .templates import HotwireTemplates

__all__ = [
    "BlockRenderer",
    "FlashMessage",
    "HotwireTemplates",
    "Jinja2BlockRenderer",
    "SessionLike",
    "TemplateRenderer",
    "TurboContext",
    "TurboStreamResponse",
    "csrf",
    "flash",
    "forms",
    "get_flashed",
    "streams",
    "testing",
    "turbo_context",
]
