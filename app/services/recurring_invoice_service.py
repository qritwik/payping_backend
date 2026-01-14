from datetime import date, datetime, timedelta
import calendar
from typing import List

from sqlalchemy.orm import Session, joinedload

from app.models.invoice import Invoice
from app.models.recurring_invoice import RecurringInvoice
from app.models.whatsapp_message import WhatsAppMessage
from app.utils.enums import (
    InvoiceStatus,
    WhatsAppDirection,
    WhatsAppMessageStatus,
    WhatsAppMessageType,
)
from app.tasks.whatsapp import send_whatsapp_message


def _last_day_of_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def calculate_next_generation_date(current_date: date, day_of_month: int) -> date:
    """Calculate the next generation date given a current date and desired day_of_month.

    Adds one month to current_date and sets the day to day_of_month.
    If that day does not exist in the target month (e.g., 31st in February),
    uses the last day of that month instead.
    """
    if day_of_month < 1 or day_of_month > 31:
        raise ValueError("day_of_month must be between 1 and 31")

    # Move to next month
    year = current_date.year
    month = current_date.month + 1
    if month > 12:
        month = 1
        year += 1

    last_day = _last_day_of_month(year, month)
    day = min(day_of_month, last_day)
    return date(year, month, day)


def calculate_initial_next_generation_date(
    start_date: date, day_of_month: int
) -> date:
    """Calculate the first generation date on or after start_date."""
    if day_of_month < 1 or day_of_month > 31:
        raise ValueError("day_of_month must be between 1 and 31")

    # If start_date's day is before or equal to desired day, use this month
    if start_date.day <= day_of_month:
        last_day = _last_day_of_month(start_date.year, start_date.month)
        day = min(day_of_month, last_day)
        return date(start_date.year, start_date.month, day)

    # Otherwise, move to next month
    year = start_date.year
    month = start_date.month + 1
    if month > 12:
        month = 1
        year += 1

    last_day = _last_day_of_month(year, month)
    day = min(day_of_month, last_day)
    return date(year, month, day)


def _should_generate_for_template(template: RecurringInvoice, today: date) -> bool:
    if not template.is_active:
        return False
    if template.next_generation_date is None:
        return False
    if template.next_generation_date > today:
        return False
    if template.end_date and template.next_generation_date > template.end_date:
        return False
    return True


def generate_invoices_from_templates(db: Session) -> List[Invoice]:
    """Generate invoices for all active recurring invoice templates that are due.

    This is intended to be called from a scheduled job (e.g., once per day).
    """
    today = date.today()

    templates: List[RecurringInvoice] = (
        db.query(RecurringInvoice)
        .options(joinedload(RecurringInvoice.customer))
        .filter(
            RecurringInvoice.is_active.is_(True),
            RecurringInvoice.next_generation_date <= today,
        )
        .all()
    )

    generated_invoices: List[Invoice] = []

    for template in templates:
        if not _should_generate_for_template(template, today):
            continue

        generation_date = max(template.next_generation_date, today)

        # Create invoice number - simple prefix + date; can be customized further
        if template.invoice_number_prefix:
            invoice_number = f"{template.invoice_number_prefix}-{generation_date.strftime('%Y%m%d')}"
        else:
            invoice_number = None

        due_date = generation_date + timedelta(days=template.due_date_offset)

        invoice = Invoice(
            merchant_id=template.merchant_id,
            customer_id=template.customer_id,
            recurring_invoice_id=template.id,
            invoice_number=invoice_number,
            description=template.description,
            amount=template.amount,
            due_date=due_date,
            status=InvoiceStatus.UNPAID.value,
            pause_reminder=template.pause_reminder,
        )
        db.add(invoice)
        db.flush()

        # Create WhatsApp message if reminders are not paused
        if not template.pause_reminder:
            message_text = (
                f"Invoice #{invoice.invoice_number or invoice.id} "
                f"for ₹{template.amount} is due on {due_date.isoformat()}"
            )
            whatsapp_message = WhatsAppMessage(
                merchant_id=template.merchant_id,
                customer_id=template.customer_id,
                invoice_id=invoice.id,
                direction=WhatsAppDirection.OUTBOUND.value,
                message_type=WhatsAppMessageType.INVOICE.value,
                status=WhatsAppMessageStatus.PENDING.value,
                message_text=message_text,
            )
            db.add(whatsapp_message)
            db.flush()  # Flush to ensure whatsapp_message is available
            
            # Trigger Celery task to send WhatsApp message
            send_whatsapp_message.delay(template.customer.phone, whatsapp_message.message_text)

        # Update next_generation_date
        next_date = calculate_next_generation_date(
            generation_date, template.day_of_month
        )

        if template.end_date and next_date > template.end_date:
            template.is_active = False
        template.next_generation_date = next_date
        template.updated_at = datetime.utcnow()

        generated_invoices.append(invoice)

    if generated_invoices:
        db.commit()

    return generated_invoices


