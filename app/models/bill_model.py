from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    Text,
    Date,
    Enum,
    ForeignKey,
    DECIMAL,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Bill(Base):
    __tablename__ = "bills"

    bill_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    vendor_id = Column(
        Integer,
        ForeignKey("vendors.vendor_id"),
        nullable=False
    )

    bill_text_gujarati = Column(
        Text,
        nullable=True
    )

    amount = Column(
        DECIMAL(10, 2),
        nullable=False
    )

    bill_date = Column(
        Date,
        nullable=False
    )

    status = Column(
        Enum("pending", "paid"),
        default="pending"
    )

    audio_file_url = Column(
        Text,
        nullable=True
    )

    is_deleted = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    vendor = relationship(
        "Vendor",
        backref="bills"
    )