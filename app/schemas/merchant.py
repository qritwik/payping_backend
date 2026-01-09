from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class MerchantCreate(BaseModel):
    business_name: str = Field(..., max_length=150)
    business_type: Optional[str] = Field(None, max_length=100)
    business_address: Optional[str] = None
    business_city: Optional[str] = Field(None, max_length=50)
    business_country: Optional[str] = Field(None, max_length=50)
    business_zipcode: Optional[str] = Field(None, max_length=20)
    owner_name: Optional[str] = Field(None, max_length=100)
    phone: str = Field(..., max_length=15)
    email: Optional[EmailStr] = None
    company_logo_s3_url: Optional[str] = None
    upi_id: Optional[str] = Field(None, max_length=100)
    upi_qr_s3_url: Optional[str] = None


class MerchantResponse(BaseModel):
    id: UUID
    business_name: str
    business_type: Optional[str]
    business_address: Optional[str]
    business_city: Optional[str]
    business_country: Optional[str]
    business_zipcode: Optional[str]
    owner_name: Optional[str]
    phone: str
    email: Optional[str]
    company_logo_s3_url: Optional[str]
    upi_id: Optional[str]
    upi_qr_s3_url: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

