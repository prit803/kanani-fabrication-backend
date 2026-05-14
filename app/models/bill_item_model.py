from sqlalchemy import Column, Integer, String
from sqlalchemy import ForeignKey, DECIMAL

from app.database import Base


class BillItem(Base):
    __tablename__ = "bill_items"

    item_id = Column(Integer, primary_key=True, index=True)

    bill_id = Column(Integer, ForeignKey("bills.bill_id"))

    item_name = Column(String(255))

    quantity = Column(Integer, default=1)

    price = Column(DECIMAL(10, 2))

    total = Column(DECIMAL(10, 2))