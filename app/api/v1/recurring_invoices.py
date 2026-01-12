from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_merchant
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.recurring_invoice import RecurringInvoice
from app.schemas.recurring_invoice import (
    RecurringInvoiceCreate,
    RecurringInvoiceUpdate,
    RecurringInvoiceResponse,
)
from app.services.recurring_invoice_service import (
    calculate_initial_next_generation_date,
)


router = APIRouter()


@router.post(
    "",
    response_model=RecurringInvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_recurring_invoice(
    payload: RecurringInvoiceCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    """Create a new recurring invoice template."""
    # Validate that the customer belongs to the merchant
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == payload.customer_id,
            Customer.merchant_id == current_merchant.id,
        )
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or does not belong to merchant",
        )

    next_generation_date = calculate_initial_next_generation_date(
        payload.start_date, payload.day_of_month
    )

    db_template = RecurringInvoice(
        merchant_id=current_merchant.id,
        customer_id=payload.customer_id,
        invoice_number_prefix=payload.invoice_number_prefix,
        description=payload.description,
        amount=payload.amount,
        day_of_month=payload.day_of_month,
        due_date_offset=payload.due_date_offset,
        start_date=payload.start_date,
        end_date=payload.end_date,
        next_generation_date=next_generation_date,
        pause_reminder=payload.pause_reminder,
    )

    db.add(db_template)
    db.commit()
    db.refresh(db_template)

    return RecurringInvoiceResponse.model_validate(db_template)


@router.get("", response_model=List[RecurringInvoiceResponse])
def list_recurring_invoices(
    is_active: Optional[bool] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    """List recurring invoice templates for the current merchant."""
    query = db.query(RecurringInvoice).filter(
        RecurringInvoice.merchant_id == current_merchant.id,
    )

    if is_active is not None:
        query = query.filter(RecurringInvoice.is_active.is_(is_active))

    if customer_id:
        query = query.filter(RecurringInvoice.customer_id == customer_id)

    if start_date:
        query = query.filter(RecurringInvoice.start_date >= start_date)

    if end_date:
        query = query.filter(RecurringInvoice.start_date <= end_date)

    templates = (
        query.order_by(RecurringInvoice.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        RecurringInvoiceResponse.model_validate(template)
        for template in templates
    ]


@router.get("/{template_id}", response_model=RecurringInvoiceResponse)
def get_recurring_invoice(
    template_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    """Get a specific recurring invoice template."""
    template = (
        db.query(RecurringInvoice)
        .filter(
            RecurringInvoice.id == template_id,
            RecurringInvoice.merchant_id == current_merchant.id,
        )
        .first()
    )

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring invoice template not found",
        )

    return RecurringInvoiceResponse.model_validate(template)


@router.put("/{template_id}", response_model=RecurringInvoiceResponse)
def update_recurring_invoice(
    template_id: UUID,
    payload: RecurringInvoiceUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    """Update a recurring invoice template."""
    template = (
        db.query(RecurringInvoice)
        .filter(
            RecurringInvoice.id == template_id,
            RecurringInvoice.merchant_id == current_merchant.id,
        )
        .first()
    )

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring invoice template not found",
        )

    data = payload.model_dump(exclude_unset=True)
    # Track if schedule-related fields changed
    schedule_fields_updated = any(
        field in data for field in ("day_of_month", "start_date")
    )

    for field, value in data.items():
        setattr(template, field, value)

    # Recalculate next_generation_date if schedule changed
    if schedule_fields_updated:
        base_date = max(template.start_date, date.today())
        template.next_generation_date = calculate_initial_next_generation_date(
            base_date, template.day_of_month
        )

    db.commit()
    db.refresh(template)

    return RecurringInvoiceResponse.model_validate(template)


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_recurring_invoice(
    template_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    """Cancel/delete a recurring invoice template (soft-delete via is_active)."""
    template = (
        db.query(RecurringInvoice)
        .filter(
            RecurringInvoice.id == template_id,
            RecurringInvoice.merchant_id == current_merchant.id,
        )
        .first()
    )

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring invoice template not found",
        )

    template.is_active = False
    db.commit()

    return None


@router.post("/{template_id}/pause", response_model=RecurringInvoiceResponse)
def pause_recurring_invoice(
    template_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    """Pause a recurring invoice template."""
    template = (
        db.query(RecurringInvoice)
        .filter(
            RecurringInvoice.id == template_id,
            RecurringInvoice.merchant_id == current_merchant.id,
        )
        .first()
    )

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring invoice template not found",
        )

    template.is_active = False
    db.commit()
    db.refresh(template)

    return RecurringInvoiceResponse.model_validate(template)


@router.post("/{template_id}/resume", response_model=RecurringInvoiceResponse)
def resume_recurring_invoice(
    template_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    """Resume a recurring invoice template."""
    template = (
        db.query(RecurringInvoice)
        .filter(
            RecurringInvoice.id == template_id,
            RecurringInvoice.merchant_id == current_merchant.id,
        )
        .first()
    )

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring invoice template not found",
        )

    template.is_active = True

    # If next_generation_date is in the past, move it forward from today
    if template.next_generation_date < date.today():
        base_date = max(template.start_date, date.today())
        template.next_generation_date = calculate_initial_next_generation_date(
            base_date, template.day_of_month
        )

    db.commit()
    db.refresh(template)

    return RecurringInvoiceResponse.model_validate(template)


