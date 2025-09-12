"""Brostel configuration manager."""

from typing import Any

from .settings import BrostelConfiguration


class ConfigManager:
    """Manager for convenient configuration work."""

    @staticmethod
    def configure(**kwargs) -> None:
        """
        Configures Brostel.

        Args:
            **kwargs: Configuration parameters
        """
        BrostelConfiguration.setup(kwargs)

    @staticmethod
    def add_default_tag(name: str, value: Any) -> None:
        """Adds default tag."""
        BrostelConfiguration.default_tags[name] = value

    @staticmethod
    def remove_default_tag(name: str) -> None:
        """Removes default tag."""
        BrostelConfiguration.default_tags.pop(name, None)

    @staticmethod
    def set_escaper(escaper_func) -> None:
        """Sets escaping function."""
        BrostelConfiguration.escaper = escaper_func

    @staticmethod
    def set_mapper(mapper_func) -> None:
        """Sets message mapping function."""
        BrostelConfiguration.map = mapper_func

    @staticmethod
    def get_config() -> dict[str, Any]:
        """Returns current configuration."""
        return {
            "default_tags": BrostelConfiguration.default_tags.copy(),
            "allow_buttons": BrostelConfiguration.allow_buttons,
            "max_message_length": BrostelConfiguration.max_message_length,
        }
