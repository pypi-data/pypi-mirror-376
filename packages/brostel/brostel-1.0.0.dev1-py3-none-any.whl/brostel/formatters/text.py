"""Formatter for text processing."""

import markupsafe


class TextFormatter:
    """Formatter for various text operations."""

    @staticmethod
    def escape_html(text: str) -> str:
        """Escapes HTML characters in text."""
        return markupsafe.escape(text)

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """Cleans extra spaces and line breaks."""
        return " ".join(text.split())

    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncates text to specified length."""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
