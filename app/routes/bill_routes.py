from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
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


# @router.post("")
# def save_bill(
#     request: BillRequest,
#     db: Session = Depends(get_db)
# ):
#     return BillService.save_bill(
#         db=db,
#         request=request
#     )


@router.delete("/{bill_id}")
def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db)
):
    return BillService.delete_bill(
        db=db,
        bill_id=bill_id
    )


@router.get("/vendor-total")
def get_vendor_bill_total(
    vendor_id: int,
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db)
):
    return BillService.get_vendor_bill_total(
        db=db,
        vendor_id=vendor_id,
        from_date=from_date,
        to_date=to_date
    )

@router.get("/pdf-data")
def get_bill_pdf_data(
    vendor_id: int,
    from_date: date,
    to_date: date,
    engineer_id: int | None = None,
    db: Session = Depends(get_db)
):
    return BillService.get_bill_pdf_data(
        db=db,
        vendor_id=vendor_id,
        from_date=from_date,
        to_date=to_date,
        engineer_id=engineer_id
    )