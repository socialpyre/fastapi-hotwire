"""Origin/Referer-check CSRF dependency factory.

For Hotwire surfaces sitting behind a CDN (CloudFront, Cloudflare, etc.)
the request ``Host`` header isn't reliable — the edge rewrites it.
Validate the browser-supplied ``Origin`` (or fall back to ``Referer``)
against an explicit deploy-time allowlist.

Wildcards are honored **per DNS label** so ``https://*.cloudfront.net``
matches ``https://dXXX.cloudfront.net`` but not
``https://evil.dXXX.cloudfront.net``. Each ``*`` consumes exactly one
label; multi-label wildcards must be expressed as multiple patterns.
Empty labels are significant — ``a..b`` does **not** match ``a.b``,
and a trailing dot does not match a non-trailing-dot host.
"""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlparse

from fastapi import HTTPException, Request, status

__all__ = ["allowed_origin"]


def allowed_origin(*patterns: str) -> Callable[[Request], None]:
    """Return a FastAPI dependency that 403s on cross-origin requests.

    Pass each allowed origin as a separate string. Wildcards in the host
    portion are honored per label; see this module's docstring for the
    semantics.

    Usage::

        from fastapi_hotwire import csrf

        @router.post(
            "/contact",
            dependencies=[Depends(csrf.allowed_origin(
                "https://example.com",
                "https://*.example.com",
            ))],
        )
        async def contact(...): ...
    """
    if not patterns:
        raise ValueError("allowed_origin() requires at least one pattern")

    def _check(request: Request) -> None:
        candidate = request.headers.get("origin") or request.headers.get("referer")
        if candidate:
            parsed = urlparse(candidate)
            if parsed.scheme and parsed.netloc:
                normalized = f"{parsed.scheme}://{parsed.netloc}"
                if any(_origin_matches(normalized, p) for p in patterns):
                    return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origin not allowed",
        )

    return _check


def _origin_matches(candidate: str, pattern: str) -> bool:
    """True iff ``candidate`` matches ``pattern`` per-label.

    Comparison is case-insensitive on the host and case-sensitive on
    scheme. Ports must match exactly. Each ``*`` in the pattern host
    consumes exactly one DNS label, and empty labels are preserved so
    ``a..b`` does not match ``a.b``.
    """
    c = urlparse(candidate)
    p = urlparse(pattern)
    if c.scheme != p.scheme:
        return False

    c_host, _, c_port = c.netloc.partition(":")
    p_host, _, p_port = p.netloc.partition(":")
    if c_port != p_port:
        return False

    c_labels = c_host.lower().split(".")
    p_labels = p_host.lower().split(".")
    if len(c_labels) != len(p_labels):
        return False
    return all(
        plabel == "*" or plabel == clabel for clabel, plabel in zip(c_labels, p_labels, strict=True)
    )
