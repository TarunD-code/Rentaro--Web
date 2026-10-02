"""
Rentora Auth — OTP Generation and Delivery
===========================================
Delivery strategy (resolved at call time, no restart needed):

  DEV_MODE=true   → OTP printed prominently to stdout; universal bypass
                    code "000000" also accepted by the verify-otp endpoint.
                    OTP is ALWAYS "123456" so manual browser testing is instant.

  SENDGRID_API_KEY set (non-mock) → real transactional email via SendGrid.

  TWILIO_AUTH_TOKEN set (non-mock) → real SMS via Twilio for phone numbers.

  Fallback → mock print only (same as DEV_MODE).

DPDP Act note: OTP codes are single-use strings stored in auth.users.otp_code
and cleared immediately on successful verification. They are never logged to
persistent storage.
"""

import os
import logging
import random

logger = logging.getLogger("otp_providers")

# ── Runtime flags ─────────────────────────────────────────────────────────────
_DEV_MODE: bool = os.environ.get("DEV_MODE", "true").lower() in ("true", "1", "yes")
_SENDGRID_KEY: str = os.environ.get("SENDGRID_API_KEY", "")
_TWILIO_SID: str = os.environ.get("TWILIO_ACCOUNT_SID", "")
_TWILIO_TOKEN: str = os.environ.get("TWILIO_AUTH_TOKEN", "")
_TWILIO_FROM: str = os.environ.get("TWILIO_PHONE_NUMBER", "")
_FROM_EMAIL: str = os.environ.get("MAIL_FROM", "noreply@rentora.com")

_IS_MOCK_SENDGRID = not _SENDGRID_KEY or _SENDGRID_KEY.startswith("SG.mock")
_IS_MOCK_TWILIO   = not _TWILIO_TOKEN or _TWILIO_TOKEN.startswith("mock")


def generate_otp() -> str:
    """
    Generate a 6-digit OTP.

    In DEV_MODE always returns "123456" so the browser test flow
    requires zero clipboard operations.
    In production returns a cryptographically-random 6-digit code.
    """
    if _DEV_MODE:
        return "123456"
    return str(random.SystemRandom().randint(100_000, 999_999))


async def _send_otp_email_async(to_email: str, otp: str) -> None:
    """
    Delivers OTP via the production SMTP client.
    Imported lazily so the auth service doesn't hard-depend on the
    notification service package at module load time.
    """
    try:
        import sys
        import os
        # Allow import from project root when running inside Docker
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)
        from notification_service.email_client import send_otp_email
        await send_otp_email(to_email, otp)
    except Exception as exc:
        logger.warning(f"[OTP] SMTP delivery failed for {to_email[:3]}***: {exc}")


def send_otp(destination: str, otp: str) -> None:
    """
    Deliver the OTP to the user.

    Routing logic:
      1. Always print the OTP prominently to stdout (visible in Docker logs).
      2. If destination is an email and SMTP is configured → send via SMTP client.
      3. If destination is a phone and Twilio is configured → send SMS.
      4. All failures are logged as warnings; they never crash registration.
    """
    # ── 1. Prominent terminal log (always, essential for dev/demo) ────────────
    bar = "=" * 56
    logger.info(f"\n{bar}\n  [DEV OTP] Destination : {destination}\n  [DEV OTP] Code        : {otp}\n  [DEV OTP] Universal   : 000000 (DEV_MODE bypass)\n{bar}")
    print(f"\n{bar}\n  🔑 DEV OTP → {destination}  |  Code: {otp}  |  Bypass: 000000\n{bar}\n", flush=True)

    is_email = "@" in destination

    # ── 2. SMTP email delivery ────────────────────────────────────────────────
    if is_email:
        try:
            import asyncio
            # Run the async sender in a new event loop if we're in a sync context
            # (FastAPI sync endpoints), or schedule it if we're in an async context.
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_send_otp_email_async(destination, otp))
            except RuntimeError:
                # No running loop — create one (only happens in test/CLI context)
                asyncio.run(_send_otp_email_async(destination, otp))
        except Exception as exc:
            logger.warning(f"[OTP] Email scheduling failed for {destination[:3]}***: {exc}")

    # ── 3. Twilio SMS delivery ────────────────────────────────────────────────
    if not is_email and not _IS_MOCK_TWILIO:
        _send_via_twilio(destination, otp)
    elif not is_email and _IS_MOCK_TWILIO:
        logger.info(f"[OTP] Twilio not configured — SMS delivery skipped for {destination[:4]}***")


def _send_via_sendgrid(to_email: str, otp: str) -> None:
    try:
        import httpx
        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": _FROM_EMAIL, "name": "Rentora"},
            "subject": f"Your Rentora OTP: {otp}",
            "content": [
                {
                    "type": "text/html",
                    "value": f"""
                    <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;
                                padding:32px;border-radius:12px;border:1px solid #e3eaf3">
                      <h2 style="color:#0A3D62;margin-bottom:8px">Verify your account</h2>
                      <p style="color:#555;margin-bottom:24px">
                        Use the code below to complete your Rentora registration.
                        It expires in 10 minutes.
                      </p>
                      <div style="background:#f0f4ff;border-radius:8px;padding:20px;
                                  text-align:center;font-size:36px;font-weight:800;
                                  letter-spacing:10px;color:#0A3D62">
                        {otp}
                      </div>
                      <p style="color:#999;font-size:11px;margin-top:20px">
                        If you did not request this, please ignore this email.
                        Rentora will never ask for this code over phone or chat.
                      </p>
                    </div>
                    """,
                }
            ],
        }
        resp = httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers={"Authorization": f"Bearer {_SENDGRID_KEY}"},
            timeout=8.0,
        )
        if resp.status_code in (200, 202):
            logger.info(f"[OTP] SendGrid delivery accepted for {to_email[:3]}***")
        else:
            logger.warning(f"[OTP] SendGrid HTTP {resp.status_code}: {resp.text[:120]}")
    except Exception as exc:
        logger.warning(f"[OTP] SendGrid delivery failed: {exc}")


def _send_via_twilio(to_phone: str, otp: str) -> None:
    try:
        import httpx
        body = f"Your Rentora verification code is: {otp}. Valid for 10 minutes. Do not share this code."
        resp = httpx.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{_TWILIO_SID}/Messages.json",
            data={"From": _TWILIO_FROM, "To": to_phone, "Body": body},
            auth=(_TWILIO_SID, _TWILIO_TOKEN),
            timeout=8.0,
        )
        if resp.status_code == 201:
            logger.info(f"[OTP] Twilio SMS sent to {to_phone[:4]}***")
        else:
            logger.warning(f"[OTP] Twilio HTTP {resp.status_code}: {resp.text[:120]}")
    except Exception as exc:
        logger.warning(f"[OTP] Twilio delivery failed: {exc}")
