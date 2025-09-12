"""Main Brostel message class."""

import typing
from functools import cached_property

from fntypes import Result
from sulguk import transform_html
from sulguk.data import MessageEntity as SulgukEntity
from telegrinder import (
    APIError,
    Context,
    InlineButton,
    InlineKeyboard,
    MessageCute,
)

from brostel.config import BrostelConfiguration
from brostel.formatters import TagFormatter
from brostel.parsers import ButtonParser
from brostel.types import BuiltMessage
from brostel.utils import convert_entities


class BrostelMessage:
    """Class for working with Telegram messages through Brostel."""

    def __init__(self, text: str, ctx: Context | None = None) -> None:
        """
        Initialize message.

        Args:
            text: HTML message text
            ctx: Telegrinder context (optional)
        """
        # Store original HTML text without transformation
        self.original_text = text
        self.tags_dict = BrostelConfiguration.default_tags.copy()
        self.ctx = ctx
        self.markup_obj = None

    def build(self) -> BuiltMessage:
        """Builds final message for sending."""
        mapped_message = BrostelConfiguration.map(self)
        if not isinstance(mapped_message, BrostelMessage):
            raise TypeError("Map function must return a BrostelMessage object")

        # First, format tags in the original HTML text
        formatted_html = TagFormatter.format(
            mapped_message.original_text,
            mapped_message.tags_dict,
            mapped_message.ctx,
        )

        # Then transform HTML to get correct entities for the final text
        html_data = transform_html(formatted_html)

        # Parse buttons from the plain text (after HTML transformation)
        final_text, markup = ButtonParser.parse(html_data.text)

        # Use markup from parsing if no custom markup was set
        if mapped_message.markup_obj is None:
            final_markup = (
                markup.get_markup() if markup.keyboard else None
            )
        else:
            final_markup = mapped_message.markup_obj.get_markup()

        # Escape the final text
        escaped_text = BrostelConfiguration.escaper(final_text)

        return BuiltMessage(
            text=escaped_text,
            entities=convert_entities(html_data.entities),
            reply_markup=final_markup,
        )

    @cached_property
    def obj(self) -> BuiltMessage:
        """Cached message build result."""
        return self.build()

    @property
    def text(self) -> str:
        """Gets the original HTML text."""
        return self.original_text

    @text.setter
    def text(self, value: str) -> None:
        """Sets the original HTML text."""
        self.original_text = value
        # Clear cache when text changes
        if hasattr(self, "__dict__") and "obj" in self.__dict__:
            del self.__dict__["obj"]

    def tags(self, **kwargs: typing.Any) -> typing.Self:
        """Adds tags for text replacement."""
        self.tags_dict.update(kwargs)
        # Clear cache when tags change
        if hasattr(self, "__dict__") and "obj" in self.__dict__:
            del self.__dict__["obj"]
        return self

    def tostring(self) -> str:
        """Returns message text as string."""
        return self.obj["text"]

    def markup(self, use: bool) -> typing.Self:
        """Enables or disables keyboard."""
        if not use:
            self.markup_obj = None
        elif use:
            self.markup_obj = InlineKeyboard()
        return self

    def button(self, text: str, **kwargs) -> typing.Self:
        """Adds button to keyboard."""
        if not self.markup_obj:
            return self
        self.markup_obj.add(InlineButton(text=text, **kwargs))
        return self

    def row(self) -> typing.Self:
        """Moves to new row in keyboard."""
        if self.markup_obj:
            self.markup_obj.row()
        return self

    async def answer(
        self, message: MessageCute,
    ) -> Result[MessageCute, APIError]:
        """Answers to message."""
        return await message.answer(**self.obj)

    async def reply(
        self, message: MessageCute,
    ) -> Result[MessageCute, APIError]:
        """Replies to message with quote."""
        return await message.reply(**self.obj)
