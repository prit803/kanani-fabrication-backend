from pydantic import BaseModel
from typing import Optional


class VendorCreate(BaseModel):
    vendor_name: str
    mobile_number: str
    shop_name: Optional[str] = None
    address: Optional[str] = None
    photo_url: Optional[str] = None
    status: Optional[str] = "active"


class VendorResponse(VendorCreate):
    vendor_id: int

    class Config:
        from_attributes = True