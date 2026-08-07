from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
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
    vendor_id: int | None = Form(None),
    vendor_name: str = Form(...),
    mobile_number: str = Form(...),
    shop_name: str | None = Form(None),
    address: str | None = Form(None),
    status: str = Form("active"),
    photo_file: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    return VendorService.save_vendor(
        db=db,
        vendor_id=vendor_id,
        vendor_name=vendor_name,
        mobile_number=mobile_number,
        shop_name=shop_name,
        address=address,
        status=status,
        photo_file=photo_file
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