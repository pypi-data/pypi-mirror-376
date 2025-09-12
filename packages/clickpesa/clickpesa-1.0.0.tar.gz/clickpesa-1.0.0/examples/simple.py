#!/usr/bin/env python3
"""Simple ClickPesa usage example."""

from clickpesa import ClickPesaClient, Currency

# Initialize the client
client = ClickPesaClient(
    client_id="your_client_id",
    api_key="your_api_key"
)

def main():
    try:
        # Preview a payment request
        print("Previewing payment...")
        preview = client.preview_ussd_push(
            amount="1000",
            currency=Currency.TZS,
            order_reference="ORDER123456",
            phone_number="255712345678",
            fetch_sender_details=True
        )

        print("Available payment methods:")
        for method in preview["activeMethods"]:
            print(f"- {method['name']}: {method['status']} (Fee: {method.get('fee', 'N/A')})")

        if preview.get("sender"):
            sender = preview["sender"]
            print(f"Sender: {sender['accountName']} ({sender['accountProvider']})")

        # Initiate the payment
        print("\nInitiating payment...")
        transaction = client.initiate_ussd_push(
            amount="1000",
            currency=Currency.TZS,
            order_reference="ORDER123456",
            phone_number="255712345678"
        )

        print(f"Transaction ID: {transaction['id']}")
        print(f"Status: {transaction['status']}")
        print(f"Channel: {transaction.get('channel', 'Unknown')}")

        # Check payment status
        print("\nChecking payment status...")
        status = client.query_payment_status("ORDER123456")
        print(f"Payment Status: {status[0]['status']}")
        print(f"Message: {status[0]['message']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
