"""Brostel configuration settings."""

import typing
from collections.abc import Callable
from dataclasses import dataclass, field

import markupsafe


def _default_identity_map(msg):
    """Default identity function for message mapping."""
    return msg


@dataclass(frozen=True)
class BrostelConfig:
    """Brostel configuration."""

    default_tags: dict[str, typing.Any] = field(default_factory=dict)
    """Default tags for all messages"""

    escaper: Callable[[str], str] = markupsafe.escape
    """Function for HTML escaping"""

    map: Callable[[typing.Any], typing.Any] = _default_identity_map
    """Function for message mapping"""

    allow_buttons: bool = True
    """Whether to allow buttons"""

    # Maximum message length
    max_message_length: int = 4096

    @classmethod
    def setup(cls, data: dict[str, typing.Any]) -> None:
        """
        Configures settings.

        Args:
            data: Dictionary with configuration parameters
        """
        for _field, value in data.items():
            if hasattr(cls, _field):
                setattr(cls, _field, value)
            else:
                raise ValueError(f"Unknown configuration parameter: {_field}")

    @classmethod
    def reset(cls) -> None:
        """Resets configuration to default values."""
        cls.default_tags = {}
        cls.escaper = markupsafe.escape
        cls.map = _default_identity_map
        cls.allow_buttons = True
        cls.max_message_length = 4096
