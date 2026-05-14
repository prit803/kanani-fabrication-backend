from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.vendor_model import Vendor
from app.schemas.vendor_schema import VendorCreate

router = APIRouter(prefix="/vendors", tags=["Vendors"])
@router.get("/list")
def get_vendors(db: Session = Depends(get_db)):
    vendors = db.query(Vendor).all()
    return vendors


@router.get("/{vendor_id}")
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):

    vendor = db.query(Vendor).filter(
        Vendor.vendor_id == vendor_id
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return vendor


@router.put("/update/{vendor_id}")
def update_vendor(
    vendor_id: int,
    vendor_data: VendorCreate,
    db: Session = Depends(get_db)
):

    vendor = db.query(Vendor).filter(
        Vendor.vendor_id == vendor_id
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    vendor.vendor_name = vendor_data.vendor_name
    vendor.mobile_number = vendor_data.mobile_number
    vendor.shop_name = vendor_data.shop_name
    vendor.address = vendor_data.address
    vendor.photo_url = vendor_data.photo_url
    vendor.status = vendor_data.status

    db.commit()

    return {
        "message": "Vendor updated successfully"
    }


@router.delete("/delete/{vendor_id}")
def delete_vendor(vendor_id: int, db: Session = Depends(get_db)):

    vendor = db.query(Vendor).filter(
        Vendor.vendor_id == vendor_id
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    db.delete(vendor)
    db.commit()

    return {
        "message": "Vendor deleted successfully"
    }