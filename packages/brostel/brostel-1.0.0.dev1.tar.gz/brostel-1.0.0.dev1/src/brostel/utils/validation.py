"""Validators for messages."""

from brostel.config import BrostelConfig


class MessageValidator:
    """Validator for message checking."""

    def __init__(self, config: BrostelConfig | None = None) -> None:
        self.cfg = config or BrostelConfig()

    def validate_text_length(self, text: str) -> bool:
        """Validates message text length."""
        return len(text) <= self.cfg.max_message_length

    def validate_buttons_allowed(self) -> bool:
        """Checks if buttons are allowed."""
        return self.cfg.allow_buttons

    def validate_message(
        self, text: str, has_buttons: bool = False,
    ) -> list[str]:
        """
        Validates message and returns list of errors.

        Args:
            text: Message text
            has_buttons: Whether message has buttons

        Returns:
            List of validation errors
        """
        errors = []

        if not self.validate_text_length(text):
            errors.append(
                f"Text exceeds maximum length "
                f"{self.cfg.max_message_length}",
            )

        if has_buttons and not self.validate_buttons_allowed():
            errors.append("Buttons are disabled in configuration")

        return errors
