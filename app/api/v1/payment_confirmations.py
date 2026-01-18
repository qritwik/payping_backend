from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_merchant
from app.models.merchant import Merchant
from app.models.payment_confirmation import PaymentConfirmation
from app.models.invoice import Invoice
from app.models.customer import Customer
from app.schemas.payment_confirmation import (
    PaymentConfirmationResponse,
    PaymentConfirmationListResponse,
)
from app.utils.enums import InvoiceStatus

router = APIRouter()


@router.get("", response_model=List[PaymentConfirmationListResponse])
def get_payment_confirmations(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Get all payment confirmations for the merchant with filters and pagination"""
    query = db.query(PaymentConfirmation).filter(
        PaymentConfirmation.merchant_id == current_merchant.id
    )
    
    # Apply status filter
    if status_filter:
        valid_statuses = ['pending', 'approved', 'rejected']
        if status_filter.lower() not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        query = query.filter(PaymentConfirmation.status == status_filter.lower())
    
    # Apply pagination and eager load relationships
    confirmations = query.options(
        joinedload(PaymentConfirmation.invoice),
        joinedload(PaymentConfirmation.customer)
    ).order_by(PaymentConfirmation.created_at.desc()).offset(skip).limit(limit).all()
    
    # Build response with related data
    result = []
    for confirmation in confirmations:
        confirmation_dict = {
            "id": confirmation.id,
            "invoice_id": confirmation.invoice_id,
            "customer_id": confirmation.customer_id,
            "customer_message": confirmation.customer_message,
            "status": confirmation.status,
            "created_at": confirmation.created_at,
            "invoice_date": None,
            "customer_name": None,
            "amount": None,
        }
        
        # Get invoice date and amount if invoice exists
        if confirmation.invoice:
            confirmation_dict["invoice_date"] = confirmation.invoice.created_at
            confirmation_dict["amount"] = confirmation.invoice.amount
        
        # Get customer name if customer exists
        if confirmation.customer:
            confirmation_dict["customer_name"] = confirmation.customer.name
        
        result.append(PaymentConfirmationListResponse(**confirmation_dict))
    
    return result


@router.get("/{confirmation_id}", response_model=PaymentConfirmationResponse)
def get_payment_confirmation_by_id(
    confirmation_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Get a specific payment confirmation by ID"""
    confirmation = db.query(PaymentConfirmation).options(
        joinedload(PaymentConfirmation.invoice),
        joinedload(PaymentConfirmation.customer)
    ).filter(
        PaymentConfirmation.id == confirmation_id,
        PaymentConfirmation.merchant_id == current_merchant.id
    ).first()
    
    if not confirmation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment confirmation not found"
        )
    
    # Build response with related data
    confirmation_dict = PaymentConfirmationResponse.model_validate(confirmation).model_dump()
    
    # Add invoice date and amount if invoice exists
    if confirmation.invoice:
        confirmation_dict["invoice_date"] = confirmation.invoice.created_at
        confirmation_dict["amount"] = confirmation.invoice.amount
    
    # Add customer name if customer exists
    if confirmation.customer:
        confirmation_dict["customer_name"] = confirmation.customer.name
    
    return PaymentConfirmationResponse(**confirmation_dict)


@router.post("/{confirmation_id}/approve", response_model=PaymentConfirmationResponse)
def approve_payment_confirmation(
    confirmation_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Approve a payment confirmation and mark associated invoice as paid"""
    confirmation = db.query(PaymentConfirmation).filter(
        PaymentConfirmation.id == confirmation_id,
        PaymentConfirmation.merchant_id == current_merchant.id
    ).first()
    
    if not confirmation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment confirmation not found"
        )
    
    # Check if already resolved
    if confirmation.status != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment confirmation is already {confirmation.status}"
        )
    
    # Update confirmation status
    confirmation.status = 'approved'
    confirmation.resolved_at = datetime.utcnow()
    
    # If there's an associated invoice, mark it as paid
    if confirmation.invoice_id:
        invoice = db.query(Invoice).filter(
            Invoice.id == confirmation.invoice_id,
            Invoice.merchant_id == current_merchant.id,
            Invoice.deleted_at.is_(None)
        ).first()
        
        if invoice and invoice.status == InvoiceStatus.UNPAID.value:
            invoice.status = InvoiceStatus.PAID.value
            invoice.paid_at = datetime.utcnow()
    
    db.commit()
    db.refresh(confirmation)
    
    # Reload with relationships for response
    confirmation = db.query(PaymentConfirmation).options(
        joinedload(PaymentConfirmation.invoice),
        joinedload(PaymentConfirmation.customer)
    ).filter(PaymentConfirmation.id == confirmation_id).first()
    
    # Build response with related data
    confirmation_dict = PaymentConfirmationResponse.model_validate(confirmation).model_dump()
    
    if confirmation.invoice:
        confirmation_dict["invoice_date"] = confirmation.invoice.created_at
        confirmation_dict["amount"] = confirmation.invoice.amount
    
    if confirmation.customer:
        confirmation_dict["customer_name"] = confirmation.customer.name
    
    return PaymentConfirmationResponse(**confirmation_dict)


@router.post("/{confirmation_id}/decline", response_model=PaymentConfirmationResponse)
def decline_payment_confirmation(
    confirmation_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Decline a payment confirmation"""
    confirmation = db.query(PaymentConfirmation).filter(
        PaymentConfirmation.id == confirmation_id,
        PaymentConfirmation.merchant_id == current_merchant.id
    ).first()
    
    if not confirmation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment confirmation not found"
        )
    
    # Check if already resolved
    if confirmation.status != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment confirmation is already {confirmation.status}"
        )
    
    # Update confirmation status
    confirmation.status = 'rejected'
    confirmation.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(confirmation)
    
    # Reload with relationships for response
    confirmation = db.query(PaymentConfirmation).options(
        joinedload(PaymentConfirmation.invoice),
        joinedload(PaymentConfirmation.customer)
    ).filter(PaymentConfirmation.id == confirmation_id).first()
    
    # Build response with related data
    confirmation_dict = PaymentConfirmationResponse.model_validate(confirmation).model_dump()
    
    if confirmation.invoice:
        confirmation_dict["invoice_date"] = confirmation.invoice.created_at
        confirmation_dict["amount"] = confirmation.invoice.amount
    
    if confirmation.customer:
        confirmation_dict["customer_name"] = confirmation.customer.name
    
    return PaymentConfirmationResponse(**confirmation_dict)
