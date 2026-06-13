"""
Notification service — SMS, Email, WhatsApp.
In production: plug in Twilio/SendGrid/360dialog credentials via settings.
Currently: structured logging + simulated send for dev.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger("gymos.notifications")


class NotificationResult:
    def __init__(self, success: bool, provider: str, recipient: str, message_id: Optional[str] = None, error: Optional[str] = None):
        self.success = success
        self.provider = provider
        self.recipient = recipient
        self.message_id = message_id
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "provider": self.provider,
            "recipient": self.recipient,
            "message_id": self.message_id,
            "error": self.error,
            "timestamp": datetime.utcnow().isoformat(),
        }


def _render_template(template: str, context: Dict[str, str]) -> str:
    """Replace {variable} placeholders with context values."""
    for key, value in context.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template


async def send_sms(phone: str, message: str, context: Dict[str, str] = None) -> NotificationResult:
    """Send SMS via configured provider."""
    from app.core.config import settings
    body = _render_template(message, context or {})

    logger.info(f"[SMS] TO={phone} | MSG={body[:80]}")

    # Production: uncomment and configure
    # if hasattr(settings, 'TWILIO_SID') and settings.TWILIO_SID:
    #     from twilio.rest import Client
    #     client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
    #     msg = client.messages.create(body=body, from_=settings.TWILIO_FROM, to=phone)
    #     return NotificationResult(True, "twilio", phone, msg.sid)

    return NotificationResult(True, "simulated", phone, f"sim_{datetime.utcnow().timestamp():.0f}")


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    context: Dict[str, str] = None,
    html_body: Optional[str] = None,
) -> NotificationResult:
    """Send email via SMTP or SendGrid."""
    from app.core.config import settings
    rendered_subject = _render_template(subject, context or {})
    rendered_body = _render_template(body, context or {})

    logger.info(f"[EMAIL] TO={to_email} | SUBJECT={rendered_subject}")

    # Production SMTP:
    # import smtplib
    # from email.mime.text import MIMEText
    # msg = MIMEText(rendered_body)
    # msg['Subject'] = rendered_subject
    # msg['From'] = settings.SMTP_FROM
    # msg['To'] = to_email
    # with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
    #     s.starttls()
    #     s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    #     s.send_message(msg)

    return NotificationResult(True, "simulated_smtp", to_email, f"email_{datetime.utcnow().timestamp():.0f}")


async def send_whatsapp(phone: str, message: str, context: Dict[str, str] = None) -> NotificationResult:
    """Send WhatsApp message via 360dialog or Twilio."""
    body = _render_template(message, context or {})
    logger.info(f"[WHATSAPP] TO={phone} | MSG={body[:80]}")
    return NotificationResult(True, "simulated_whatsapp", phone, f"wa_{datetime.utcnow().timestamp():.0f}")


async def send_membership_expiry_reminder(
    phone: str, email: Optional[str], name: str, plan: str, expiry_date: str, branch_phone: str = ""
) -> List[NotificationResult]:
    """Send membership expiry reminder via SMS + optional Email."""
    context = {"name": name, "plan": plan, "date": expiry_date, "branch": branch_phone}
    results = []
    results.append(await send_sms(
        phone,
        "Hi {name}, your {plan} membership expires on {date}. Renew at our front desk or call {branch}.",
        context,
    ))
    if email:
        results.append(await send_email(
            email,
            "GymOS — Your membership is expiring soon",
            "Dear {name},\n\nYour {plan} membership expires on {date}.\nPlease visit us to renew.\n\nGymOS Team",
            context,
        ))
    return results


async def send_invoice_notification(
    phone: str, email: Optional[str], name: str, invoice_number: str, amount: str, due_date: str
) -> List[NotificationResult]:
    """Notify member about new invoice."""
    context = {"name": name, "invoice_id": invoice_number, "amount": amount, "date": due_date}
    results = []
    results.append(await send_sms(
        phone,
        "Hi {name}, invoice #{invoice_id} for SAR {amount} is due on {date}. GymOS",
        context,
    ))
    if email:
        results.append(await send_email(
            email, "GymOS Invoice #{invoice_id}",
            "Dear {name},\n\nInvoice #{invoice_id} for SAR {amount} is due on {date}.\n\nGymOS",
            context,
        ))
    return results


async def send_bulk_campaign(
    recipients: List[Dict[str, Any]],
    channel: str,
    template: str,
    subject: str = "",
) -> Dict[str, Any]:
    """Process a bulk marketing campaign send."""
    sent = 0
    failed = 0
    for r in recipients:
        ctx = {
            "name": r.get("name", ""),
            "plan": r.get("plan", ""),
            "date": r.get("date", ""),
            "branch": r.get("branch", ""),
        }
        try:
            if channel == "sms":
                result = await send_sms(r.get("phone", ""), template, ctx)
            elif channel == "email":
                result = await send_email(r.get("email", ""), subject, template, ctx)
            elif channel == "whatsapp":
                result = await send_whatsapp(r.get("phone", ""), template, ctx)
            else:
                result = NotificationResult(False, channel, r.get("phone", ""), error="Unknown channel")
            if result.success:
                sent += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Bulk send error for {r}: {e}")
            failed += 1
    return {"sent": sent, "failed": failed, "total": len(recipients)}
