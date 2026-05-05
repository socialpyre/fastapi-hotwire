"""Hotwire-aware ``Jinja2Templates`` wrapper.

Adds three things to Starlette's ``Jinja2Templates``:

1. ``render_block(request, name, block, **ctx)`` returns an
   ``HTMLResponse`` containing only one ``{% block %}``. Useful for
   responding to ``<turbo-frame>`` requests — same template, different
   render scope.

2. ``render_stream(request, name, block, *, action="replace", target=...)``
   returns a :class:`~fastapi_hotwire.responses.TurboStreamResponse`
   wrapping the rendered block in the chosen Turbo Stream action.

3. A ``flashes`` context processor that pulls + clears
   ``request.session["_flash"]`` so flash messages appear automatically
   in any template that includes a flash partial.

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

    Construct exactly as you would Starlette's ``Jinja2Templates``, plus
    an optional ``context_processors=[...]`` list of callables that take
    a :class:`fastapi.Request` and return a context ``dict``. The flash
    processor is registered automatically; pass ``flashes=False`` to
    opt out (e.g. tests or APIs that don't want any session coupling).
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
        # Starlette's Jinja2Templates accepts ``context_processors`` and runs
        # them on every ``TemplateResponse`` — pass through so users get the
        # same processors regardless of which render path they take. The
        # branch is here because Starlette's overloads accept either
        # ``directory=`` (non-None) OR ``env=`` (no directory) — passing
        # ``directory=None`` doesn't match either.
        if directory is None:
            super().__init__(context_processors=procs, **kwargs)
        else:
            super().__init__(directory=directory, context_processors=procs, **kwargs)
        # Starlette's Jinja2Templates exposes the ``Environment`` as ``self.env``.
        # Autoescape MUST be on for the trust contract in
        # :mod:`fastapi_hotwire.streams` to hold (rendered block output
        # is interpolated into ``<turbo-stream>`` markup verbatim).
        if not self.env.autoescape:
            raise RuntimeError(
                "HotwireTemplates requires Jinja2 autoescape to be enabled. "
                "Block output is interpolated into Turbo Stream markup without "
                "additional escaping; disabling autoescape would turn any "
                "user-supplied template variable into an XSS sink."
            )
        self.block_renderer = Jinja2BlockRenderer(self.env)
        self._context_processors: list[ContextProcessor] = procs

    def _merged_context(self, request: Request, extra: dict[str, Any]) -> dict[str, Any]:
        ctx: dict[str, Any] = {"request": request}
        for proc in self._context_processors:
            ctx.update(proc(request))
        ctx.update(extra)
        return ctx

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
        """Render a single block and return it wrapped in a Turbo Stream action."""
        body = self.render_block_string(request, name, block, **context)
        if action == "remove":
            stream = _stream("remove", target=target, targets=targets, html=None)
        else:
            stream = _stream(action, target=target, targets=targets, html=body)
        return TurboStreamResponse(stream, status_code=status_code, headers=headers)
