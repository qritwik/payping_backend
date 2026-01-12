from sqlalchemy import (
    Column,
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    Boolean,
    Numeric,
    Date,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class RecurringInvoice(Base):
    __tablename__ = "recurring_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )

    invoice_number_prefix = Column(String(50))
    description = Column(Text)

    amount = Column(Numeric(10, 2), nullable=False)
    day_of_month = Column(Integer, nullable=False)  # 1-31 (DB CHECK enforces range)
    due_date_offset = Column(Integer, nullable=False, default=7)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    next_generation_date = Column(Date, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    frequency = Column(String(20), default="MONTHLY", nullable=False)

    # Whether to pause WhatsApp reminders for invoices generated from this template
    pause_reminder = Column(Boolean, default=False, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    merchant = relationship("Merchant", backref="recurring_invoices")
    customer = relationship("Customer", backref="recurring_invoices")
    invoices = relationship(
        "Invoice",
        back_populates="recurring_invoice",
        cascade="all, delete-orphan",
    )


