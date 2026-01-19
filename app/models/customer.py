from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False)
    email = Column(String(150))
    address = Column(Text)
    employment_type = Column(String(20))
    class_ = Column(String(100), name="class")
    section = Column(String(100))
    batch = Column(String(100))
    
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "employment_type IN ('SALARIED', 'SELF_EMPLOYED', 'BUSINESS', 'UNEMPLOYED') OR employment_type IS NULL",
            name='customers_employment_type_check'
        ),
    )

    # Relationship to merchant
    merchant = relationship("Merchant", backref="customers")

