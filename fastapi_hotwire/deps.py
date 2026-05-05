"""FastAPI dependencies for reading Hotwire-related request signals."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

__all__ = ["TurboContext", "turbo_context"]


_STREAM_MEDIA_TYPE = "text/vnd.turbo-stream.html"


@dataclass(frozen=True, slots=True)
class TurboContext:
    """Read-only summary of how the current request relates to Turbo.

    Attributes:
        is_frame: True if the request was issued by a ``<turbo-frame>``
            (the ``Turbo-Frame`` header is present).
        frame_id: The ``id`` of the frame that initiated the request,
            or ``None`` for non-frame requests.
        accepts_stream: True if the client's ``Accept`` header includes
            ``text/vnd.turbo-stream.html``. Turbo sends this on form
            submissions; a normal page navigation doesn't.
        is_visit: True for a top-level Turbo visit (``Sec-Fetch-Mode``
            is ``navigate`` AND there's no ``Turbo-Frame`` header).
            Useful when you want to render the chrome only on real
            navigations.
    """

    is_frame: bool
    frame_id: str | None
    accepts_stream: bool
    is_visit: bool


async def turbo_context(request: Request) -> TurboContext:
    """FastAPI dependency that returns a :class:`TurboContext` for the request.

    Use as::

        from typing import Annotated
        from fastapi import Depends
        from fastapi_hotwire import TurboContext, turbo_context

        @app.post("/items")
        async def create(turbo: Annotated[TurboContext, Depends(turbo_context)]):
            if turbo.accepts_stream:
                ...
    """
    frame_id = request.headers.get("turbo-frame")
    accept = request.headers.get("accept", "")
    sec_fetch_mode = request.headers.get("sec-fetch-mode", "")
    return TurboContext(
        is_frame=frame_id is not None,
        frame_id=frame_id,
        accepts_stream=_STREAM_MEDIA_TYPE in accept,
        is_visit=frame_id is None and sec_fetch_mode == "navigate",
    )
