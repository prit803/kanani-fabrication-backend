from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.bill_item_schema import BillItemRequest, CreateBillItemsRequest
from app.services.bill_item_service import BillItemService

router = APIRouter(prefix="/bill-items", tags=["Bill Item"])


@router.get("")
def get_bill_item(
    bill_item_id: int | None = None,
    bill_id: int | None = None,
    db: Session = Depends(get_db),
):
    return BillItemService.get_bill_item(
        db=db, bill_item_id=bill_item_id, bill_id=bill_id
    )


@router.post("")
def save_bill_item(request: CreateBillItemsRequest, db: Session = Depends(get_db)):
    return BillItemService.save_bill_item(db=db, request=request)


@router.delete("/{bill_item_id}")
def delete_bill_item(bill_item_id: int, db: Session = Depends(get_db)):
    return BillItemService.delete_bill_item(db=db, bill_item_id=bill_item_id)
