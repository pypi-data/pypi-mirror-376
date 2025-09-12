"""Brostel configuration settings."""

import typing
from collections.abc import Callable

import markupsafe


def _default_identity_map(msg):
    """Default identity function for message mapping."""
    return msg


class BrostelConfiguration:
    """Global Brostel configuration."""

    # Default tags for all messages
    default_tags: dict[str, typing.Any] = {}

    # Function for HTML escaping
    escaper: Callable[[str], str] = markupsafe.escape

    # Function for message mapping
    map: Callable[[typing.Any], typing.Any] = _default_identity_map

    # Whether to allow buttons
    allow_buttons: bool = True

    # Maximum message length
    max_message_length: int = 4096

    @classmethod
    def setup(cls, data: dict[str, typing.Any]) -> None:
        """
        Configures settings.

        Args:
            data: Dictionary with configuration parameters
        """
        for field, value in data.items():
            if hasattr(cls, field):
                setattr(cls, field, value)
            else:
                raise ValueError(f"Unknown configuration parameter: {field}")

    @classmethod
    def reset(cls) -> None:
        """Resets configuration to default values."""
        cls.default_tags = {}
        cls.escaper = markupsafe.escape
        cls.map = _default_identity_map
        cls.allow_buttons = True
        cls.max_message_length = 4096
