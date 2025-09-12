"""Utilities for working with message entities."""

import typing

from fntypes import Nothing, Option, Some
from sulguk.data import MessageEntity as SulgukEntity
from telegrinder.types import MessageEntity, MessageEntityType


def _get_optional_field(field: str, data: dict[str, typing.Any]) -> Option:
    """Gets optional field from dictionary."""
    return (
        Some(data[field])
        if field in data and data[field] is not None
        else Nothing()
    )


def convert_entities(entities: list[SulgukEntity]) -> list[MessageEntity]:
    """
    Converts Sulguk entities to Telegrinder entities.

    Args:
        entities: List of Sulguk entities

    Returns:
        List of Telegrinder entities
    """
    return [
        MessageEntity(
            type=MessageEntityType(entity["type"]),
            offset=entity["offset"],
            length=entity["length"],
            url=_get_optional_field("url", entity),
            user=_get_optional_field("user", entity),
            language=_get_optional_field("language", entity),
        )
        for entity in entities
    ]
