from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date
from app.core.database import get_db
from app.core.security import get_current_merchant, create_access_token
from app.models.merchant import Merchant
from app.models.invoice import Invoice
from app.models.payment_confirmation import PaymentConfirmation
from app.schemas.merchant import MerchantCreate, MerchantResponse, MerchantUpdate, DashboardResponse
from app.schemas.auth import TokenResponse
from app.services.otp_service import is_otp_verified
from app.utils.enums import InvoiceStatus

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_merchant(merchant: MerchantCreate, db: Session = Depends(get_db)):
    """Register a new merchant - requires OTP verification first"""
    # Check if merchant with this phone already exists
    existing_merchant = db.query(Merchant).filter(Merchant.phone == merchant.phone).first()
    if existing_merchant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Merchant with this phone number already exists"
        )
    
    # Verify that OTP was verified for this phone number
    if not is_otp_verified(db, merchant.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP verification required. Please verify your phone number first."
        )
    
    # Create merchant account
    db_merchant = Merchant(**merchant.model_dump())
    db.add(db_merchant)
    db.commit()
    db.refresh(db_merchant)
    
    # Generate JWT token for the newly registered merchant
    access_token = create_access_token(data={"sub": merchant.phone})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        merchant=MerchantResponse.model_validate(db_merchant)
    )


@router.get("/me", response_model=MerchantResponse)
def get_my_profile(current_merchant: Merchant = Depends(get_current_merchant)):
    """Get current authenticated merchant profile (protected endpoint)"""
    return MerchantResponse.model_validate(current_merchant)


@router.put("/me", response_model=MerchantResponse)
def update_my_profile(
    merchant_update: MerchantUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Update current authenticated merchant profile (protected endpoint)"""
    # Get only the fields that were provided (not None)
    update_data = merchant_update.model_dump(exclude_unset=True)
    
    # Update the merchant with provided fields
    for field, value in update_data.items():
        setattr(current_merchant, field, value)
    
    db.commit()
    db.refresh(current_merchant)
    
    return MerchantResponse.model_validate(current_merchant)


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for the authenticated merchant"""
    # Get current month start and end dates
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
    
    # Base query filter for merchant's invoices (not soft deleted)
    base_filter = and_(
        Invoice.merchant_id == current_merchant.id,
        Invoice.deleted_at.is_(None)
    )
    
    # Total Outstanding: Sum of unpaid invoice amounts
    total_outstanding_result = db.query(func.coalesce(func.sum(Invoice.amount), 0)).filter(
        base_filter,
        Invoice.status == InvoiceStatus.UNPAID.value
    ).scalar()
    total_outstanding = float(total_outstanding_result) if total_outstanding_result else 0.0
    
    # Paid This Month: Sum of paid invoices in the current month
    paid_this_month_result = db.query(func.coalesce(func.sum(Invoice.amount), 0)).filter(
        base_filter,
        Invoice.status == InvoiceStatus.PAID.value,
        Invoice.paid_at >= datetime.combine(month_start, datetime.min.time()),
        Invoice.paid_at < datetime.combine(month_end, datetime.min.time())
    ).scalar()
    paid_this_month = float(paid_this_month_result) if paid_this_month_result else 0.0
    
    # Unpaid Invoices: Count of unpaid invoices
    unpaid_invoices = db.query(func.count(Invoice.id)).filter(
        base_filter,
        Invoice.status == InvoiceStatus.UNPAID.value
    ).scalar() or 0
    
    # Payment Confirmations Pending: Count of pending payment confirmations
    payment_confirmations_pending = db.query(func.count(PaymentConfirmation.id)).filter(
        PaymentConfirmation.merchant_id == current_merchant.id,
        PaymentConfirmation.status == 'pending'
    ).scalar() or 0
    
    return DashboardResponse(
        total_outstanding=total_outstanding,
        paid_this_month=paid_this_month,
        unpaid_invoices=unpaid_invoices,
        payment_confirmations_pending=payment_confirmations_pending
    )
