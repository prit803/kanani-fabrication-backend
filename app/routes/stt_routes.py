from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.stt_service import STTService

router = APIRouter(prefix="/stt", tags=["STT"])


@router.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await STTService.speech_to_text(file=file, db=db)


@router.get("/recordings/{recording_id}")
def get_recording(recording_id: int, db: Session = Depends(get_db)):
    return STTService.get_recording(db=db, recording_id=recording_id)


@router.get("/recordings/{recording_id}/audio")
def get_recording_audio(recording_id: int, db: Session = Depends(get_db)):
    return STTService.get_recording_audio(db=db, recording_id=recording_id)
