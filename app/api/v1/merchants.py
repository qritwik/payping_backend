from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_merchant, create_access_token
from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate, MerchantResponse
from app.schemas.auth import TokenResponse
from app.services.otp_service import is_otp_verified

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
