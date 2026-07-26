from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VendorRequest(BaseModel):

    vendor_id: Optional[int] = None

    vendor_name: str = Field(
        ...,
        min_length=2,
        max_length=255
    )

    mobile_number: str = Field(
        ...,
        min_length=10,
        max_length=20
    )

    shop_name: Optional[str] = None

    address: Optional[str] = None

    photo_url: Optional[str] = None

    status: Optional[str] = "active"


class VendorResponse(BaseModel):

    vendor_id: int

    vendor_name: str

    mobile_number: str

    shop_name: Optional[str]

    address: Optional[str]

    photo_url: Optional[str]

    status: str

    is_deleted: bool

    created_at: str

    updated_at: str

    model_config = ConfigDict(
        from_attributes=True
    )