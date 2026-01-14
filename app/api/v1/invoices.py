from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from app.core.database import get_db
from app.core.security import get_current_merchant
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.whatsapp_message import WhatsAppMessage
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceWithMessagesResponse,
    InvoiceWithMerchantResponse,
    WhatsAppMessageResponse
)
from app.schemas.merchant import MerchantResponse
from app.utils.enums import InvoiceStatus, WhatsAppDirection, WhatsAppMessageType, WhatsAppMessageStatus
from app.tasks.whatsapp import send_whatsapp_message

router = APIRouter()



@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice: InvoiceCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Create a new invoice for a customer"""
    # Validate merchant owns customer
    customer = db.query(Customer).filter(
        Customer.id == invoice.customer_id,
        Customer.merchant_id == current_merchant.id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or does not belong to merchant"
        )
    
    # Create invoice with UNPAID status
    db_invoice = Invoice(
        merchant_id=current_merchant.id,
        customer_id=invoice.customer_id,
        invoice_number=invoice.invoice_number,
        description=invoice.description,
        amount=invoice.amount,
        due_date=invoice.due_date,
        status=InvoiceStatus.UNPAID.value,
        pause_reminder=invoice.pause_reminder
    )
    db.add(db_invoice)
    db.flush()  # Flush to get invoice ID
    
    # If pause_reminder is False, create WhatsApp message
    if not invoice.pause_reminder:
        whatsapp_message = WhatsAppMessage(
            merchant_id=current_merchant.id,
            customer_id=invoice.customer_id,
            invoice_id=db_invoice.id,
            direction=WhatsAppDirection.OUTBOUND.value,
            message_type=WhatsAppMessageType.INVOICE.value,
            status=WhatsAppMessageStatus.PENDING.value,
            message_text=f"Invoice #{db_invoice.invoice_number or db_invoice.id} for ₹{invoice.amount}"
        )
        db.add(whatsapp_message)
        db.flush()  # Flush to get message ID
        
        # Trigger Celery task to send WhatsApp message
        send_whatsapp_message.delay(customer.phone, whatsapp_message.message_text)
    
    db.commit()
    db.refresh(db_invoice)
    
    return InvoiceResponse.model_validate(db_invoice)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: UUID,
    invoice_update: InvoiceUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Update invoice details (only if not PAID)"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.merchant_id == current_merchant.id,
        Invoice.deleted_at.is_(None)  # Not soft deleted
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Check if invoice is PAID
    if invoice.status == InvoiceStatus.PAID.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a paid invoice"
        )
    
    # Update fields
    update_data = invoice_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    db.commit()
    db.refresh(invoice)
    
    return InvoiceResponse.model_validate(invoice)


@router.get("", response_model=List[InvoiceResponse])
def get_all_invoices(
    status_filter: Optional[str] = Query(None, alias="status"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Get all invoices for the merchant with filters and pagination"""
    query = db.query(Invoice).filter(
        Invoice.merchant_id == current_merchant.id,
        Invoice.deleted_at.is_(None)  # Not soft deleted
    )
    
    # Apply filters
    if status_filter:
        query = query.filter(Invoice.status == status_filter.upper())
    
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    
    if start_date:
        query = query.filter(Invoice.created_at >= datetime.combine(start_date, datetime.min.time()))
    
    if end_date:
        query = query.filter(Invoice.created_at <= datetime.combine(end_date, datetime.max.time()))
    
    # Apply pagination
    invoices = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    
    return [InvoiceResponse.model_validate(invoice) for invoice in invoices]


