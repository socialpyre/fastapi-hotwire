"""Response classes for Hotwire-aware endpoints."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from starlette.responses import Response

__all__ = ["TurboStreamResponse"]


class TurboStreamResponse(Response):
    """HTTP response carrying one or more Turbo Stream actions.

    Sets ``Content-Type: text/vnd.turbo-stream.html`` so Turbo on the
    client recognizes the body as stream actions to apply rather than
    HTML to render. ``content`` accepts a single string of stream HTML
    or an iterable of strings (e.g. the return values from
    ``fastapi_hotwire.streams.*``), which are joined verbatim — no
    separator, no extra escaping, since each builder already produces
    well-formed ``<turbo-stream>`` markup.

    Use as ``response_class=TurboStreamResponse`` on a route to have
    OpenAPI document the response media type, or instantiate directly.
    """

    media_type = "text/vnd.turbo-stream.html"

    def __init__(
        self,
        content: str | bytes | Iterable[str] | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
        background: Any = None,
    ) -> None:
        if content is not None and not isinstance(content, (str, bytes)):
            content = "".join(content)
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )
