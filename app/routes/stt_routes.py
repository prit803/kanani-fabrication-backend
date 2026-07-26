from fastapi import APIRouter, File, UploadFile

from app.services.stt_service import STTService


router = APIRouter(
    prefix="/stt",
    tags=["STT"]
)


@router.post("/speech-to-text")
async def speech_to_text(
    file: UploadFile = File(...)
):
    return await STTService.speech_to_text(file=file)