"""
Onboarding Service — Async Tasks
"""
import logging
logger = logging.getLogger("onboarding_service.tasks")


def send_signature_reminders():
    """Daily reminders for pending signatures."""
    logger.info("[TASK] Checking for pending agreement signatures...")
    logger.info("[TASK] Signature reminders sent (sandbox mode)")


def notify_onboarding_completion(tenant_id: str, onboarding_id: int):
    """Notify tenant and owner when onboarding is verified."""
    logger.info(f"[NOTIFICATION] Onboarding #{onboarding_id} completed for {tenant_id}")


def notify_agreement_ready(agreement_id: int, tenant_id: str, owner_id: str):
    """Notify both parties when agreement is ready for signing."""
    logger.info(f"[NOTIFICATION] Agreement #{agreement_id} ready: {tenant_id} ↔ {owner_id}")


def notify_signature_received(agreement_id: int, signer: str, role: str):
    """Notify when a party signs the agreement."""
    logger.info(f"[NOTIFICATION] Agreement #{agreement_id} signed by {role}: {signer}")