@router.get("/{invoice_id}", response_model=InvoiceWithMessagesResponse)
def get_invoice_by_id(
    invoice_id: UUID,
    include_messages: bool = Query(False, alias="include_messages"),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Get a specific invoice by ID, optionally with WhatsApp messages"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.merchant_id == current_merchant.id,
        Invoice.deleted_at.is_(None)  # Not soft deleted
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    response_data = InvoiceResponse.model_validate(invoice).model_dump()
    
    # Optionally include WhatsApp messages
    if include_messages:
        messages = db.query(WhatsAppMessage).filter(
            WhatsAppMessage.invoice_id == invoice_id
        ).order_by(WhatsAppMessage.created_at.desc()).all()
        response_data["whatsapp_messages"] = [
            WhatsAppMessageResponse.model_validate(msg).model_dump() for msg in messages
        ]
    else:
        response_data["whatsapp_messages"] = None
    
    return InvoiceWithMessagesResponse(**response_data)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Soft delete an invoice (only if UNPAID)"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.merchant_id == current_merchant.id,
        Invoice.deleted_at.is_(None)  # Not already deleted
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Only allow deletion if status is UNPAID
    if invoice.status != InvoiceStatus.UNPAID.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete unpaid invoices"
        )
    
    # Soft delete
    invoice.deleted_at = datetime.utcnow()
    db.commit()
    
    return None


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceResponse)
def mark_invoice_as_paid(
    invoice_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Mark an invoice as paid"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.merchant_id == current_merchant.id,
        Invoice.deleted_at.is_(None)  # Not soft deleted
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Update status to PAID
    invoice.status = InvoiceStatus.PAID.value
    invoice.paid_at = datetime.utcnow()
    
    db.commit()
    db.refresh(invoice)
    
    return InvoiceResponse.model_validate(invoice)


@router.post("/{invoice_id}/send-followup", response_model=WhatsAppMessageResponse, status_code=status.HTTP_201_CREATED)
def send_followup(
    invoice_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Send a manual follow-up WhatsApp message for an unpaid invoice"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.merchant_id == current_merchant.id,
        Invoice.deleted_at.is_(None)  # Not soft deleted
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Check if invoice is unpaid
    if invoice.status == InvoiceStatus.PAID.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send follow-up for paid invoice"
        )
    
    # Create follow-up WhatsApp message
    whatsapp_message = WhatsAppMessage(
        merchant_id=current_merchant.id,
        customer_id=invoice.customer_id,
        invoice_id=invoice.id,
        direction=WhatsAppDirection.OUTBOUND.value,
        message_type=WhatsAppMessageType.FOLLOWUP.value,
        status=WhatsAppMessageStatus.PENDING.value,
        message_text=f"Follow-up: Invoice #{invoice.invoice_number or invoice.id} for ₹{invoice.amount} is still pending"
    )
    db.add(whatsapp_message)
    db.flush()  # Flush to get message ID
    
    # Trigger Celery task to send WhatsApp message
    send_whatsapp_message.delay(invoice.customer.phone, whatsapp_message.message_text)
    
    db.commit()
    db.refresh(whatsapp_message)
    
    return WhatsAppMessageResponse.model_validate(whatsapp_message)


@router.post("/{invoice_id}/pause-reminder", response_model=InvoiceResponse)
def pause_reminder(
    invoice_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Pause reminders for an invoice"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.merchant_id == current_merchant.id,
        Invoice.deleted_at.is_(None)  # Not soft deleted
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Check if invoice is paid
    if invoice.status == InvoiceStatus.PAID.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pause reminders for a paid invoice"
        )
    
    invoice.pause_reminder = True
    db.commit()
    db.refresh(invoice)
    
    return InvoiceResponse.model_validate(invoice)


@router.post("/{invoice_id}/unpause-reminder", response_model=InvoiceResponse)
def unpause_reminder(
    invoice_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Unpause reminders for an invoice"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.merchant_id == current_merchant.id,
        Invoice.deleted_at.is_(None)  # Not soft deleted
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Check if invoice is paid
    if invoice.status == InvoiceStatus.PAID.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unpause reminders for a paid invoice"
        )
    
    invoice.pause_reminder = False
    db.commit()
    db.refresh(invoice)
    
    return InvoiceResponse.model_validate(invoice)


@router.get("/public/{invoice_id}", response_model=InvoiceWithMerchantResponse)
def get_invoice_with_merchant_public(
    invoice_id: UUID,
    db: Session = Depends(get_db)
):
    """Get invoice and merchant details by invoice ID (Public endpoint - no authentication required)"""
    # Query invoice with merchant relationship loaded (public access)
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.deleted_at.is_(None)  # Not soft deleted
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Access merchant through relationship
    merchant = invoice.merchant
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found for this invoice"
        )
    
    return InvoiceWithMerchantResponse(
        invoice=InvoiceResponse.model_validate(invoice),
        merchant=MerchantResponse.model_validate(merchant)
    )

