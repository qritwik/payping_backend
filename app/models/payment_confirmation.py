from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, CheckConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class PaymentConfirmation(Base):
    __tablename__ = "payment_confirmations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    whatsapp_message_id = Column(UUID(as_uuid=True), ForeignKey("whatsapp_messages.id", ondelete="SET NULL"), nullable=True)

    customer_message = Column(Text)
    detected_intent = Column(String(100))
    llm_confidence = Column(Numeric(3, 2))

    status = Column(String(20), default='pending', nullable=False)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    resolved_at = Column(TIMESTAMP, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name='payment_confirmations_status_check'
        ),
    )

    # Relationships
    merchant = relationship("Merchant", backref="payment_confirmations")
    customer = relationship("Customer", backref="payment_confirmations")
    invoice = relationship("Invoice", backref="payment_confirmations")
    whatsapp_message = relationship("WhatsAppMessage", backref="payment_confirmations")
