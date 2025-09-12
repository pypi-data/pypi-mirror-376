"""ClickPesa Python SDK

A comprehensive Python library for integrating with the ClickPesa payment gateway API.
"""

from .client import ClickPesaClient
from .exceptions import (
    ClickPesaAPIError,
    ClickPesaAuthError,
    ClickPesaError,
    ClickPesaNotFoundError,
    ClickPesaValidationError,
)
from .models import (
    Currency,
    PaymentMethod,
    PaymentStatus,
    PreviewResponse,
    QueryAllPaymentsParams,
    SenderDetails,
    SortOrder,
    TransactionResponse,
)

__version__ = "1.0.0"
__all__ = [
    "ClickPesaClient",
    "ClickPesaError",
    "ClickPesaAPIError",
    "ClickPesaAuthError",
    "ClickPesaValidationError",
    "ClickPesaNotFoundError",
    "Currency",
    "PaymentStatus",
    "PaymentMethod",
    "SortOrder",
    "PreviewResponse",
    "TransactionResponse",
    "SenderDetails",
    "QueryAllPaymentsParams",
]
