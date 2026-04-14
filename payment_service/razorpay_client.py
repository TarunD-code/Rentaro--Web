"""
Razorpay Client Abstraction Layer

When RAZORPAY_KEY_ID is set in the environment, uses the real Razorpay SDK.
Otherwise, operates in sandbox mode with deterministic mock responses.
"""

import os
import hashlib
import hmac
import uuid
import logging
import datetime

logger = logging.getLogger("payment_service.razorpay")


class RazorpayClient:
    """Unified Razorpay client with automatic sandbox fallback."""

    def __init__(self):
        self.key_id = os.environ.get("RAZORPAY_KEY_ID", "")
        self.key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
        self.is_sandbox = not bool(self.key_id and self.key_secret)

        if self.is_sandbox:
            logger.warning("⚠ Razorpay running in SANDBOX mode — no real payments will be processed")
        else:
            try:
                import razorpay
                self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
                logger.info("✓ Razorpay client initialized with live credentials")
            except ImportError:
                logger.error("razorpay SDK not installed — falling back to sandbox")
                self.is_sandbox = True

    # ── Order Creation ───────────────────────────────────────────────────

    def create_order(self, amount: float, currency: str = "INR",
                     receipt: str = None, notes: dict = None) -> dict:
        """Create a Razorpay payment order. Amount in INR (not paise)."""
        amount_paise = int(amount * 100)
        receipt = receipt or f"rcpt_{uuid.uuid4().hex[:12]}"

        if self.is_sandbox:
            order_id = f"order_mock_{uuid.uuid4().hex[:16]}"
            logger.info(f"[SANDBOX] Created order {order_id} for ₹{amount}")
            return {
                "id": order_id,
                "entity": "order",
                "amount": amount_paise,
                "amount_paid": 0,
                "amount_due": amount_paise,
                "currency": currency,
                "receipt": receipt,
                "status": "created",
                "notes": notes or {},
            }

        order_data = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
            "notes": notes or {},
        }
        return self._client.order.create(data=order_data)

    # ── Payment Verification ─────────────────────────────────────────────

    def verify_payment_signature(self, order_id: str, payment_id: str,
                                  signature: str) -> bool:
        """Verify Razorpay payment signature."""
        if self.is_sandbox:
            # In sandbox, accept any signature that starts with "mock_sig_"
            # or compute a deterministic one
            expected = self._mock_signature(order_id, payment_id)
            is_valid = signature == expected or signature.startswith("mock_sig_")
            logger.info(f"[SANDBOX] Signature verification: {is_valid}")
            return is_valid

        try:
            self._client.utility.verify_payment_signature({
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            })
            return True
        except Exception:
            return False

    # ── Subscription / Mandate ───────────────────────────────────────────

    def create_subscription(self, plan_amount: float, tenant_id: str,
                            total_count: int = 12, notes: dict = None) -> dict:
        """Create a Razorpay subscription for auto-pay mandate."""
        if self.is_sandbox:
            sub_id = f"sub_mock_{uuid.uuid4().hex[:16]}"
            logger.info(f"[SANDBOX] Created subscription {sub_id} for tenant {tenant_id}")
            return {
                "id": sub_id,
                "entity": "subscription",
                "plan_id": f"plan_mock_{uuid.uuid4().hex[:8]}",
                "status": "created",
                "total_count": total_count,
                "paid_count": 0,
                "auth_attempts": 0,
                "notes": notes or {},
                "short_url": f"https://rzp.io/i/mock_{uuid.uuid4().hex[:8]}",
            }

        # Production: Would create plan + subscription via SDK
        # razorpay.Plan.create(...) then razorpay.Subscription.create(...)
        raise NotImplementedError("Live subscription creation needs plan setup")

    def cancel_subscription(self, subscription_id: str) -> dict:
        """Cancel a Razorpay subscription."""
        if self.is_sandbox:
            logger.info(f"[SANDBOX] Cancelled subscription {subscription_id}")
            return {"id": subscription_id, "status": "cancelled"}

        return self._client.subscription.cancel(subscription_id)

    def charge_subscription(self, subscription_id: str, amount: float) -> dict:
        """Charge a subscription (auto-pay). In sandbox, simulates success."""
        if self.is_sandbox:
            payment_id = f"pay_mock_{uuid.uuid4().hex[:16]}"
            logger.info(f"[SANDBOX] Charged ₹{amount} on subscription {subscription_id}")
            return {
                "razorpay_payment_id": payment_id,
                "razorpay_subscription_id": subscription_id,
                "status": "captured",
                "amount": int(amount * 100),
            }

        raise NotImplementedError("Live subscription charging via Razorpay SDK")

    # ── Webhook Signature ────────────────────────────────────────────────

    def verify_webhook_signature(self, body: bytes, signature: str,
                                  webhook_secret: str = None) -> bool:
        """Verify Razorpay webhook signature."""
        if self.is_sandbox:
            logger.info("[SANDBOX] Webhook signature accepted")
            return True

        secret = webhook_secret or os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
        expected = hmac.new(
            secret.encode(), body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    # ── Helpers ──────────────────────────────────────────────────────────

    def _mock_signature(self, order_id: str, payment_id: str) -> str:
        """Generate a deterministic mock signature for sandbox."""
        msg = f"{order_id}|{payment_id}"
        return "mock_sig_" + hashlib.sha256(msg.encode()).hexdigest()[:32]

    def generate_mock_payment_id(self) -> str:
        """Generate a mock payment ID for sandbox verification flow."""
        return f"pay_mock_{uuid.uuid4().hex[:16]}"

    def generate_mock_signature(self, order_id: str, payment_id: str) -> str:
        """Generate a mock signature for sandbox verification flow."""
        return self._mock_signature(order_id, payment_id)


# Singleton instance
razorpay_client = RazorpayClient()
