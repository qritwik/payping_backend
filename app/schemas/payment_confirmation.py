from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class PaymentConfirmationResponse(BaseModel):
    id: UUID
    invoice_id: Optional[UUID]
    merchant_id: UUID
    customer_id: Optional[UUID]
    whatsapp_message_id: Optional[UUID]
    customer_message: Optional[str]
    detected_intent: Optional[str]
    llm_confidence: Optional[Decimal]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]
    
    # Related data for display
    invoice_date: Optional[datetime] = None
    customer_name: Optional[str] = None
    amount: Optional[Decimal] = None

    class Config:
        from_attributes = True


class PaymentConfirmationListResponse(BaseModel):
    id: UUID
    invoice_id: Optional[UUID]
    customer_id: Optional[UUID]
    customer_message: Optional[str]
    status: str
    created_at: datetime
    
    # Display fields from related models
    invoice_date: Optional[datetime] = None
    customer_name: Optional[str] = None
    amount: Optional[Decimal] = None

    class Config:
        from_attributes = True
