from datetime import date
from typing import Optional

from pydantic import BaseModel


class BillRequest(BaseModel):

    bill_id: Optional[int] = None

    vendor_id: int

    bill_date: date

    status: str = "pending"


class BillResponse(BillRequest):
    pass