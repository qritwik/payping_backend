from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.merchant import Merchant
from app.schemas.auth import (
    PhoneRequest,
    OTPRequest,
    OTPResponse,
    VerifyOTPResponse,
)
from app.services.otp_service import create_otp, verify_otp, RateLimitError

router = APIRouter()


@router.post("/send-otp", response_model=OTPResponse)
def send_otp(request: PhoneRequest, db: Session = Depends(get_db)):
    """Send OTP to a phone number"""
    try:
        otp = create_otp(db, request.phone)
        return OTPResponse(
            message="OTP sent successfully",
            phone=request.phone
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {str(e)}"
        )


@router.post("/verify-otp", response_model=VerifyOTPResponse)
def verify_otp_endpoint(request: OTPRequest, db: Session = Depends(get_db)):
    """Verify OTP code and return JWT token if merchant exists, otherwise just verify OTP for registration"""
    is_valid = verify_otp(db, request.phone, request.otp_code)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Check if merchant exists
    merchant = db.query(Merchant).filter(Merchant.phone == request.phone).first()
    
    if merchant:
        # Check if merchant is active
        if not merchant.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is inactive. Please contact support."
            )
        
        # Merchant exists and is active - login flow: return JWT token
        access_token = create_access_token(data={"sub": request.phone})
        return VerifyOTPResponse(
            message="OTP verified successfully",
            verified=True,
            access_token=access_token,
            token_type="bearer",
            requires_registration=False
        )
    else:
        # Merchant doesn't exist - registration flow: just verify OTP
        return VerifyOTPResponse(
            message="OTP verified successfully. Please complete registration.",
            verified=True,
            access_token=None,
            token_type=None,
            requires_registration=True
        )

