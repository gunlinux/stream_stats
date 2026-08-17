class DomainError(Exception):
    """Base class for domain-level errors."""


class MessageNotFoundError(DomainError):
    """Raised when a requested message does not exist."""

    def __init__(self, message_id: int) -> None:
        super().__init__(f"Message {message_id} not found")
        self.message_id = message_id
