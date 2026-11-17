from io import BytesIO
import mimetypes
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.recording_model import SpeechRecording
from app.utils.logger import get_logger
from app.utils.response import ApiResponse
from app.services.stt_client import client as stt_client

logger = get_logger(__name__)


class STTService:

    @staticmethod
    async def speech_to_text(file: UploadFile, db: Session):

        try:

            logger.info("Starting speech to text transcription.")

            if not file.filename:

                logger.warning("Audio file name is missing.")

                return ApiResponse.error(
                    error_message="Audio file name is required.",
                    status_code=400,
                )

            allowed_extensions = {".wav", ".mp3", ".m4a", ".aac"}

            safe_file_name = Path(file.filename).name
            file_extension = Path(safe_file_name).suffix.lower()

            if file_extension not in allowed_extensions:

                logger.warning(f"Unsupported audio file type : {file_extension}")

                return ApiResponse.error(
                    error_message="Only audio files are allowed.",
                    status_code=400,
                )

            if stt_client is None:

                logger.error("STT client is not configured.")

                return ApiResponse.error(
                    error_message="STT client is not configured.",
                    status_code=500,
                )

            file_content = await file.read()
            if not file_content:
                return ApiResponse.error(
                    error_message="Audio file is empty.", status_code=400
                )

            content_type = file.content_type or mimetypes.guess_type(safe_file_name)[0]
            response = stt_client.speech_to_text.transcribe(
                file=(
                    safe_file_name,
                    BytesIO(file_content),
                    content_type or "application/octet-stream",
                ),
                model="saaras:v3",
                mode="transcribe",
            )

            transcript = getattr(response, "transcript", None)

            if transcript is None and isinstance(response, dict):
                transcript = response.get("transcript")

            formatted_text = fabrication_formatter(transcript or "")

            recording = SpeechRecording(
                filename=safe_file_name,
                content_type=content_type or "application/octet-stream",
                audio_data=file_content,
                transcript=formatted_text,
            )
            db.add(recording)
            db.commit()
            db.refresh(recording)

            data = {
                "recordingId": recording.recording_id,
                "audioUrl": f"/stt/recordings/{recording.recording_id}/audio",
                "transcription": formatted_text,
            }

            logger.info("Speech to text transcription completed successfully.")

            return ApiResponse.success(
                data=data, message="Speech to text completed successfully."
            )

        except Exception:
            db.rollback()

            logger.exception("Exception occurred while processing speech to text.")

            return ApiResponse.error(
                error_message="Internal Server Error.",
                status_code=500,
            )

    @staticmethod
    def get_recording(db: Session, recording_id: int):
        try:
            recording = db.get(SpeechRecording, recording_id)
            if recording is None:
                return ApiResponse.error(
                    error_message="Recording not found.", status_code=404
                )
            return ApiResponse.success(
                data={
                    "recordingId": recording.recording_id,
                    "filename": recording.filename,
                    "contentType": recording.content_type,
                    "transcription": recording.transcript,
                    "audioUrl": f"/stt/recordings/{recording.recording_id}/audio",
                    "createdAt": (
                        recording.created_at.isoformat()
                        if recording.created_at
                        else None
                    ),
                },
                message="Recording fetched successfully.",
            )
        except Exception:
            logger.exception("Exception occurred while fetching recording.")
            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )

    @staticmethod
    def get_recording_audio(db: Session, recording_id: int):
        from fastapi.responses import Response

        try:
            recording = db.get(SpeechRecording, recording_id)
            if recording is None:
                return ApiResponse.error(
                    error_message="Recording not found.", status_code=404
                )
            return Response(
                content=recording.audio_data,
                media_type=recording.content_type,
            )
        except Exception:
            logger.exception("Exception occurred while fetching recording audio.")
            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )


import re

# =========================================================
# GUJARATI FABRICATION FORMATTER
# Production Ready
# =========================================================

# ---------------------------------------------------------
# Gujarati Unicode Digits -> English Digits
# Example:
# ૧૫ -> 15
# ---------------------------------------------------------


