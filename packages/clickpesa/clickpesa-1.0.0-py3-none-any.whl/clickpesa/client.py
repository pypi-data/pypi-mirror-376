"""ClickPesa API client implementation."""

import time
from typing import Dict, List, Optional

import requests

from .exceptions import (
    ClickPesaAPIError,
    ClickPesaAuthError,
    ClickPesaNotFoundError,
    ClickPesaValidationError,
)
from .models import (
    Currency,
    PaymentMethod,
    PreviewResponse,
    QueryAllPaymentsParams,
    QueryAllPaymentsResponse,
    TransactionResponse,
)


class ClickPesaClient:
    """ClickPesa API client for handling payments and transactions."""

    def __init__(
        self,
        client_id: str,
        api_key: str,
        base_url: str = "https://api.clickpesa.com/third-parties",
    ) -> None:
        """Initialize the ClickPesa client.

        Args:
            client_id: Your Application Client ID
            api_key: Your Application API Key
            base_url: Base URL for the API (defaults to production URL)
        """
        self.client_id: str = client_id
        self.api_key: str = api_key
        self.base_url: str = base_url.rstrip("/")
        self._token: Optional[str] = None
        self._token_expiry: Optional[float] = None

    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get headers for API requests.

        Args:
            include_auth: Whether to include authorization header

        Returns:
            Dictionary of headers
        """
        headers = {"Content-Type": "application/json"}

        if include_auth:
            if not self._is_token_valid():
                self._generate_token()
            if self._token:
                headers["Authorization"] = self._token

        return headers

    def _is_token_valid(self) -> bool:
        """Check if the current token is valid.

        Returns:
            True if token exists and hasn't expired
        """
        if not self._token or not self._token_expiry:
            return False
        return time.time() < self._token_expiry

    def _generate_token(self) -> None:
        """Generate a new JWT token."""
        url = f"{self.base_url}/generate-token"
        headers = {
            "client-id": self.client_id,
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, headers=headers, timeout=30)
            self._handle_response(response)

            data = response.json()
            self._token = data["token"]
            self._token_expiry = time.time() + (59 * 60)

        except requests.exceptions.RequestException as e:
            raise ClickPesaAPIError(f"Failed to generate token: {str(e)}")

    def _handle_response(self, response: requests.Response) -> None:
        """Handle API response and raise appropriate exceptions.

        Args:
            response: The HTTP response object

        Raises:
            ClickPesaAuthError: For authentication errors (401, 403)
            ClickPesaNotFoundError: For not found errors (404)
            ClickPesaValidationError: For validation errors (400, 409)
            ClickPesaAPIError: For other API errors
        """
        if response.status_code == 200:
            return

        try:
            error_data = response.json()
            message = error_data.get("message", f"HTTP {response.status_code}")
        except ValueError:
            message = f"HTTP {response.status_code}: {response.text}"

        if response.status_code in [401, 403]:
            raise ClickPesaAuthError(message, response.status_code)
        elif response.status_code == 404:
            raise ClickPesaNotFoundError(message, response.status_code)
        elif response.status_code in [400, 409]:
            raise ClickPesaValidationError(message, response.status_code)
        else:
            raise ClickPesaAPIError(message, response.status_code)

    def preview_ussd_push(
        self,
        amount: str,
        currency: Currency,
        order_reference: str,
        phone_number: Optional[str] = None,
        fetch_sender_details: bool = False,
        checksum: Optional[str] = None,
    ) -> PreviewResponse:
        """Preview USSD push request to validate payment details.

        Args:
            amount: Payment amount
            currency: Payment currency (TZS)
            order_reference: Unique order reference
            phone_number: Mobile phone number (optional)
            fetch_sender_details: Whether to fetch sender details
            checksum: Generated checksum if enabled

        Returns:
            PreviewResponse containing active payment methods and sender details

        Raises:
            ClickPesaValidationError: For invalid request data
            ClickPesaNotFoundError: If no payment methods available
            ClickPesaAPIError: For other API errors
        """
        url = f"{self.base_url}/payments/preview-ussd-push-request"
        payload = {
            "amount": amount,
            "currency": currency.value,
            "orderReference": order_reference,
            "fetchSenderDetails": fetch_sender_details,
        }

        if phone_number:
            payload["phoneNumber"] = phone_number
        if checksum:
            payload["checksum"] = checksum

        response = requests.post(
            url, json=payload, headers=self._get_headers(), timeout=30
        )
        self._handle_response(response)
        return response.json()

    def initiate_ussd_push(
        self,
        amount: str,
        currency: Currency,
        order_reference: str,
        phone_number: str,
        checksum: Optional[str] = None,
    ) -> TransactionResponse:
        """Initiate USSD push request to customer's mobile device.

        Args:
            amount: Payment amount
            currency: Payment currency (TZS)
            order_reference: Unique order reference
            phone_number: Mobile phone number to receive USSD push
            checksum: Generated checksum if enabled

        Returns:
            TransactionResponse with transaction details

        Raises:
            ClickPesaValidationError: For invalid request data
            ClickPesaNotFoundError: If no payment methods available
            ClickPesaAPIError: For other API errors
        """
        url = f"{self.base_url}/payments/initiate-ussd-push-request"
        payload = {
            "amount": amount,
            "currency": currency.value,
            "orderReference": order_reference,
            "phoneNumber": phone_number,
        }

        if checksum:
            payload["checksum"] = checksum

        response = requests.post(
            url, json=payload, headers=self._get_headers(), timeout=30
        )
        self._handle_response(response)
        return response.json()

    def query_payment_status(self, order_reference: str) -> List[TransactionResponse]:
        """Query payment status by order reference.

        Args:
            order_reference: The order reference to query

        Returns:
            TransactionResponse with payment details and status

        Raises:
            ClickPesaNotFoundError: If payment not found
            ClickPesaAPIError: For other API errors
        """
        url = f"{self.base_url}/payments/{order_reference}"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        self._handle_response(response)
        return response.json()

    def query_all_payments(
        self, params: Optional[QueryAllPaymentsParams] = None
    ) -> QueryAllPaymentsResponse:
        """Query all payments with filtering and pagination.

        Args:
            params: Query parameters for filtering, sorting, and pagination

        Returns:
            QueryAllPaymentsResponse with payment data and total count

        Raises:
            ClickPesaAPIError: For API errors
        """
        url = f"{self.base_url}/payments/all"
        query_params = {}

        if params:
            for key, value in params.items():
                if value is not None:
                    if hasattr(value, "value"):
                        query_params[key] = value.value
                    else:
                        query_params[key] = value

        response = requests.get(
            url, params=query_params, headers=self._get_headers(), timeout=30
        )
        self._handle_response(response)
        return response.json()

    def get_payment_methods(
        self,
        amount: str,
        currency: Currency,
        order_reference: str,
        phone_number: Optional[str] = None,
    ) -> List[PaymentMethod]:
        """Get available payment methods for a transaction.

        This is a convenience method that calls preview_ussd_push and returns
        only the active payment methods.

        Args:
            amount: Payment amount
            currency: Payment currency
            order_reference: Unique order reference
            phone_number: Mobile phone number (optional)

        Returns:
            List of available payment methods
        """
        preview = self.preview_ussd_push(
            amount=amount,
            currency=currency,
            order_reference=order_reference,
            phone_number=phone_number,
        )
        return preview["activeMethods"]

    def check_payment_completed(self, order_reference: str) -> bool:
        """Check if a payment has been completed successfully.

        Args:
            order_reference: The order reference to check

        Returns:
            True if payment is SUCCESS or SETTLED, False otherwise
        """
        try:
            payment = self.query_payment_status(order_reference)
            return payment["status"] in ["SUCCESS", "SETTLED"]
        except ClickPesaNotFoundError:
            return False
