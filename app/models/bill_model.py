from sqlalchemy import Column, Integer, Text, Date, Enum
from sqlalchemy import ForeignKey, DECIMAL, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Bill(Base):
    __tablename__ = "bills"

    bill_id = Column(Integer, primary_key=True, index=True)

    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id"))

    bill_text_gujarati = Column(Text)

    amount = Column(DECIMAL(10, 2), nullable=False)

    bill_date = Column(Date)

    status = Column(Enum('pending', 'paid'), default='pending')

    audio_file_url = Column(Text)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    vendor = relationship("Vendor")