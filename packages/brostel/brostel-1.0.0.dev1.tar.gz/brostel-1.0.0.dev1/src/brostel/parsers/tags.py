"""Tag parser for text replacement."""

import re
from typing import Any


class TagParser:
    """Parser for working with tags in message text."""

    TAG_PATTERN = re.compile(r"%(\w+)%")

    @classmethod
    def find_tags(cls, text: str) -> list[str]:
        """Finds all tags in text."""
        return cls.TAG_PATTERN.findall(text)

    @classmethod
    def replace_tags(cls, text: str, tags: dict[str, Any]) -> str:
        """Replaces tags in text with their values."""
        def replace_func(match: re.Match) -> str:
            tag_name = match.group(1)
            return str(tags.get(tag_name, match.group(0)))

        return cls.TAG_PATTERN.sub(replace_func, text)

    @classmethod
    def validate_tags(
        cls, text: str, available_tags: dict[str, Any],
    ) -> list[str]:
        """Checks which tags in text have no values."""
        found_tags = cls.find_tags(text)
        return [tag for tag in found_tags if tag not in available_tags]
