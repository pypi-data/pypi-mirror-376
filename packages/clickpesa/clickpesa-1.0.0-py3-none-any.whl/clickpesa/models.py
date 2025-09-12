"""ClickPesa data models and type definitions."""

from enum import Enum
from typing import List, Optional, Union

from typing_extensions import TypedDict


class Currency(str, Enum):
    """Supported currencies."""

    TZS = "TZS"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    SUCCESS = "SUCCESS"
    SETTLED = "SETTLED"
    PROCESSING = "PROCESSING"
    PENDING = "PENDING"
    FAILED = "FAILED"


class PaymentMethodStatus(str, Enum):
    """Payment method status enumeration."""

    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class SortOrder(str, Enum):
    """Sort order enumeration."""

    ASC = "ASC"
    DESC = "DESC"


class SenderDetails(TypedDict):
    """Sender details from preview response."""

    accountName: str
    accountNumber: str
    accountProvider: str


class PaymentMethod(TypedDict):
    """Payment method information."""

    name: str
    status: PaymentMethodStatus
    fee: Optional[int]
    message: Optional[str]


class PreviewResponse(TypedDict):
    """Response from preview USSD push request."""

    activeMethods: List[PaymentMethod]
    sender: Optional[SenderDetails]


class Customer(TypedDict):
    """Customer information."""

    customerName: str
    customerPhoneNumber: str
    customerEmail: Optional[str]


class TransactionResponse(TypedDict):
    """Transaction response data."""

    id: str
    status: PaymentStatus
    channel: Optional[str]
    orderReference: str
    collectedAmount: Union[str, int]
    collectedCurrency: str
    createdAt: str
    clientId: str
    paymentReference: Optional[str]
    message: Optional[str]
    updatedAt: Optional[str]
    customer: Optional[Customer]


class QueryAllPaymentsParams(TypedDict, total=False):
    """Parameters for querying all payments."""

    startDate: Optional[str]
    endDate: Optional[str]
    status: Optional[PaymentStatus]
    collectedCurrency: Optional[str]
    channel: Optional[str]
    orderReference: Optional[str]
    clientId: Optional[str]
    sortBy: Optional[str]
    orderBy: Optional[SortOrder]
    skip: Optional[int]
    limit: Optional[int]


class QueryAllPaymentsResponse(TypedDict):
    """Response from query all payments."""

    data: List[TransactionResponse]
    totalCount: int
