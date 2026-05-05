"""Session-backed flash messages with a Hotwire-native turbo-stream variant.

This module is deliberately decoupled from any specific session
middleware. It only requires that ``request.session`` exist and behave
like a ``MutableMapping[str, Any]`` — ``starlette.middleware.sessions
.SessionMiddleware`` provides this; ``starsessions`` and other
compatible middleware do too.

Flash semantics:

- :func:`flash` appends a message to ``request.session["_flash"]``.
- :func:`get_flashed` reads + clears the queue in one call.
- :func:`flashes_context_processor` is registered automatically by
  :class:`~fastapi_hotwire.templates.HotwireTemplates` so any rendered
  template sees a ``flashes`` variable populated with the latest queue.
- :func:`flash.stream` turns a flash into a turbo-stream response that
  appends the rendered partial to a target region — useful for
  Hotwire-aware flows that don't redirect.

SECURITY — flash content trust contract
---------------------------------------

Flash messages ride in the user's session cookie. Starlette's
``SessionMiddleware`` (and most compatible middlewares) **sign** the
cookie but do **not encrypt** it. The cookie is base64-encoded JSON
that any user can decode locally.

Therefore:

- **Do not put PII or secrets in flash messages.** Anything you queue
  is readable by the recipient (and by anyone with access to their
  cookie jar).
- **Keep flash text server-supplied, not user-controlled.** A pattern
  like ``flash(request, f"Welcome {user.email}!")`` is fine for the
  user themselves but means their email rides in their own cookie —
  acceptable only if you've already accepted that trade-off.
- **Avoid templating user input into flash text** — it's interpolated
  into HTML at render time, and while the built-in template uses
  :func:`markupsafe.escape`, custom flash partials may not.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request
from markupsafe import Markup, escape
from starlette.responses import HTMLResponse

from .responses import TurboStreamResponse
from .streams import _stream

__all__ = [
    "FlashMessage",
    "flash",
    "flashes_context_processor",
    "get_flashed",
]


_SESSION_KEY = "_flash"


@dataclass(frozen=True, slots=True)
class FlashMessage:
    """A single flash entry. ``category`` is freeform — by convention
    one of ``info`` / ``success`` / ``warning`` / ``error``."""

    text: str
    category: str = "info"


def _require_session(request: Request) -> dict[str, Any]:
    """Strict accessor — used by the write path. Raises ``RuntimeError``
    with a clear setup message when ``SessionMiddleware`` (or compatible)
    isn't installed."""
    try:
        return request.session  # type: ignore[no-any-return]
    except AssertionError as exc:
        # Starlette raises AssertionError when SessionMiddleware isn't
        # installed — translate to something more useful.
        raise RuntimeError(
            "fastapi-hotwire flash requires a session: install "
            "starlette.middleware.sessions.SessionMiddleware (or another "
            "middleware that exposes request.session as a MutableMapping)."
        ) from exc


def _try_session(request: Request) -> dict[str, Any] | None:
    """Tolerant accessor — used by read paths (``get_flashed``, the
    ``flashes`` context processor). Returns ``None`` when the request
    has no session, so reads silently degrade to "no flashes" instead
    of crashing pages that don't actively use flash. The strict write
    path (``flash()``) still surfaces a clear error if the user forgot
    to install the middleware."""
    try:
        return request.session  # type: ignore[no-any-return]
    except AssertionError:
        return None


def _enqueue(request: Request, text: str, category: str) -> None:
    session = _require_session(request)
    queue = session.get(_SESSION_KEY) or []
    queue.append({"text": text, "category": category})
    session[_SESSION_KEY] = queue


def _drain(request: Request) -> list[FlashMessage]:
    session = _try_session(request)
    if session is None:
        return []
    raw = session.pop(_SESSION_KEY, None) or []
    return [FlashMessage(**entry) for entry in raw]


def get_flashed(request: Request) -> list[FlashMessage]:
    """Return all queued flashes for ``request`` and clear the queue."""
    return _drain(request)


def flashes_context_processor(request: Request) -> dict[str, Any]:
    """Templates context processor exposing ``flashes`` and clearing the queue.

    Once invoked the queue is empty, so subsequent ``get_flashed`` calls
    on the same request return ``[]``. Templates that need the data more
    than once should bind it to a local variable.
    """
    return {"flashes": _drain(request)}


def _builtin_flash_html(messages: list[FlashMessage]) -> Markup:
    parts = [
        f'<div class="flash flash-{escape(m.category)}" role="status">{escape(m.text)}</div>'
        for m in messages
    ]
    return Markup("".join(parts))


class _FlashAPI:
    """Implements ``flash(request, text)`` and ``flash.stream(request, text)``.

    Exposed as the module-level ``flash`` singleton so the API reads
    naturally either way.
    """

    def __call__(self, request: Request, text: str, *, category: str = "info") -> None:
        """Queue a flash message in ``request.session`` for the next request."""
        _enqueue(request, text, category)

    def stream(
        self,
        request: Request,
        text: str,
        *,
        category: str = "info",
        target: str = "flash",
        action: str = "append",
        template: str | None = None,
        templates: Any = None,
        include_pending: bool = True,
    ) -> TurboStreamResponse:
        """Return a :class:`TurboStreamResponse` carrying this flash plus
        any already-queued flashes.

        The stream's content is rendered either by ``templates.render_block``
        (when both ``templates`` and ``template`` are passed; the block
        named by ``template`` is rendered with a ``flashes`` context
        variable), or by a built-in minimal partial as a fallback. The
        built-in markup matches the ``flashes`` example partial in the
        package docs.

        ``include_pending`` (default True) drains any flashes already in
        the session and combines them with this one — useful so a single
        Hotwire response shows all messages, not just the most recent.
        """
        new = FlashMessage(text=text, category=category)
        messages: list[FlashMessage] = []
        if include_pending:
            messages.extend(_drain(request))
        messages.append(new)

        if templates is not None and template is not None:
            html = templates.render_block_string(
                request,
                template,
                "flashes",
                flashes=messages,
            )
        else:
            html = _builtin_flash_html(messages)

        body = _stream(action, target=target, targets=None, html=html)
        return TurboStreamResponse(body)


flash = _FlashAPI()


def render_flashes_html(request: Request) -> HTMLResponse:
    """Convenience for endpoints that want to return just the flash region.

    Drains pending flashes and returns them as a plain ``HTMLResponse``
    using the built-in minimal markup. Most apps won't need this; it's
    here for completeness.
    """
    return HTMLResponse(_builtin_flash_html(_drain(request)))
