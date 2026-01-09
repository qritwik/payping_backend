from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.merchant import MerchantResponse


class PhoneRequest(BaseModel):
    phone: str = Field(..., max_length=15)


class OTPRequest(BaseModel):
    phone: str = Field(..., max_length=15)
    otp_code: str = Field(..., max_length=6, min_length=6)


class OTPResponse(BaseModel):
    message: str
    phone: str


class VerifyOTPResponse(BaseModel):
    message: str
    verified: bool
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    requires_registration: bool = False


class LoginResponse(BaseModel):
    message: str
    phone: str
    merchant: Optional[MerchantResponse] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    merchant: MerchantResponse

