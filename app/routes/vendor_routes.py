from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.vendor_schema import VendorRequest
from app.services.vendor_service import VendorService

router = APIRouter(
    prefix="/vendors",
    tags=["Vendor"]
)


@router.get("")
def get_vendor(
    vendor_id: int | None = None,
    db: Session = Depends(get_db)
):
    return VendorService.get_vendor(
        db=db,
        vendor_id=vendor_id
    )


@router.post("")
def save_vendor(
    request: VendorRequest,
    db: Session = Depends(get_db)
):
    return VendorService.save_vendor(
        db=db,
        request=request
    )


@router.delete("/{vendor_id}")
def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db)
):
    return VendorService.delete_vendor(
        db=db,
        vendor_id=vendor_id
    )