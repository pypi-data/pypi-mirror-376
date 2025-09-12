"""Message types for Brostel."""

import typing

from telegrinder.types import InlineKeyboardMarkup, MessageEntity


class BuiltMessage(typing.TypedDict):
    """
    Brostel message build result for sending to Telegram.

    Usage:
    ```python
    await api.send_message(chat_id=..., **brostel(...).build())
    ```
    """

    text: str
    entities: list[MessageEntity]
    reply_markup: InlineKeyboardMarkup | None
