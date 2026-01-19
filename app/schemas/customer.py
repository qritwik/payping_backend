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
    class_: Optional[str] = Field(None, max_length=100, alias="class")
    section: Optional[str] = Field(None, max_length=100)
    batch: Optional[str] = Field(None, max_length=100)
    
    class Config:
        populate_by_name = True


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    class_: Optional[str] = Field(None, max_length=100, alias="class")
    section: Optional[str] = Field(None, max_length=100)
    batch: Optional[str] = Field(None, max_length=100)
    
    class Config:
        populate_by_name = True


class CustomerResponse(BaseModel):
    id: UUID
    merchant_id: UUID
    name: str
    phone: str
    email: Optional[str]
    address: Optional[str]
    employment_type: Optional[str]
    class_: Optional[str] = Field(None, alias="class")
    section: Optional[str] = None
    batch: Optional[str] = None
    created_at: datetime
    total_pending_amount: float = 0.0

    class Config:
        from_attributes = True
        populate_by_name = True

