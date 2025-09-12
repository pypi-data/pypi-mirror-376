"""Builder for creating Brostel messages."""

from telegrinder import Context, Message

from .message import BrostelMessage


class MessageBuilder:
    """Factory for creating BrostelMessage from various sources."""

    @staticmethod
    def from_text(text: str, ctx: Context | None = None) -> BrostelMessage:
        """Creates message from text."""
        return BrostelMessage(text=text, ctx=ctx)

    @staticmethod
    def from_message(
        message: Message, ctx: Context | None = None,
    ) -> BrostelMessage:
        """Creates message from Message object."""
        text = MessageBuilder._extract_text_from_message(message)
        if not text:
            raise ValueError("Message contains no text")
        return BrostelMessage(text=text, ctx=ctx)

    @staticmethod
    def _extract_text_from_message(message: Message) -> str | None:
        """Extracts text from Telegram message."""
        return (
            message.html_text.unwrap_or(
                message.text.unwrap_or(
                    message.html_caption.unwrap_or(
                        message.caption.unwrap_or_none(),
                    ),
                ),
            )
        )
