"""Validators for messages."""



from brostel.config import BrostelConfiguration


class MessageValidator:
    """Validator for message checking."""

    @staticmethod
    def validate_text_length(text: str) -> bool:
        """Validates message text length."""
        return len(text) <= BrostelConfiguration.max_message_length

    @staticmethod
    def validate_buttons_allowed() -> bool:
        """Checks if buttons are allowed."""
        return BrostelConfiguration.allow_buttons

    @classmethod
    def validate_message(
        cls, text: str, has_buttons: bool = False,
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

        if not cls.validate_text_length(text):
            errors.append(
                f"Text exceeds maximum length "
                f"{BrostelConfiguration.max_message_length}",
            )

        if has_buttons and not cls.validate_buttons_allowed():
            errors.append("Buttons are disabled in configuration")

        return errors
