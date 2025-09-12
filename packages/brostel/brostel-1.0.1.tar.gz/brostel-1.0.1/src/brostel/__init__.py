"""
Brostel - Telegram formatting tool for Telegrinder-based bots.

Key features:
- HTML message formatting
- Dynamic tag replacement support
- Automatic inline button creation
- Flexible configuration

Usage example:
```python
from brostel import brostel, configure

# Configuration
configure(default_tags={"bot": "MyBot"})

# Usage
message = brostel("Hello, %user%! Welcome to %bot%!")
message.tags(user="John")
await message.reply(telegram_message)
```
"""

from .api import brostel, configure
from .config import BrostelConfiguration
from .core import BrostelMessage

__version__ = "1.0.0"
__all__ = ["brostel", "configure", "BrostelMessage", "BrostelConfiguration"]
