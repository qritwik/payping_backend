import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.auth import OTP
from app.core.config import settings


def generate_otp(length: int = None) -> str:
    """Generate a random OTP code"""
    if length is None:
        length = settings.OTP_LENGTH
    return ''.join(random.choices(string.digits, k=length))


def create_otp(db: Session, phone: str, expiry_minutes: int = None) -> OTP:
    """Create and store an OTP for a phone number"""
    if expiry_minutes is None:
        expiry_minutes = settings.OTP_EXPIRY_MINUTES
    
    # Invalidate any existing unverified OTPs for this phone
    db.query(OTP).filter(
        OTP.phone == phone,
        OTP.is_verified == 'false'
    ).update({"is_verified": "expired"})
    
    # Generate new OTP
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    
    otp = OTP(
        phone=phone,
        otp_code=otp_code,
        expires_at=expires_at,
        is_verified='false'
    )
    
    db.add(otp)
    db.commit()
    db.refresh(otp)
    
    # In a real application, you would send this OTP via SMS service
    # For now, we'll just return it (in production, remove this print)
    print(f"OTP for {phone}: {otp_code}")  # Remove in production
    
    return otp


def verify_otp(db: Session, phone: str, otp_code: str) -> bool:
    """Verify an OTP code for a phone number"""
    otp = db.query(OTP).filter(
        OTP.phone == phone,
        OTP.otp_code == otp_code,
        OTP.is_verified == 'false',
        OTP.expires_at > datetime.utcnow()
    ).first()
    
    if otp:
        otp.is_verified = 'true'
        db.commit()
        return True
    
    return False


def is_otp_verified(db: Session, phone: str) -> bool:
    """Check if phone number has a verified OTP"""
    otp = db.query(OTP).filter(
        OTP.phone == phone,
        OTP.is_verified == 'true',
        OTP.expires_at > datetime.utcnow()
    ).order_by(OTP.created_at.desc()).first()
    
    return otp is not None

