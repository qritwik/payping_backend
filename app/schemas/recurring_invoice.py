from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class RecurringInvoiceCreate(BaseModel):
    customer_id: UUID
    invoice_number_prefix: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    amount: Decimal = Field(..., gt=0)
    day_of_month: int = Field(..., ge=1, le=31)
    due_date_offset: int = Field(7, ge=0)
    start_date: date
    end_date: Optional[date] = None
    pause_reminder: bool = False

    @model_validator(mode="after")
    def validate_dates(self) -> "RecurringInvoiceCreate":
        today = date.today()

        if self.start_date < today:
            raise ValueError("start_date cannot be in the past")

        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")

        return self


class RecurringInvoiceUpdate(BaseModel):
    invoice_number_prefix: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    due_date_offset: Optional[int] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    pause_reminder: Optional[bool] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "RecurringInvoiceUpdate":
        today = date.today()

        if self.start_date is not None and self.start_date < today:
            raise ValueError("start_date cannot be in the past")

        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date cannot be before start_date")

        return self


class RecurringInvoiceResponse(BaseModel):
    id: UUID
    merchant_id: UUID
    customer_id: UUID
    invoice_number_prefix: Optional[str]
    description: Optional[str]
    amount: Decimal
    day_of_month: int
    due_date_offset: int
    start_date: date
    end_date: Optional[date]
    next_generation_date: date
    is_active: bool
    frequency: str
    pause_reminder: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


