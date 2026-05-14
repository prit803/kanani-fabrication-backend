from sqlalchemy import Column, Integer, String, Text, Enum, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String(255), nullable=False)
    mobile_number = Column(String(20))
    shop_name = Column(String(255))
    address = Column(Text)
    photo_url = Column(Text)
    status = Column(Enum('active', 'inactive'), default='active')

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )