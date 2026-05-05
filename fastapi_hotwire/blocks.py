"""Block-level Jinja2 rendering.

The Hotwire pattern most worth supporting is "one template, two render
modes": render the full page on a normal navigation, or render just one
``{% block frame_x %}`` on a partial request. Jinja2 doesn't expose this
directly out of the box, so this module implements it on top of the
``Template.blocks`` mapping while staying behind a Protocol that
alternative engines can satisfy.
"""

from __future__ import annotations

from typing import Any

import jinja2

from .protocols import BlockRenderer

__all__ = ["BlockNotFoundError", "BlockRenderer", "Jinja2BlockRenderer"]


class BlockNotFoundError(LookupError):
    """Raised when a referenced ``{% block %}`` doesn't exist in the template."""

    def __init__(self, block: str, template: str) -> None:
        super().__init__(f"block {block!r} not found in template {template!r}")
        self.block = block
        self.template = template


class Jinja2BlockRenderer:
    """Default :class:`~fastapi_hotwire.protocols.BlockRenderer` implementation.

    Construct with an existing :class:`jinja2.Environment` so users keep
    full control over loaders, filters, globals, autoescape, and async
    rendering. Block resolution walks template inheritance — a block
    overridden in a child template is rendered with the child's content,
    same as a normal full-page render.

    Implementation note: we intentionally don't depend on
    ``jinja2-fragments`` because its public API takes context as
    ``**context``, which collides with any context key whose name
    matches one of its positional parameters (notably ``environment``).
    Inlining the dozen-line block render avoids the footgun without
    losing functionality.
    """

    def __init__(self, env: jinja2.Environment) -> None:
        self.env = env

    def render_block(self, name: str, block: str, context: dict[str, Any]) -> str:
        template = self.env.get_template(name)
        block_render = template.blocks.get(block)
        if block_render is None:
            raise BlockNotFoundError(block, name)
        ctx = template.new_context(context)
        return self.env.concat(block_render(ctx))  # type: ignore[attr-defined]
