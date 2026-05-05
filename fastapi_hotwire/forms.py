"""Form helpers: HMAC time-trap token and Pydantic ``ValidationError`` to stream.

The time-trap token is a small, server-signed timestamp embedded as a
hidden form field. ``verify_form_token`` rejects submissions that arrive
implausibly fast (a bot that scrapes and submits in <``min_age``
seconds) or implausibly stale (a page that sat idle past ``max_age``).

``validation_error_stream`` turns a Pydantic ``ValidationError`` into a
turbo-stream that replaces only the form's block — no full-page reload,
no scroll loss, no flash-of-unstyled.

SECURITY — what the form-token IS and ISN'T
-------------------------------------------

The token is sized as an **anti-bot tripwire**:

- HMAC-SHA256 truncated to 64 bits (16 hex chars) — adequate against
  online brute-force when the validating endpoint sits behind a CDN /
  rate-limiter, NOT adequate as a long-lived auth artifact.
- No per-user, per-form, or per-IP binding — a token minted for one
  form works against any other form on the same site within the
  ``[min_age, max_age]`` window. The pairing with Origin/Referer
  checks (see :mod:`fastapi_hotwire.csrf`) is what makes this a
  defensible CSRF posture for low-stakes forms.
- The signing key is a single secret, rotated as a unit. Rotating it
  invalidates every in-flight token — fine for marketing forms,
  problematic if you reused this primitive for password reset.

**Do not reuse** ``make_form_token`` / ``verify_form_token`` for:

- Password-reset / magic-link tokens — use a 256-bit token bound to a
  user id and stored server-side.
- Session tokens — use a real session middleware.
- Anti-CSRF for state-changing endpoints in authenticated apps — bind
  to user + form + nonce, not just time.

Use it as documented (anti-spam tripwire on public forms) and the
properties are sufficient.
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


# Defaults — tuned for human form-fill speeds. Override via kwargs if
# your form has typing assistance or read-only views that legitimately
# submit faster, or if some surface needs a longer max age.
DEFAULT_MIN_AGE_SECONDS = 3
DEFAULT_MAX_AGE_SECONDS = 3600


def _sign(message: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16]


def make_form_token(secret: str, *, now: int | None = None) -> str:
    """Return an HMAC-signed timestamp suitable for a hidden form field.

    Embed in the form and check on submit with :func:`verify_form_token`.
    The token has no per-user binding — it's a tripwire against bots,
    not a CSRF token.
    """
    issued_at = int(time.time()) if now is None else now
    payload = str(issued_at)
    return f"{payload}.{_sign(payload, secret)}"


def verify_form_token(
    token: str,
    secret: str,
    *,
    min_age: int = DEFAULT_MIN_AGE_SECONDS,
    max_age: int = DEFAULT_MAX_AGE_SECONDS,
    now: int | None = None,
) -> bool:
    """Return True iff ``token`` is well-formed, validly signed, and within bounds.

    A bot that scrapes and submits in <``min_age`` seconds fails; a
    stale token (page sat for >``max_age`` seconds) also fails. Constant-
    time signature comparison.
    """
    if not token or "." not in token:
        return False
    payload, sig = token.rsplit(".", 1)
    expected = _sign(payload, secret)
    if not hmac.compare_digest(sig, expected):
        return False
    try:
        issued_at = int(payload)
    except ValueError:
        return False
    elapsed = (int(time.time()) if now is None else now) - issued_at
    return min_age <= elapsed <= max_age


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
      ``error_formatter`` if given, otherwise a minimal default that
      uses Pydantic's own messages).
    - ``form_data``: a ``{field_name: value}`` mapping. Pass the raw
      submitted form dict explicitly to round-trip *all* input back
      to the user (including fields that validated cleanly). When
      omitted, falls back to a best-effort extraction from the
      exception, which only contains values for fields that failed
      validation.
    - Plus anything you pass in ``extra_context``.

    Returns ``status_code=422`` to mirror REST validation semantics
    without breaking Hotwire's HTTP-status handling — Turbo applies
    streams on any 2xx/4xx response with the right content-type.
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
