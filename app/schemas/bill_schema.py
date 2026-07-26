from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class BillRequest(BaseModel):
    bill_id: Optional[int] = None
    vendor_id: int
    bill_text_gujarati: Optional[str] = None
    amount: Decimal
    bill_date: date
    status: str = "pending"
    audio_file_url: Optional[str] = None


class BillResponse(BillRequest):
    pass