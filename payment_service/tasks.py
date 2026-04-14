"""
Celery-Ready Task Module for Payment Service

These tasks can be called directly (synchronous) or via Celery worker.
When Celery is not configured, functions execute synchronously.

Scheduled execution:
  - send_rent_reminders():         daily at 9:00 AM IST
  - process_auto_rent_charge():    daily at 10:00 AM IST  
  - retry_failed_rent_payments():  daily at 2:00 PM IST
"""

import logging
import datetime
from sqlalchemy.orm import Session
from . import models, database, notifications
from .razorpay_client import razorpay_client

logger = logging.getLogger("payment_service.tasks")

# Try to import Celery; if not available, tasks run synchronously
try:
    from celery import shared_task
except ImportError:
    # Fallback: decorator that just calls the function directly
    def shared_task(func):
        func.delay = func  # Allow .delay() calls without Celery
        func.apply_async = lambda *a, **kw: func()
        return func


@shared_task
def send_rent_reminders():
    """
    Check for rent due within the next 3 days and send reminders.
    Called daily at 9:00 AM.
    """
    logger.info("▶ Running send_rent_reminders task")
    db: Session = database.SessionLocal()

    try:
        today = datetime.datetime.utcnow()
        reminder_window = today + datetime.timedelta(days=3)

        # Find transactions that are created (not yet paid) with upcoming due dates
        upcoming = db.query(models.PaymentTransaction).filter(
            models.PaymentTransaction.status == models.TransactionStatus.created.value,
            models.PaymentTransaction.transaction_type == models.TransactionType.rent.value,
            models.PaymentTransaction.due_date <= reminder_window,
            models.PaymentTransaction.due_date >= today,
        ).all()

        logger.info(f"Found {len(upcoming)} upcoming rent payments to remind")

        for txn in upcoming:
            try:
                notifications.send_rent_reminder(
                    tenant_email=f"{txn.tenant_id}@rentora.test",
                    tenant_phone=None,
                    tenant_name=txn.tenant_id,
                    amount=txn.amount,
                    due_date=txn.due_date,
                    property_title=f"Property #{txn.property_id}",
                )
                logger.info(f"Reminder sent for TXN-{txn.id} to {txn.tenant_id}")
            except Exception as e:
                logger.error(f"Failed to send reminder for TXN-{txn.id}: {e}")

        return {"reminders_sent": len(upcoming)}

    finally:
        db.close()


@shared_task
def process_auto_rent_charge():
    """
    Find active mandates where next_charge_date <= today.
    Create Razorpay charge via mandate, record transaction.
    Called daily at 10:00 AM.
    """
    logger.info("▶ Running process_auto_rent_charge task")
    db: Session = database.SessionLocal()

    try:
        today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        active_mandates = db.query(models.AutoPayMandate).filter(
            models.AutoPayMandate.status == models.MandateStatus.active.value,
            models.AutoPayMandate.next_charge_date <= today,
        ).all()

        logger.info(f"Found {len(active_mandates)} mandates to charge")
        charged = 0

        for mandate in active_mandates:
            try:
                # Find the expected rent amount from recent transactions
                recent_txn = db.query(models.PaymentTransaction).filter(
                    models.PaymentTransaction.agreement_id == mandate.agreement_id,
                    models.PaymentTransaction.transaction_type == models.TransactionType.rent.value,
                ).order_by(models.PaymentTransaction.created_at.desc()).first()

                charge_amount = recent_txn.amount if recent_txn else mandate.max_amount

                # Charge via Razorpay
                charge_result = razorpay_client.charge_subscription(
                    mandate.razorpay_subscription_id, charge_amount
                )

                # Create transaction record
                new_txn = models.PaymentTransaction(
                    agreement_id=mandate.agreement_id,
                    tenant_id=mandate.tenant_id,
                    owner_id="auto",  # Will be resolved from agreement
                    property_id=mandate.property_id,
                    transaction_type=models.TransactionType.rent.value,
                    payment_method=models.PaymentMethod.mandate.value,
                    amount=charge_amount,
                    razorpay_order_id=None,
                    razorpay_payment_id=charge_result.get("razorpay_payment_id"),
                    status=models.TransactionStatus.captured.value,
                    due_date=mandate.next_charge_date,
                    paid_at=datetime.datetime.utcnow(),
                )
                db.add(new_txn)

                # Advance next charge date by 1 month
                next_month = mandate.next_charge_date.replace(day=1) + datetime.timedelta(days=32)
                mandate.next_charge_date = next_month.replace(day=1)

                db.commit()
                charged += 1

                # Send receipt
                notifications.send_payment_receipt(
                    tenant_email=f"{mandate.tenant_id}@rentora.test",
                    tenant_name=mandate.tenant_id,
                    transaction_id=new_txn.id,
                    amount=charge_amount,
                    payment_method="mandate",
                    paid_at=new_txn.paid_at,
                    property_title=f"Property #{mandate.property_id}",
                )

                logger.info(f"Auto-charged ₹{charge_amount} for mandate {mandate.id}")

            except Exception as e:
                logger.error(f"Auto-charge failed for mandate {mandate.id}: {e}")
                notifications.send_autopay_failure(
                    tenant_email=f"{mandate.tenant_id}@rentora.test",
                    tenant_name=mandate.tenant_id,
                    amount=mandate.max_amount,
                    reason=str(e),
                    property_title=f"Property #{mandate.property_id}",
                )

        return {"charged": charged, "total_mandates": len(active_mandates)}

    finally:
        db.close()


@shared_task
def retry_failed_rent_payments():
    """
    Retry failed rent payments (max 3 attempts).
    Called daily at 2:00 PM.
    """
    logger.info("▶ Running retry_failed_rent_payments task")
    db: Session = database.SessionLocal()

    try:
        failed = db.query(models.PaymentTransaction).filter(
            models.PaymentTransaction.status == models.TransactionStatus.failed.value,
            models.PaymentTransaction.transaction_type == models.TransactionType.rent.value,
            models.PaymentTransaction.retry_count < 3,
        ).all()

        logger.info(f"Found {len(failed)} failed payments to retry")
        retried = 0

        for txn in failed:
            try:
                # Check if there's an active mandate for this tenant
                mandate = db.query(models.AutoPayMandate).filter(
                    models.AutoPayMandate.tenant_id == txn.tenant_id,
                    models.AutoPayMandate.agreement_id == txn.agreement_id,
                    models.AutoPayMandate.status == models.MandateStatus.active.value,
                ).first()

                if mandate:
                    charge_result = razorpay_client.charge_subscription(
                        mandate.razorpay_subscription_id, txn.amount
                    )
                    txn.razorpay_payment_id = charge_result.get("razorpay_payment_id")
                    txn.status = models.TransactionStatus.captured.value
                    txn.paid_at = datetime.datetime.utcnow()
                    txn.payment_method = models.PaymentMethod.mandate.value
                    retried += 1
                    logger.info(f"Retry succeeded for TXN-{txn.id}")
                else:
                    logger.info(f"No active mandate for TXN-{txn.id}, skipping retry")

                txn.retry_count += 1
                db.commit()

            except Exception as e:
                txn.retry_count += 1
                txn.failure_reason = str(e)
                db.commit()
                logger.error(f"Retry failed for TXN-{txn.id}: {e}")

        return {"retried": retried, "total_failed": len(failed)}

    finally:
        db.close()
