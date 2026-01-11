from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.utils.enums import EmploymentType


class CustomerCreate(BaseModel):
    name: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=15)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    employment_type: Optional[EmploymentType] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    employment_type: Optional[EmploymentType] = None


class CustomerResponse(BaseModel):
    id: UUID
    merchant_id: UUID
    name: str
    phone: str
    email: Optional[str]
    address: Optional[str]
    employment_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

