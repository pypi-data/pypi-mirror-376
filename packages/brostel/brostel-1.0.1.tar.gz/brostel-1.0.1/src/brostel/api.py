"""Main API for Brostel."""

from telegrinder import Context, Message

from .config import ConfigManager
from .core import MessageBuilder


def brostel(value: str | Message, ctx: Context | None = None):
    """
    Creates a BrostelMessage object for Telegram message formatting.

    Args:
        value: Text string or Message object
        ctx: Telegrinder context (optional)

    Returns:
        BrostelMessage for further processing

    Example:
        ```python
        # From text
        msg = brostel("Hello, %user%!").tags(user="World")

        # From Telegram message
        msg = brostel(telegram_message).tags(user="User")
        ```
    """
    if isinstance(value, str):
        return MessageBuilder.from_text(value, ctx)
    else:
        return MessageBuilder.from_message(value, ctx)


def configure(**kwargs) -> None:
    """
    Configures global Brostel settings.

    Args:
        **kwargs: Configuration parameters

    Example:
        ```python
        configure(
            default_tags={"app": "MyBot"},
            allow_buttons=True,
            max_message_length=2000
        )
        ```
    """
    ConfigManager.configure(**kwargs)
