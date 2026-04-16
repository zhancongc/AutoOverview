"""
Paddle Payment Service for International Markets
Supports USD payments via credit cards for US/Canada/UK/EU markets
"""
import os
import logging
import hmac
import hashlib
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PaddleService:
    """Paddle payment service for international markets"""

    def __init__(self):
        """Initialize Paddle service with environment variables"""
        self.api_key = os.getenv("PADDLE_API_KEY", "")
        self.vendor_id = os.getenv("PADDLE_VENDOR_ID", "")
        self.client_side_token = os.getenv("PADDLE_CLIENT_SIDE_TOKEN", "")
        self.webhook_secret = os.getenv("PADDLE_WEBHOOK_SECRET", "")
        self.sandbox = os.getenv("PADDLE_SANDBOX", "true").lower() == "true"

        # Paddle API endpoints
        if self.sandbox:
            self.api_base = "https://sandbox-api.paddle.com"
            self.checkout_base = "https://sandbox-checkout.paddle.com"
        else:
            self.api_base = "https://api.paddle.com"
            self.checkout_base = "https://checkout.paddle.com"

        logger.info(f"[Paddle] Initialized in {'sandbox' if self.sandbox else 'production'} mode")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Paddle API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def create_price(self, amount: float, currency: str = "USD") -> str:
        """
        Create a price in Paddle (returns price_id)
        Amount is in dollars, Paddle uses cents
        """
        import httpx

        amount_cents = int(amount * 100)
        payload = {
            "product_id": os.getenv("PADDLE_PRODUCT_ID", "PROD_123456"),
            "amount": amount_cents,
            "currency": currency,
            "description": f"AutoOverview Review Credits - {amount} USD",
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/v2/prices",
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                price_id = data.get("id")
                logger.info(f"[Paddle] Created price: {price_id} for {amount} {currency}")
                return price_id
        except Exception as e:
            logger.error(f"[Paddle] Failed to create price: {e}")
            raise

    def create_checkout_link(
        self,
        price_id: str,
        customer_email: str,
        custom_data: Dict[str, Any],
        success_url: str,
    ) -> str:
        """
        Create a Paddle checkout link
        """
        import httpx

        payload = {
            "items": [
                {
                    "price_id": price_id,
                    "quantity": 1,
                }
            ],
            "customer_email": customer_email,
            "custom_data": custom_data,
            "settings": {
                "success_url": success_url,
                "display_mode": "overlay",
            },
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/v2/checkout-links",
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                checkout_url = data.get("url")
                logger.info(f"[Paddle] Created checkout link: {checkout_url}")
                return checkout_url
        except Exception as e:
            logger.error(f"[Paddle] Failed to create checkout link: {e}")
            raise

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """
        Verify Paddle webhook signature
        """
        if not self.webhook_secret:
            logger.warning("[Paddle] No webhook secret configured, skipping verification")
            return True

        # Paddle uses HMAC-SHA256 for webhook signatures
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Compare signatures securely
        return hmac.compare_digest(expected_signature, signature)

    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details from Paddle
        """
        import httpx

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.api_base}/v2/transactions/{transaction_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"[Paddle] Failed to get transaction {transaction_id}: {e}")
            return None


class DevPaddleService:
    """Development environment mock Paddle service"""

    def __init__(self):
        self.sandbox = True
        logger.info("[Paddle] Development mode - using mock service")

    def create_price(self, amount: float, currency: str = "USD") -> str:
        """Mock price creation"""
        price_id = f"pri_dev_{amount}_{currency}"
        logger.info(f"[Paddle Dev] Mock price created: {price_id}")
        return price_id

    def create_checkout_link(
        self,
        price_id: str,
        customer_email: str,
        custom_data: Dict[str, Any],
        success_url: str,
    ) -> str:
        """
        Mock checkout link - returns a URL that will auto-complete
        """
        from urllib.parse import urlencode, urlunparse

        # Extract amount from price_id
        amount = price_id.split("_")[2]

        mock_params = {
            "success": "true",
            "price_id": price_id,
            "email": customer_email,
            "amount": amount,
        }
        query_string = urlencode(mock_params)
        mock_url = urlunparse((
            "",
            "",
            success_url,
            "",
            query_string,
            ""
        ))

        logger.info(f"[Paddle Dev] Mock checkout link: {mock_url}")
        return mock_url

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Mock webhook verification - always true in dev"""
        return True

    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Mock transaction details"""
        return {
            "id": transaction_id,
            "status": "completed",
            "amount": 5.99,
        }


# Pricing in USD for international market
PADDLE_PRICING = {
    "single": {
        "name": "Starter",
        "price": 5.99,
        "credits": 6,
        "currency": "USD",
    },
    "semester": {
        "name": "Semester Pro",
        "price": 27.99,
        "credits": 20,
        "currency": "USD",
    },
    "yearly": {
        "name": "Annual Premium",
        "price": 64.99,
        "credits": 50,
        "currency": "USD",
    },
    "unlock": {
        "name": "Unlock Single Export",
        "price": 9.99,
        "credits": 0,
        "currency": "USD",
    },
}


def get_paddle_service():
    """Get Paddle service instance"""
    is_dev = os.getenv("IS_DEV", "true").lower() == "true"

    if is_dev:
        return DevPaddleService()
    else:
        api_key = os.getenv("PADDLE_API_KEY")
        if not api_key or api_key == "your-paddle-api-key":
            logger.warning("[Paddle] No API key configured, using dev mode")
            return DevPaddleService()
        return PaddleService()
