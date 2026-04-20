"""
PayPal Payment Service for International Markets
Supports USD payments via PayPal for US/Canada/UK/EU markets
"""
import os
import logging
import hmac
import hashlib
import base64
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PayPalService:
    """PayPal payment service for international markets"""

    def __init__(self):
        """Initialize PayPal service with environment variables"""
        self.client_id = os.getenv("PAYPAL_CLIENT_ID", "")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET", "")
        self.webhook_id = os.getenv("PAYPAL_WEBHOOK_ID", "")
        self.sandbox = os.getenv("PAYPAL_SANDBOX", "true").lower() == "true"

        # PayPal API endpoints
        if self.sandbox:
            self.api_base = "https://api-m.sandbox.paypal.com"
            self.checkout_base = "https://www.sandbox.paypal.com"
        else:
            self.api_base = "https://api-m.paypal.com"
            self.checkout_base = "https://www.paypal.com"

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

        logger.info(f"[PayPal] Initialized in {'sandbox' if self.sandbox else 'production'} mode")

    def _get_access_token(self) -> str:
        """Get or refresh PayPal access token"""
        import time
        import httpx

        # Check if token is still valid (with 5 minute buffer)
        if self._access_token and time.time() < self._token_expires_at - 300:
            return self._access_token

        # Get new token
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/v1/oauth2/token",
                    headers=headers,
                    data=data
                )
                response.raise_for_status()
                token_data = response.json()
                self._access_token = token_data["access_token"]
                self._token_expires_at = time.time() + token_data["expires_in"]
                logger.info("[PayPal] Access token obtained successfully")
                return self._access_token
        except Exception as e:
            logger.error(f"[PayPal] Failed to get access token: {e}")
            raise

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for PayPal API requests"""
        token = self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def create_order(
        self,
        amount: float,
        currency: str = "USD",
        description: str = "",
        custom_id: str = "",
        return_url: str = "",
        cancel_url: str = "",
    ) -> Dict[str, Any]:
        """
        Create a PayPal order
        Returns order data including order_id and approval_link
        """
        import httpx

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": custom_id,
                    "description": description,
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}",
                    }
                }
            ],
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url,
                "brand_name": "Danmo Scholar",
                "landing_page": "BILLING",
                "user_action": "PAY_NOW",
            }
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/v2/checkout/orders",
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                order_data = response.json()
                order_id = order_data.get("id")

                # Find approval link
                approval_link = ""
                for link in order_data.get("links", []):
                    if link.get("rel") == "approve":
                        approval_link = link.get("href")
                        break

                logger.info(f"[PayPal] Created order: {order_id}")
                return {
                    "order_id": order_id,
                    "approval_link": approval_link,
                    "status": order_data.get("status"),
                    "raw": order_data,
                }
        except Exception as e:
            logger.error(f"[PayPal] Failed to create order: {e}")
            raise

    def capture_order(self, order_id: str) -> Dict[str, Any]:
        """
        Capture a PayPal order after approval
        """
        import httpx

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/v2/checkout/orders/{order_id}/capture",
                    headers=self._get_headers(),
                    json={}
                )
                response.raise_for_status()
                capture_data = response.json()
                logger.info(f"[PayPal] Captured order: {order_id}")
                return capture_data
        except Exception as e:
            logger.error(f"[PayPal] Failed to capture order {order_id}: {e}")
            raise

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order details from PayPal
        """
        import httpx

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.api_base}/v2/checkout/orders/{order_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"[PayPal] Failed to get order {order_id}: {e}")
            return None

    def verify_webhook(self, payload: bytes, transmission_id: str, transmission_time: str,
                       transmission_sig: str, cert_url: str, auth_algo: str) -> bool:
        """
        Verify PayPal webhook signature via PayPal API
        https://developer.paypal.com/api/rest/webhooks/rest/#verify-webhook-signature
        """
        if not self.webhook_id:
            logger.warning("[PayPal] No webhook ID configured, skipping verification")
            return True

        # 沙箱模式跳过验证（沙箱 webhook 配置可能不完整）
        if self.sandbox:
            logger.info("[PayPal] Sandbox mode, skipping webhook verification")
            return True

        try:
            import httpx
            import json

            headers = self._get_headers()
            verification_payload = {
                "transmission_id": transmission_id,
                "transmission_time": transmission_time,
                "cert_url": cert_url,
                "auth_algo": auth_algo,
                "transmission_sig": transmission_sig,
                "webhook_id": self.webhook_id,
                "webhook_event": json.loads(payload),
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/v1/notifications/verify-webhook-signature",
                    headers=headers,
                    json=verification_payload,
                )
                response.raise_for_status()
                result = response.json()
                status = result.get("verification_status", "").upper()

                if status == "SUCCESS":
                    return True
                else:
                    logger.warning(f"[PayPal] Webhook verification failed: {status}")
                    return False

        except Exception as e:
            logger.error(f"[PayPal] Webhook verification error: {e}")
            return False


class DevPayPalService:
    """Development environment mock PayPal service"""

    def __init__(self):
        self.sandbox = True
        logger.info("[PayPal] Development mode - using mock service")

    def create_order(
        self,
        amount: float,
        currency: str = "USD",
        description: str = "",
        custom_id: str = "",
        return_url: str = "",
        cancel_url: str = "",
    ) -> Dict[str, Any]:
        """Mock order creation"""
        from urllib.parse import urlencode, urlunparse

        order_id = f"ORDER-{custom_id}-{int(amount)}"

        mock_params = {
            "token": order_id,
            "PayerID": "DEV-PAYER-ID",
        }
        query_string = urlencode(mock_params)
        approval_link = urlunparse((
            "",
            "",
            return_url,
            "",
            query_string,
            ""
        ))

        logger.info(f"[PayPal Dev] Mock order created: {order_id}")
        return {
            "order_id": order_id,
            "approval_link": approval_link,
            "status": "CREATED",
            "raw": {"id": order_id, "status": "CREATED"},
        }

    def capture_order(self, order_id: str) -> Dict[str, Any]:
        """Mock order capture"""
        logger.info(f"[PayPal Dev] Mock captured order: {order_id}")
        return {
            "id": order_id,
            "status": "COMPLETED",
            "purchase_units": [
                {
                    "reference_id": order_id.split("-")[1] if "-" in order_id else "",
                    "payments": {
                        "captures": [
                            {
                                "id": "CAPTURE-123",
                                "status": "COMPLETED",
                            }
                        ]
                    }
                }
            ],
        }

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Mock order details"""
        return {
            "id": order_id,
            "status": "COMPLETED",
        }

    def verify_webhook(self, payload: bytes, transmission_id: str, transmission_time: str,
                       transmission_sig: str, cert_url: str, auth_algo: str) -> bool:
        """Mock webhook verification - always true in dev"""
        return True


# Pricing in USD for international market
PAYPAL_PRICING = {
    "single": {
        "name": "Starter",
        "price": 9.99,
        "credits": 6,
        "currency": "USD",
    },
    "semester": {
        "name": "Semester Pro",
        "price": 24.99,
        "credits": 18,
        "currency": "USD",
    },
    "yearly": {
        "name": "Annual Premium",
        "price": 49.99,
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


def get_paypal_service():
    """Get PayPal service instance"""
    is_dev = os.getenv("IS_DEV", "true").lower() == "true"

    if is_dev:
        return DevPayPalService()
    else:
        client_id = os.getenv("PAYPAL_CLIENT_ID")
        if not client_id or client_id == "your-paypal-client-id":
            logger.warning("[PayPal] No Client ID configured, using dev mode")
            return DevPayPalService()
        return PayPalService()
