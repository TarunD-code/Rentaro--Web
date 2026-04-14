"""
Maintenance Service — Async Tasks (Celery-ready with sync fallback)
"""

import logging
import datetime

logger = logging.getLogger("maintenance_service.tasks")


def send_request_notification(request_data: dict):
    """Notify owner/vendor when a new request is raised."""
    logger.info(
        f"[NOTIFICATION] New service request: {request_data.get('title')} "
        f"(Category: {request_data.get('category')}, Priority: {request_data.get('priority')})"
    )
    logger.info(f"  -> Notifying owner: {request_data.get('owner_id')}")


def send_assignment_notification(assignment_data: dict):
    """Notify vendor of new assignment."""
    logger.info(
        f"[NOTIFICATION] Vendor assigned: {assignment_data.get('vendor_name')} "
        f"to request #{assignment_data.get('request_id')}"
    )
    if assignment_data.get("vendor_email"):
        logger.info(f"  -> Email to: {assignment_data['vendor_email']}")
    if assignment_data.get("vendor_phone"):
        logger.info(f"  -> SMS to: {assignment_data['vendor_phone']}")


def send_resolution_notification(request_data: dict):
    """Notify tenant that their request has been resolved."""
    logger.info(
        f"[NOTIFICATION] Request #{request_data.get('id')} resolved. "
        f"Notifying tenant: {request_data.get('tenant_id')}"
    )


def remind_pending_requests():
    """Daily reminder for unresolved requests older than 48 hours."""
    logger.info("[TASK] Checking for pending maintenance requests...")
    # In production: query DB for open requests > 48h, send reminders
    logger.info("[TASK] Pending request reminders sent (sandbox mode)")


def escalate_urgent_requests():
    """Escalate urgent requests that haven't been assigned within 4 hours."""
    logger.info("[TASK] Checking for unassigned urgent requests...")
    logger.info("[TASK] Escalation check complete (sandbox mode)")
