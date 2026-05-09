"""Form helpers — Pydantic validation-error → Turbo Stream replacement.

:func:`validation_error_stream` turns a Pydantic ``ValidationError`` into
a turbo-stream that replaces only the form's block — no full-page
reload, no scroll loss.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from fastapi import Request

from .responses import TurboStreamResponse
from .streams import _stream

if TYPE_CHECKING:
    from pydantic import ValidationError

    from .templates import HotwireTemplates

__all__ = [
    "validation_error_stream",
]


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
