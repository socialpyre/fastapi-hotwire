"""Form helpers: HMAC time-trap token and Pydantic validation-error stream.

The time-trap token is a server-signed timestamp embedded as a hidden
form field. :func:`verify_form_token` rejects submissions that arrive
implausibly fast (a bot scraping and submitting in <``min_age`` seconds)
or stale (a page that sat past ``max_age``).

:func:`validation_error_stream` turns a Pydantic ``ValidationError`` into
a turbo-stream that replaces only the form's block — no full-page
reload, no scroll loss.

The form token is sized as an **anti-bot tripwire**, not a long-lived
auth artifact: HMAC-SHA256 truncated to 64 bits, no per-user binding,
single rotation key. Pair with :mod:`fastapi_hotwire.csrf` for
state-changing endpoints. Do **not** reuse for password-reset tokens,
session tokens, or authenticated-CSRF — use a 256-bit, server-stored,
user-bound primitive for those.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from fastapi import Request

from .responses import TurboStreamResponse
from .streams import _stream

if TYPE_CHECKING:
    from pydantic import ValidationError

    from .templates import HotwireTemplates

__all__ = [
    "make_form_token",
    "validation_error_stream",
    "verify_form_token",
]

DEFAULT_MIN_AGE_SECONDS = 3
DEFAULT_MAX_AGE_SECONDS = 3600


def make_form_token(secret: str, *, now: int | None = None) -> str:
    """Return an HMAC-signed timestamp suitable for a hidden form field.

    Embed in the form and check on submit with :func:`verify_form_token`.
    No per-user binding — this is a tripwire against bots, not a CSRF
    token.
    """
    issued_at = int(time.time()) if now is None else now
    payload = str(issued_at)
    return f"{payload}.{_sign(payload, secret)}"


def validation_error_stream(
    exc: ValidationError,
    *,
    templates: HotwireTemplates,
    template: str,
    block: str,
    target: str,
    request: Request,
    form_data: Mapping[str, Any] | None = None,
    error_formatter: Callable[[ValidationError], Mapping[str, str]] | None = None,
    extra_context: Mapping[str, Any] | None = None,
    action: str = "replace",
) -> TurboStreamResponse:
    """Render the form block with errors as a Turbo Stream.

    The rendered template receives:

    - ``errors``: a ``{field_name: human_message}`` mapping (built by
      ``error_formatter`` if given, otherwise Pydantic's own messages).
    - ``form_data``: a ``{field_name: value}`` mapping. Pass the raw
      submitted form dict to round-trip *all* input back to the user;
      omit to fall back to a best-effort extraction from the exception
      (only the values that failed validation).
    - Anything in ``extra_context``.

    Returns ``status_code=422`` — Turbo applies streams on any 2xx/4xx
    response with the right content-type.
    """
    formatter = error_formatter or _default_errors
    errors = formatter(exc)
    resolved_form_data = (
        dict(form_data) if form_data is not None else _form_data_from_validation_error(exc)
    )
    context = dict(extra_context or {})
    context.update({"errors": errors, "form_data": resolved_form_data})

    body = templates.render_block_string(request, template, block, **context)
    stream = _stream(action, target=target, targets=None, html=body)
    return TurboStreamResponse(stream, status_code=422)


def verify_form_token(
    token: str,
    secret: str,
    *,
    min_age: int = DEFAULT_MIN_AGE_SECONDS,
    max_age: int = DEFAULT_MAX_AGE_SECONDS,
    now: int | None = None,
) -> bool:
    """Return True iff ``token`` is well-formed, validly signed, and within bounds.

    Constant-time signature comparison; rejects fresh-too-fast, stale,
    and any non-canonical (signed, whitespace-padded, non-digit)
    timestamps.
    """
    if not token or "." not in token:
        return False
    payload, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(sig, _sign(payload, secret)):
        return False
    if not payload.isdigit():
        return False
    issued_at = int(payload)
    elapsed = (int(time.time()) if now is None else now) - issued_at
    return min_age <= elapsed <= max_age


def _default_errors(exc: ValidationError) -> dict[str, str]:
    out: dict[str, str] = {}
    for err in exc.errors():
        loc = err.get("loc") or ()
        field = str(loc[0]) if loc else ""
        out.setdefault(field, str(err.get("msg", "Invalid value")))
    return out


def _form_data_from_validation_error(exc: ValidationError) -> dict[str, Any]:
    """Best-effort: pull each error's input value out of the exception."""
    out: dict[str, Any] = {}
    for err in exc.errors():
        loc = err.get("loc") or ()
        if not loc:
            continue
        out[str(loc[0])] = err.get("input")
    return out


def _sign(message: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16]
