from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, CheckConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    
    direction = Column(String(20), nullable=False)
    message_type = Column(String(20))
    status = Column(String(20), default='PENDING', nullable=False)
    
    message_text = Column(Text)
    provider_message_id = Column(String(255), unique=True)
    
    detected_intent = Column(String(100))
    llm_confidence = Column(Numeric(3, 2))
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "direction IN ('INBOUND', 'OUTBOUND')",
            name='whatsapp_messages_direction_check'
        ),
        CheckConstraint(
            "message_type IN ('invoice', 'followup', 'customer_message') OR message_type IS NULL",
            name='whatsapp_messages_type_check'
        ),
        CheckConstraint(
            "status IN ('PENDING', 'SENT', 'DELIVERED', 'READ', 'FAILED', 'RECEIVED')",
            name='whatsapp_messages_status_check'
        ),
    )

    # Relationships
    merchant = relationship("Merchant", backref="whatsapp_messages")
    customer = relationship("Customer", backref="whatsapp_messages")

