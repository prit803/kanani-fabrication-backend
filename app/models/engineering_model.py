from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Engineering(Base):
    __tablename__ = "engineering"

    engineer_id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)

    sign_image = Column(String(500), nullable=True)

    pan_number = Column(String(50), nullable=True)

    bank_account_number = Column(String(50), nullable=True)

    is_deleted = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, server_default=func.now())

    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    bills = relationship("Bill", back_populates="engineer")
