"""Main API for Brostel."""

from telegrinder import Context, Message

from .config import BrostelConfig
from .core import MessageBuilder


def brostel(
    value: str | Message,
    ctx: Context | None = None,
    config: BrostelConfig | None = None,
):
    """
    Creates a BrostelMessage object for Telegram message formatting.

    Args:
        value: Text string or Message object
        ctx: Telegrinder context (optional)
        config: Brostel configuration (optional)

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
        return MessageBuilder.from_text(value, ctx, config)
    if isinstance(value, Message):
        return MessageBuilder.from_message(value, ctx, config)
    raise TypeError("Value must be str or telegrinder Message")