def gujarati_digit_to_english(text):

    translation_table = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")

    return text.translate(translation_table)


# ---------------------------------------------------------
# Gujarati Word Numbers
# ---------------------------------------------------------


# ---------------------------------------------------------
# Units Mapping
# ---------------------------------------------------------

UNIT_MAP = {
    # MM
    "એમએમ": "mm",
    "એમ એમ": "mm",
    "મિલીમીટર": "mm",
    # CM
    "સેન્ટિમીટર": "cm",
    "સેન્ટીમીટર": "cm",
    "સી એમ": "cm",
    # Meter
    "મીટર": "m",
    # Feet
    "ફૂટ": "ft",
    "ફિટ": "ft",
    # Inch
    "ઇંચ": "inch",
    # Weight
    "કિલો": "kg",
    "કિલોગ્રામ": "kg",
    "ગ્રામ": "gm",
    # Liquid
    "લિટર": "ltr",
    "મિલીલીટર": "ml",
    # Area
    "સ્ક્વેર ફૂટ": "sqft",
    "સ્ક્વેર મીટર": "sqm",
}


# ---------------------------------------------------------
# Fabrication Terms
# ---------------------------------------------------------

FABRICATION_TERMS = {
    # "પ્લેટ": "plate",
    # "પાઈપ": "pipe",
    # "પાઇપ": "pipe",
    # "એંગલ": "angle",
    # "ચેનલ": "channel",
    # "રોડ": "rod",
    # "સળિયો": "rod",
    # "વેલ્ડિંગ": "welding",
    # "કટિંગ": "cutting",
    # "દરવાજો": "door",
    # "ગેટ": "gate",
    # "જાળી": "jali",
}


# ---------------------------------------------------------
# Convert Gujarati Word Numbers
# ---------------------------------------------------------

import re

NUMBER_WORDS = {
    "એક": "1",
    "બે": "2",
    "ત્રણ": "3",
    "ચાર": "4",
    "પાંચ": "5",
    "છ": "6",
    "સાત": "7",
    "આઠ": "8",
    "નવ": "9",
    "દસ": "10",
    "અગિયાર": "11",
    "બાર": "12",
    "તેર": "13",
    "ચૌદ": "14",
    "પંદર": "15",
    "સોળ": "16",
    "સત્તર": "17",
    "અઢાર": "18",
    "ઓગણીસ": "19",
    "વીસ": "20",
    "એકવીસ": "21",
    "બાવીસ": "22",
    "તેવીસ": "23",
    "ચોવીસ": "24",
    "પચ્ચીસ": "25",
    "છવ્વીસ": "26",
    "સત્તાવીસ": "27",
    "અઠ્ઠાવીસ": "28",
    "ઓગણત્રીસ": "29",
    "ત્રીસ": "30",
    "એકત્રીસ": "31",
    "બત્રીસ": "32",
    "તેત્રીસ": "33",
    "ચોત્રીસ": "34",
    "પાંત્રીસ": "35",
    "છત્રીસ": "36",
    "સડત્રીસ": "37",
    "અડત્રીસ": "38",
    "ઓગણચાલીસ": "39",
    "ચાલીસ": "40",
    "એકતાલીસ": "41",
    "બેતાલીસ": "42",
    "ત્રેતાલીસ": "43",
    "ચુંમાલીસ": "44",
    "પિસ્તાલીસ": "45",
    "છેતાલીસ": "46",
    "સુડતાલીસ": "47",
    "અડતાલીસ": "48",
    "ઓગણપચાસ": "49",
    "પચાસ": "50",
    "એકાવન": "51",
    "બાવન": "52",
    "ત્રેપન": "53",
    "ચોપન": "54",
    "પંચાવન": "55",
    "છપ્પન": "56",
    "સત્તાવન": "57",
    "અઠ્ઠાવન": "58",
    "ઓગણસાઠ": "59",
    "સાઠ": "60",
    "એકસઠ": "61",
    "બાસઠ": "62",
    "ત્રેસઠ": "63",
    "ચોસઠ": "64",
    "પાંસઠ": "65",
    "છાસઠ": "66",
    "સડસઠ": "67",
    "અડસઠ": "68",
    "અગણોસિત્તેર": "69",
    "સિત્તેર": "70",
    "એકોતેર": "71",
    "બોતેર": "72",
    "તોતેર": "73",
    "ચુમોતેર": "74",
    "પંચોતેર": "75",
    "છોતેર": "76",
    "સિત્યોતેર": "77",
    "ઇઠ્યોતેર": "78",
    "ઓગણએંસી": "79",
    "એંસી": "80",
    "એક્યાસી": "81",
    "બ્યાસી": "82",
    "ત્ર્યાસી": "83",
    "ચોર્યાસી": "84",
    "પંચ્યાસી": "85",
    "છ્યાસી": "86",
    "સત્યાસી": "87",
    "ઈઠ્યાસી": "88",
    "નેવ્યાસી": "89",
    "નેવું": "90",
    "એકાણું": "91",
    "બાણું": "92",
    "ત્રાણું": "93",
    "ચોરાણું": "94",
    "પંચાણું": "95",
    "છન્નું": "96",
    "સત્તાણું": "97",
    "અઠ્ઠાણું": "98",
    "નવ્વાણું": "99",
    "સો": "100",
}


