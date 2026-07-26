from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    Text,
    ForeignKey,
    DECIMAL,
    TIMESTAMP,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class BillItem(Base):
    __tablename__ = "bill_items"

    bill_item_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    bill_id = Column(
        Integer,
        ForeignKey("bills.bill_id"),
        nullable=False
    )

    item_description = Column(
        Text,
        nullable=False
    )

    quantity = Column(
        DECIMAL(10, 2),
        nullable=False,
        default=1
    )

    rate = Column(
        DECIMAL(10, 2),
        nullable=False,
        default=0
    )

    amount = Column(
        DECIMAL(10, 2),
        nullable=False
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

    bill = relationship(
        "Bill",
        backref="bill_items"
    )