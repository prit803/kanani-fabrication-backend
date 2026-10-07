from fastapi import APIRouter, File, UploadFile

from app.services.gujarati_stt_service import GujaratiSTTService

router = APIRouter(tags=["Gujarati STT"])


@router.post("/speech-to-text/upload")
def speech_to_text_upload(file: UploadFile = File(...)):
    return GujaratiSTTService.speech_to_text_upload(file=file)