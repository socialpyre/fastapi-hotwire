"""pytest helpers for asserting on Hotwire responses.

The parser uses a narrow regex against ``<turbo-stream>`` markup that
this package generates — it is not a general-purpose HTML parser. The
frame-presence check uses a similarly narrow regex on
``<turbo-frame id="…">``.

Helpers accept any object with the duck-typed shape of
``starlette.responses.Response`` or ``httpx.Response`` (a ``text``
attribute or a ``body`` attribute, plus a ``headers`` mapping).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

__all__ = [
    "StreamAction",
    "assert_turbo_frame",
    "assert_turbo_stream",
    "parse_streams",
    "turbo_frame_request",
    "turbo_stream_request",
]

_STREAM_MEDIA_TYPE = "text/vnd.turbo-stream.html"

_STREAM_RE = re.compile(
    r"<turbo-stream\s+(?P<attrs>[^>]*?)>"
    r"(?:<template>(?P<content>.*?)</template>)?"
    r"\s*</turbo-stream>",
    re.DOTALL,
)
_ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')


@dataclass(frozen=True, slots=True)
class StreamAction:
    """One ``<turbo-stream>`` element parsed out of a response body."""

    action: str
    content: str
    target: str | None
    targets: str | None


def assert_turbo_frame(response: Any, *, frame_id: str) -> None:
    """Assert that the response body contains ``<turbo-frame id="frame_id">``."""
    body = _body_text(response)
    pattern = re.compile(
        rf'<turbo-frame\b[^>]*\bid="{re.escape(frame_id)}"',
        re.DOTALL,
    )
    if not pattern.search(body):
        raise AssertionError(f'no <turbo-frame id="{frame_id}"> found in response body')


def assert_turbo_stream(response: Any) -> None:
    """Assert that ``response`` carries the Turbo Stream media type."""
    ct = _content_type(response)
    if not ct.startswith(_STREAM_MEDIA_TYPE):
        raise AssertionError(
            f"expected Content-Type starting with {_STREAM_MEDIA_TYPE!r}, got {ct!r}"
        )


def parse_streams(response: Any) -> list[StreamAction]:
    """Parse all ``<turbo-stream>`` elements out of the response body.

    Doesn't assert the content-type — pair with
    :func:`assert_turbo_stream` when that's also part of the contract.
    """
    body = _body_text(response)
    actions: list[StreamAction] = []
    for match in _STREAM_RE.finditer(body):
        attrs = dict(_ATTR_RE.findall(match.group("attrs") or ""))
        actions.append(
            StreamAction(
                action=attrs.get("action", ""),
                content=match.group("content") or "",
                target=attrs.get("target"),
                targets=attrs.get("targets"),
            )
        )
    return actions


def turbo_frame_request(
    client: Any, url: str, frame_id: str, *, method: str = "GET", **kwargs: Any
) -> Any:
    """Issue a request with a ``Turbo-Frame`` header set."""
    headers = dict(kwargs.pop("headers", {}) or {})
    headers["Turbo-Frame"] = frame_id
    return client.request(method, url, headers=headers, **kwargs)


def turbo_stream_request(client: Any, url: str, *, method: str = "POST", **kwargs: Any) -> Any:
    """Issue a request advertising acceptance of ``text/vnd.turbo-stream.html``."""
    headers = dict(kwargs.pop("headers", {}) or {})
    existing = headers.get("Accept", "")
    if _STREAM_MEDIA_TYPE not in existing:
        headers["Accept"] = (
            f"{existing}, {_STREAM_MEDIA_TYPE}".lstrip(", ") if existing else _STREAM_MEDIA_TYPE
        )
    return client.request(method, url, headers=headers, **kwargs)


def _body_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text is not None:
        return text
    body = getattr(response, "body", None)
    if isinstance(body, (bytes, bytearray)):
        return body.decode("utf-8")
    if isinstance(body, str):
        return body
    raise TypeError(f"cannot read body from {response!r}")


def _content_type(response: Any) -> str:
    headers = getattr(response, "headers", {})
    if isinstance(headers, Mapping):
        return str(headers.get("content-type") or headers.get("Content-Type") or "")
    return ""
