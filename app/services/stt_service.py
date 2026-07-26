

from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from app.utils.logger import get_logger
from app.utils.response import ApiResponse
from app.services.stt_client import client as stt_client


logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_FOLDER = BASE_DIR / "storage" / "stt" / "input"
OUTPUT_FOLDER = BASE_DIR / "storage" / "stt" / "output"

INPUT_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


class STTService:

    @staticmethod
    async def speech_to_text(file: UploadFile):

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

                logger.warning(
                    f"Unsupported audio file type : {file_extension}"
                )

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

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            input_file_path = INPUT_FOLDER / f"{timestamp}_{safe_file_name}"
            output_file_path = OUTPUT_FOLDER / f"{timestamp}.txt"

            file_content = await file.read()

            with open(input_file_path, "wb") as buffer:

                buffer.write(file_content)

            logger.info(f"Audio file saved at : {input_file_path}")

            with open(input_file_path, "rb") as audio_file:

                response = stt_client.speech_to_text.transcribe(
                    file=audio_file,
                    model="saaras:v3",
                    mode="transcribe",
                )

            transcript = getattr(response, "transcript", None)

            if transcript is None and isinstance(response, dict):

                transcript = response.get("transcript")

            formatted_text = fabrication_formatter(transcript or "")

            with open(output_file_path, "w", encoding="utf-8") as text_file:

                text_file.write(formatted_text)

            data = {
                "inputFile": str(input_file_path),
                "outputFile": str(output_file_path),
                "transcription": formatted_text,
            }

            logger.info("Speech to text transcription completed successfully.")

            return ApiResponse.success(
                data=data,
                message="Speech to text completed successfully."
            )

        except Exception:

            logger.exception(
                "Exception occurred while processing speech to text."
            )

            return ApiResponse.error(
                error_message="Internal Server Error.",
                status_code=500,
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
    "શૂન્ય": "0",
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
    "ચાલીસ": "40",
    "પચાસ": "50",
    "સાઠ": "60",
    "સિત્તેર": "70",
    "એંસી": "80",
    "નેવું": "90",
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
