from pydantic import BaseModel
from typing import Optional
from datetime import date


class BillCreate(BaseModel):
    vendor_id: int
    bill_text_gujarati: Optional[str] = None
    amount: float
    bill_date: date
    status: Optional[str] = "pending"
    audio_file_url: Optional[str] = None


class BillResponse(BillCreate):
    bill_id: int

    class Config:
        from_attributes = True