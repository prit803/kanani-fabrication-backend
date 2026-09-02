from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.engineering_service import EngineeringService

router = APIRouter(prefix="/engineering", tags=["Engineering"])


@router.get("")
def get_engineering(engineer_id: int | None = None, db: Session = Depends(get_db)):
    return EngineeringService.get_engineering(db=db, engineer_id=engineer_id)


@router.post("")
def save_engineering(
    engineer_id: int | None = Form(None),
    name: str = Form(...),
    pan_number: str | None = Form(None),
    bank_account_number: str | None = Form(None),
    sign_image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    return EngineeringService.save_engineering(
        db=db,
        engineer_id=engineer_id,
        name=name,
        pan_number=pan_number,
        bank_account_number=bank_account_number,
        sign_image=sign_image,
    )
