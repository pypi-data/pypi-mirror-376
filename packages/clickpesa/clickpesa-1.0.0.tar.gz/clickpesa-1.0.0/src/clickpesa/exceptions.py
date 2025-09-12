"""ClickPesa exception classes."""

from typing import Optional


class ClickPesaError(Exception):
    """Base exception class for ClickPesa SDK."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ClickPesaAPIError(ClickPesaError):
    """Raised when the API returns an error response."""

    pass


class ClickPesaAuthError(ClickPesaError):
    """Raised when authentication fails."""

    pass


class ClickPesaValidationError(ClickPesaError):
    """Raised when request validation fails."""

    pass


class ClickPesaNotFoundError(ClickPesaError):
    """Raised when a resource is not found."""

    pass
