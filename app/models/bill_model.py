from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    Date,
    Enum,
    ForeignKey,
    TIMESTAMP,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Bill(Base):
    __tablename__ = "bills"

    bill_id = Column(Integer, primary_key=True, index=True)

    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id"), nullable=False)

    engineer_id = Column(Integer, ForeignKey("engineering.engineer_id"), nullable=True)

    bill_date = Column(Date, nullable=False)

    status = Column(Enum("pending", "paid"), default="pending")

    is_deleted = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, server_default=func.now())

    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    vendor = relationship("Vendor", backref="bills")

    engineer = relationship("Engineering", back_populates="bills")
