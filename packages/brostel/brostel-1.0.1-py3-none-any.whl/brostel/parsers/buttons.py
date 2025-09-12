"""Button parser for Telegram keyboards."""

import re

from telegrinder import InlineButton, InlineKeyboard


class ButtonParser:
    """Parser for extracting buttons from message text."""

    BUTTON_PATTERN = re.compile(
        r"\[(?P<text>[^]]+)]"
        r"\((?P<content>[^)]+?)"
        r"(?P<row_tag>:row)?"
        r"(?P<tags>:(?:copy|share))?\)",
        flags=re.IGNORECASE,
    )

    @classmethod
    def parse(cls, text: str) -> tuple[str, InlineKeyboard]:
        """
        Parses text and extracts buttons.

        Args:
            text: Text with button markup

        Returns:
            Tuple of cleaned text and keyboard
        """
        keyboard = InlineKeyboard()
        cleaned_text = text

        for match in cls.BUTTON_PATTERN.finditer(text):
            button = cls._create_button_from_match(match)
            keyboard.add(button)

            if not match.group("row_tag"):
                keyboard.row()

            cleaned_text = cleaned_text.replace(match.group(0), "")

        return cleaned_text.strip(), keyboard

    @classmethod
    def _create_button_from_match(cls, match: re.Match) -> InlineButton:
        """Creates button from regex match result."""
        btn_text = match.group("text")
        content = match.group("content")
        tags = match.group("tags")

        button_params = cls._get_button_params(content, tags)
        return InlineButton(text=btn_text, **button_params)

    @staticmethod
    def _get_button_params(content: str, tags: str | None) -> dict:
        """Determines button parameters based on tags."""
        if tags == ":copy":
            return {"copy_text": content}
        elif tags == ":share":
            return {"url": f"https://t.me/share/url?url={content}"}
        else:
            return {"url": content}
