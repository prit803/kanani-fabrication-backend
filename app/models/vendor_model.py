from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Text,
    DateTime,
)

from sqlalchemy.sql import func

from app.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    vendor_name = Column(
        String(255),
        nullable=False
    )

    mobile_number = Column(
        String(20),
        nullable=False
    )

    shop_name = Column(
        String(255),
        nullable=True
    )

    address = Column(
        Text,
        nullable=True
    )

    photo_url = Column(
        Text,
        nullable=True
    )

    status = Column(
        String(20),
        default="active"
    )

    is_deleted = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )