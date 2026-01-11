from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, CheckConstraint, Boolean, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    
    invoice_number = Column(String(50))
    description = Column(Text)
    
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date)
    
    status = Column(String(20), default='UNPAID', nullable=False)
    paid_at = Column(TIMESTAMP)
    pause_reminder = Column(Boolean, default=False, nullable=False)
    
    deleted_at = Column(TIMESTAMP, nullable=True)  # Soft delete
    
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('UNPAID', 'PAID')",
            name='invoices_status_check'
        ),
    )

    # Relationships
    merchant = relationship("Merchant", backref="invoices")
    customer = relationship("Customer", backref="invoices")
    whatsapp_messages = relationship("WhatsAppMessage", backref="invoice", cascade="all, delete-orphan")

