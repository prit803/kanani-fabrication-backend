from decimal import Decimal
from typing import Optional, List
from datetime import date

from pydantic import BaseModel, Field


class BillItemRequest(BaseModel):

    bill_item_id: Optional[int] = None

    # bill_id is optional now; when not provided the API can create a bill
    bill_id: Optional[int] = None

    item_description: str = Field(..., min_length=1, max_length=1000)

    quantity: Decimal = Field(default=1, gt=0)

    rate: Decimal = Field(default=0, ge=0)

    audio_file_url: Optional[str] = None


class CreateBillItemsRequest(BaseModel):
    """
    Request model for creating/updating multiple bill items in one call.
    If `bill_id` is not provided, a new bill will be created using
    `vendor_id`, `bill_date` and `status`.
    """

    # Either supply an existing bill_id or vendor_id to create a new bill
    bill_id: Optional[int] = None
    vendor_id: Optional[int] = None
    bill_date: Optional[date] = None
    status: Optional[str] = None

    items: List[BillItemRequest]


class BillItemResponse(BaseModel):

    bill_item_id: int

    bill_id: int

    item_description: str

    quantity: Decimal

    rate: Decimal

    amount: Decimal

    audio_file_url: Optional[str]

    class Config:
        from_attributes = True
