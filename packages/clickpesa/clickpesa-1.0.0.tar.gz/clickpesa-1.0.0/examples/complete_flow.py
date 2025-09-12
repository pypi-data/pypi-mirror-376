#!/usr/bin/env python3
"""Complete ClickPesa integration example with error handling."""

import time
from typing import Optional

from clickpesa import (
    ClickPesaClient,
    ClickPesaError,
    Currency,
    PaymentStatus,
    QueryAllPaymentsParams,
    SortOrder,
)


class PaymentProcessor:
    """Example payment processor using ClickPesa."""

    def __init__(self, client_id: str, api_key: str):
        self.client = ClickPesaClient(client_id, api_key)

    def process_payment(
        self,
        amount: str,
        phone_number: str,
        order_reference: str
    ) -> Optional[str]:
        """Process a complete payment flow.

        Returns:
            Transaction ID if successful, None if failed
        """
        try:
            # Step 1: Preview the payment
            print(f"Processing payment for {amount} TZS...")
            preview = self.client.preview_ussd_push(
                amount=amount,
                currency=Currency.TZS,
                order_reference=order_reference,
                phone_number=phone_number,
                fetch_sender_details=True
            )

            # Check if any payment methods are available
            available_methods = [
                method for method in preview["activeMethods"]
                if method["status"] == "AVAILABLE"
            ]

            if not available_methods:
                print("No payment methods available")
                return None

            print("Available payment methods:")
            for method in available_methods:
                print(f"  - {method['name']} (Fee: {method.get('fee', 0)} TZS)")

            # Step 2: Initiate the payment
            transaction = self.client.initiate_ussd_push(
                amount=amount,
                currency=Currency.TZS,
                order_reference=order_reference,
                phone_number=phone_number
            )

            transaction_id = transaction["id"]
            print(f"Payment initiated. Transaction ID: {transaction_id}")
            print(f"Initial status: {transaction['status']}")

            # Step 3: Monitor payment status
            return self._monitor_payment(order_reference, max_wait_time=300)

        except ClickPesaError as e:
            print(f"ClickPesa error: {e.message}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def _monitor_payment(self, order_reference: str, max_wait_time: int = 300) -> Optional[str]:
        """Monitor payment status until completion or timeout.

        Args:
            order_reference: Order reference to monitor
            max_wait_time: Maximum time to wait in seconds

        Returns:
            Transaction ID if successful, None if failed or timeout
        """
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                status_response = self.client.query_payment_status(order_reference)
                status_response = status_response[0] # we get a list even though its for a specific trx
                current_status = status_response["status"]

                print(f"Payment status: {current_status}")

                if current_status in [PaymentStatus.SUCCESS, PaymentStatus.SETTLED]:
                    print("Payment completed successfully!")
                    print(f"Amount collected: {status_response['collectedAmount']} {status_response['collectedCurrency']}")
                    if status_response.get("customer"):
                        customer = status_response["customer"]
                        print(f"Customer: {customer['customerName']} ({customer['customerPhoneNumber']})")
                    return status_response["id"]

                elif current_status == PaymentStatus.FAILED:
                    print("Payment failed!")
                    print(f"Message: {status_response.get('message', 'No error message')}")
                    return None

                elif current_status in [PaymentStatus.PROCESSING, PaymentStatus.PENDING]:
                    print("Payment still processing... waiting 10 seconds")
                    time.sleep(10)

            except ClickPesaError as e:
                print(f"Error checking payment status: {e.message}")
                time.sleep(10)

        print("Payment monitoring timeout!")
        return None

    def get_payment_history(self, days: int = 7) -> None:
        """Get payment history for the last N days."""
        try:
            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            params: QueryAllPaymentsParams = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "sortBy": "createdAt",
                "orderBy": SortOrder.DESC,
                "limit": 50
            }

            response = self.client.query_all_payments(params)
            payments = response["data"]
            total_count = response["totalCount"]

            print(f"\nPayment History (Last {days} days)")
            print(f"Total payments: {total_count}")
            print("-" * 80)

            for payment in payments:
                print(f"Order: {payment['orderReference']}")
                print(f"Status: {payment['status']}")
                print(f"Amount: {payment['collectedAmount']} {payment['collectedCurrency']}")
                print(f"Date: {payment['createdAt']}")
                if payment.get("customer"):
                    print(f"Customer: {payment['customer']['customerName']}")
                print("-" * 40)

        except ClickPesaError as e:
            print(f"Error fetching payment history: {e.message}")


def main():
    """Example usage."""
    # Initialize with your credentials
    processor = PaymentProcessor(
        client_id="your_client_id",
        api_key="your_api_key"
    )

    # Example 1: Process a single payment
    transaction_id = processor.process_payment(
        amount="5000",
        phone_number="255712345678",
        order_reference="ORDER789"
    )

    if transaction_id:
        print(f"Payment successful! Transaction ID: {transaction_id}")
    else:
        print("Payment failed or was cancelled")

    # Example 2: Get payment history
    processor.get_payment_history(days=30)

    # Example 3: Check if a specific payment was completed
    is_completed = processor.client.check_payment_completed("ORDER789")
    print(f"Payment ORDER789 completed: {is_completed}")


if __name__ == "__main__":
    main()
