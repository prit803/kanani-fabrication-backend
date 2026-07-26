from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.bill_schema import BillRequest
from app.services.bill_service import BillService

router = APIRouter(
    prefix="/bills",
    tags=["Bill"]
)


@router.get("")
def get_bill(
    bill_id: int | None = None,
    db: Session = Depends(get_db)
):
    return BillService.get_bill(
        db=db,
        bill_id=bill_id
    )


@router.post("")
def save_bill(
    request: BillRequest,
    db: Session = Depends(get_db)
):
    return BillService.save_bill(
        db=db,
        request=request
    )


@router.delete("/{bill_id}")
def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db)
):
    return BillService.delete_bill(
        db=db,
        bill_id=bill_id
    )