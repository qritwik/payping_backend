from sqlalchemy import Column, String, Text, TIMESTAMP, CheckConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_name = Column(String(150), nullable=False)
    business_type = Column(String(100))
    business_address = Column(Text)
    business_city = Column(String(50))
    business_country = Column(String(50))
    business_zipcode = Column(String(20))
    owner_name = Column(String(100))
    phone = Column(String(15), unique=True, nullable=False)
    email = Column(String(150))
    company_logo_s3_url = Column(Text)
    upi_id = Column(String(100))
    upi_qr_s3_url = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    plan = Column(String(20), default='trial', nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "plan IN ('trial', 'starter', 'pro')",
            name='merchants_plan_check'
        ),
    )