def convert_gujarati_words(text: str) -> str:
    """
    Replace ONLY standalone Gujarati number words.
    Never replaces words like:
        છે
        નવા
        નવી
        નવાં
        છઠ્ઠું
    """

    tokens = re.findall(r"[\u0A80-\u0AFF]+|[0-9]+|[^\s]", text)

    result = []

    for token in tokens:
        if token in NUMBER_WORDS:
            result.append(NUMBER_WORDS[token])
        else:
            result.append(token)

    text = " ".join(result)

    # remove unwanted spaces before punctuation
    text = re.sub(r"\s+([,.!?])", r"\1", text)

    return text


# ---------------------------------------------------------
# Main Formatter
# ---------------------------------------------------------


def fabrication_formatter(text):

    # -----------------------------------------------------
    # Initial Cleanup
    # -----------------------------------------------------

    text = str(text).strip()

    # -----------------------------------------------------
    # Gujarati Digit -> English Digit
    # ૧૫ -> 15
    # -----------------------------------------------------

    text = gujarati_digit_to_english(text)

    # -----------------------------------------------------
    # Gujarati Word Numbers
    # પંદર -> 15
    # -----------------------------------------------------

    text = convert_gujarati_words(text)

    # -----------------------------------------------------
    # Normalize Units
    # -----------------------------------------------------

    for guj, eng in UNIT_MAP.items():

        text = re.sub(rf"\b{re.escape(guj)}\b", eng, text, flags=re.IGNORECASE)

    # -----------------------------------------------------
    # Multiplication Patterns
    #
    # 15 બાય 25
    # 15 x 25
    # 15 ગુણ્યા 25
    # 15*25
    #
    # =>
    #
    # 15*25
    # -----------------------------------------------------

    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*(?:બાય|ગુણ્યા|ગણ્યા|x|X|\*)\s*(\d+(?:\.\d+)?)",
        r"\1*\2",
        text,
    )

    # -----------------------------------------------------
    # Range Patterns
    #
    # 15 થી 30
    #
    # =>
    #
    # 15 to 30
    # -----------------------------------------------------

    text = re.sub(r"(\d+(?:\.\d+)?)\s*થી\s*(\d+(?:\.\d+)?)", r"\1 to \2", text)

    # -----------------------------------------------------
    # Add Space Before Units
    #
    # 5mm -> 5 mm
    # -----------------------------------------------------

    text = re.sub(r"(\d)(mm|cm|m|ft|inch|kg|gm|ltr|ml|sqft|sqm)", r"\1 \2", text)

    # -----------------------------------------------------
    # Remove Duplicate *
    # -----------------------------------------------------

    text = re.sub(r"\*+", "*", text)

    # -----------------------------------------------------
    # Remove Extra Spaces
    # -----------------------------------------------------

    text = re.sub(r"\s+", " ", text).strip()

    return text
