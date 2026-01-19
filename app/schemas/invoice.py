from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from app.utils.enums import InvoiceStatus


class InvoiceCreate(BaseModel):
    customer_id: UUID
    invoice_number: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    amount: Decimal = Field(..., gt=0)
    due_date: Optional[date] = None
    pause_reminder: bool = False


class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    due_date: Optional[date] = None


class InvoiceResponse(BaseModel):
    id: UUID
    merchant_id: UUID
    customer_id: UUID
    customer_name: Optional[str] = None
    class_: Optional[str] = Field(None, alias="class")
    section: Optional[str] = None
    batch: Optional[str] = None
    recurring_invoice_id: Optional[UUID] = None
    invoice_number: Optional[str]
    description: Optional[str]
    amount: Decimal
    due_date: Optional[date]
    status: str
    paid_at: Optional[datetime]
    pause_reminder: bool
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class WhatsAppMessageResponse(BaseModel):
    id: UUID
    merchant_id: UUID
    customer_id: Optional[UUID]
    invoice_id: Optional[UUID]
    direction: str
    message_type: Optional[str]
    status: str
    message_text: Optional[str]
    provider_message_id: Optional[str]
    detected_intent: Optional[str]
    llm_confidence: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceWithMessagesResponse(InvoiceResponse):
    whatsapp_messages: Optional[List[WhatsAppMessageResponse]] = None


class InvoiceWithMerchantResponse(BaseModel):
    invoice: InvoiceResponse
    merchant: "MerchantResponse"

    class Config:
        from_attributes = True


# Resolve forward reference
from app.schemas.merchant import MerchantResponse
InvoiceWithMerchantResponse.model_rebuild()

