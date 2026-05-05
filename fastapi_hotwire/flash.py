"""Session-backed flash messages with a Hotwire-native turbo-stream variant.

Decoupled from any specific session middleware. Requires only that
``request.session`` exist and behave like a ``MutableMapping[str, Any]``
— Starlette's ``SessionMiddleware``, ``starsessions``, and other
compatible middlewares all qualify.

Flash content rides in the user's signed-but-not-encrypted session
cookie. **Do not** put PII or secrets in flash messages. Keep flash
text server-supplied; user input must be escaped before templating.
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
    "render_flashes_html",
]

_SESSION_KEY = "_flash"


@dataclass(frozen=True, slots=True)
class FlashMessage:
    """A single flash entry. ``category`` is freeform — by convention
    one of ``info`` / ``success`` / ``warning`` / ``error``."""

    text: str
    category: str = "info"


def flashes_context_processor(request: Request) -> dict[str, Any]:
    """Templates context processor exposing ``flashes`` and clearing the queue.

    Once invoked the queue is empty, so subsequent calls return ``[]``.
    Templates that need the data more than once should bind it locally.
    """
    return {"flashes": _drain(request)}


def get_flashed(request: Request) -> list[FlashMessage]:
    """Return all queued flashes for ``request`` and clear the queue."""
    return _drain(request)


def render_flashes_html(request: Request) -> HTMLResponse:
    """Drain pending flashes and return them as a plain ``HTMLResponse``.

    Convenience for endpoints that want just the flash region. Most apps
    will use the ``flashes`` context processor or :meth:`flash.stream`
    instead.
    """
    return HTMLResponse(_builtin_flash_html(_drain(request)))


def _builtin_flash_html(messages: list[FlashMessage]) -> Markup:
    parts = [
        f'<div class="flash flash-{escape(m.category)}" role="status">{escape(m.text)}</div>'
        for m in messages
    ]
    return Markup("".join(parts))


def _drain(request: Request) -> list[FlashMessage]:
    session = _try_session(request)
    if session is None:
        return []
    raw = session.pop(_SESSION_KEY, None) or []
    return [FlashMessage(**entry) for entry in raw]


def _enqueue(request: Request, text: str, category: str) -> None:
    session = _require_session(request)
    queue = session.get(_SESSION_KEY) or []
    queue.append({"text": text, "category": category})
    session[_SESSION_KEY] = queue


class _FlashAPI:
    """Implementation of the ``flash`` public singleton.

    Exposed as a callable instance so the API reads naturally either as
    ``flash(request, "Saved")`` or ``flash.stream(request, "Saved")``.
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
        """Return a Turbo Stream that delivers this flash without redirecting.

        ``include_pending`` (default ``True``) drains any flashes already
        queued and combines them with this one so a single response
        shows all messages.

        When ``templates`` and ``template`` are both provided, the named
        template's ``flashes`` block is rendered with a ``flashes``
        context variable. Otherwise a built-in minimal partial is used.
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


def _require_session(request: Request) -> dict[str, Any]:
    """Strict accessor for the write path; raises with a clear setup message."""
    try:
        return request.session  # type: ignore[no-any-return]
    except AssertionError as exc:
        raise RuntimeError(
            "fastapi-hotwire flash requires a session: install "
            "starlette.middleware.sessions.SessionMiddleware (or another "
            "middleware that exposes request.session as a MutableMapping)."
        ) from exc


def _try_session(request: Request) -> dict[str, Any] | None:
    """Tolerant accessor for read paths; returns ``None`` when no session is installed."""
    try:
        return request.session  # type: ignore[no-any-return]
    except AssertionError:
        return None


flash = _FlashAPI()
