"""Hotwire-aware ``Jinja2Templates`` wrapper.

Adds three things to Starlette's ``Jinja2Templates``:

1. :meth:`HotwireTemplates.render_block` returns an ``HTMLResponse``
   containing only one ``{% block %}`` — useful for
   ``<turbo-frame>`` requests.
2. :meth:`HotwireTemplates.render_stream` wraps a rendered block in a
   :class:`TurboStreamResponse` for the chosen Turbo Stream action.
3. A ``flashes`` context processor that drains
   ``request.session["_flash"]`` so any rendered template sees the
   queue automatically.

Application-specific globals (theme, brand, asset hashes, analytics)
belong in the ``context_processors=`` argument so they stay in app
code, not in the package.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from .blocks import Jinja2BlockRenderer
from .flash import flashes_context_processor
from .responses import TurboStreamResponse
from .streams import _stream

__all__ = ["HotwireTemplates"]


ContextProcessor = Callable[[Request], dict[str, Any]]
PathLike = str | os.PathLike[str] | Sequence[str | os.PathLike[str]]


class HotwireTemplates(Jinja2Templates):
    """``Jinja2Templates`` with Hotwire helpers and a flash context processor.

    Construct as you would Starlette's ``Jinja2Templates``, plus an
    optional ``context_processors=[...]`` list of callables that take a
    :class:`fastapi.Request` and return a context ``dict``. The flash
    processor is registered automatically; pass ``flashes=False`` to opt
    out (for tests or APIs that don't want session coupling).

    The constructor checks ``self.env.autoescape`` and refuses to build
    if it's falsy at construction time — block output is interpolated
    into Turbo Stream markup verbatim, so disabling autoescape would
    turn any user-supplied template variable into an XSS sink. Note
    that callers can still flip ``self.env.autoescape`` after
    construction; that's outside this class's reach.
    """

    def __init__(
        self,
        directory: PathLike | None = None,
        *,
        context_processors: Sequence[ContextProcessor] = (),
        flashes: bool = True,
        **kwargs: Any,
    ) -> None:
        procs: list[ContextProcessor] = list(context_processors)
        if flashes:
            procs.insert(0, flashes_context_processor)
        if directory is None:
            super().__init__(context_processors=procs, **kwargs)
        else:
            super().__init__(directory=directory, context_processors=procs, **kwargs)
        if not self.env.autoescape:
            raise RuntimeError(
                "HotwireTemplates requires Jinja2 autoescape to be enabled. "
                "Block output is interpolated into Turbo Stream markup without "
                "additional escaping; disabling autoescape would turn any "
                "user-supplied template variable into an XSS sink."
            )
        self.block_renderer = Jinja2BlockRenderer(self.env)
        self._context_processors: list[ContextProcessor] = procs

    def render_block(
        self,
        request: Request,
        name: str,
        block: str,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        **context: Any,
    ) -> HTMLResponse:
        """Render a single ``{% block %}`` and return an ``HTMLResponse``."""
        body = self.render_block_string(request, name, block, **context)
        return HTMLResponse(body, status_code=status_code, headers=headers)

    def render_block_string(
        self,
        request: Request,
        name: str,
        block: str,
        **context: Any,
    ) -> str:
        """Render a single ``{% block %}`` and return the raw HTML string."""
        merged = self._merged_context(request, context)
        return self.block_renderer.render_block(name, block, merged)

    def render_stream(
        self,
        request: Request,
        name: str,
        block: str,
        *,
        action: str = "replace",
        target: str | None = None,
        targets: str | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        **context: Any,
    ) -> TurboStreamResponse:
        """Render a single block and wrap it in a Turbo Stream action."""
        body = self.render_block_string(request, name, block, **context)
        if action == "remove":
            stream = _stream("remove", target=target, targets=targets, html=None)
        else:
            stream = _stream(action, target=target, targets=targets, html=body)
        return TurboStreamResponse(stream, status_code=status_code, headers=headers)

    def _merged_context(self, request: Request, extra: dict[str, Any]) -> dict[str, Any]:
        ctx: dict[str, Any] = {"request": request}
        for proc in self._context_processors:
            ctx.update(proc(request))
        ctx.update(extra)
        return ctx
