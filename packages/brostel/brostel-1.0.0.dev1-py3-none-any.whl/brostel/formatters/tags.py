"""Formatter for processing tags in text."""

from typing import Any

from telegrinder import Context

from brostel.parsers import TagParser


class TagFormatter:
    """Formatter for replacing tags in message text."""

    @classmethod
    def format(
        cls, text: str, tags: dict[str, Any], ctx: Context | None = None,
    ) -> str:
        """
        Formats text by replacing tags with their values.

        Args:
            text: Source text with tags
            tags: Dictionary of tags for replacement
            ctx: Telegrinder context (takes priority over regular tags)

        Returns:
            Formatted text
        """
        formatted_text = text

        # First replace context tags (if any)
        if ctx:
            context_tags = ctx.get("brostel", {})
            formatted_text = TagParser.replace_tags(
                formatted_text, context_tags,
            )

        # Then replace regular tags
        return TagParser.replace_tags(formatted_text, tags)
