# This module is kept for backward compatibility
# All functions have been moved to appropriate modules

from brostel.parsers import ButtonParser
from brostel.utils import convert_entities

# Backward compatibility
parse_buttons = ButtonParser.parse

__all__ = ["parse_buttons", "convert_entities"]
