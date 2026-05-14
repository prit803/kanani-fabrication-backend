from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.bill_model import Bill
from app.schemas.bill_schema import BillCreate

router = APIRouter(prefix="/bills", tags=["Bills"])



@router.get("/list")
def get_bills(db: Session = Depends(get_db)):
    bills = db.query(Bill).all()
    return bills


@router.get("/{bill_id}")
def get_bill(bill_id: int, db: Session = Depends(get_db)):

    bill = db.query(Bill).filter(
        Bill.bill_id == bill_id
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    return bill


@router.put("/update/{bill_id}")
def update_bill(
    bill_id: int,
    bill_data: BillCreate,
    db: Session = Depends(get_db)
):

    bill = db.query(Bill).filter(
        Bill.bill_id == bill_id
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    bill.vendor_id = bill_data.vendor_id
    bill.bill_text_gujarati = bill_data.bill_text_gujarati
    bill.amount = bill_data.amount
    bill.bill_date = bill_data.bill_date
    bill.status = bill_data.status
    bill.audio_file_url = bill_data.audio_file_url

    db.commit()

    return {
        "message": "Bill updated successfully"
    }


@router.delete("/delete/{bill_id}")
def delete_bill(bill_id: int, db: Session = Depends(get_db)):

    bill = db.query(Bill).filter(
        Bill.bill_id == bill_id
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    db.delete(bill)
    db.commit()

    return {
        "message": "Bill deleted successfully"
    }


@router.get("/status/paid")
def paid_bills(db: Session = Depends(get_db)):
    return db.query(Bill).filter(Bill.status == 'paid').all()


@router.get("/status/pending")
def pending_bills(db: Session = Depends(get_db)):
    return db.query(Bill).filter(Bill.status == 'pending').all()