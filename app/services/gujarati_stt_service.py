import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

import imageio_ffmpeg
import speech_recognition as sr
from fastapi import UploadFile

from app.utils.logger import get_logger
from app.utils.response import ApiResponse

logger = get_logger(__name__)

LANGUAGE = "gu-IN"
CHUNK_SECONDS = 30
QUARRY_VARIANTS = re.compile(
    r"(?<![\w\u0A80-\u0AFF])"
    r"(?:કવરી|કવોરી|કવોરિ|કવૉરી|કુવારી|ક્વારી|ક્વૉરી|kavory|quarry)"
    r"(?![\w\u0A80-\u0AFF])",
    re.IGNORECASE,
)


def normalize_transcription(text: str) -> str:
    return QUARRY_VARIANTS.sub("ક્વોરી", text)


def convert_to_wav(src_path: str, dst_path: str) -> None:
    logger.info("Starting audio conversion to WAV.")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    conversion_started = time.perf_counter()
    result = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            src_path,
            "-ar",
            "16000",
            "-ac",
            "1",
            dst_path,
        ],
        capture_output=True,
    )
    if result.returncode != 0:
        error_message = result.stderr.decode(errors="ignore").strip()
        logger.error(
            "Audio conversion failed with exit code %s: %s",
            result.returncode,
            error_message,
        )
        raise ValueError(error_message)
    logger.info(
        "Audio conversion completed in %.2fs.",
        time.perf_counter() - conversion_started,
    )


class GujaratiSTTService:
    @staticmethod
    def speech_to_text_upload(file: UploadFile):
        if not file.filename:
            logger.warning("Gujarati STT request rejected: audio file name is missing.")
            return ApiResponse.error(
                error_message="Audio file name is required.", status_code=400
            )

        request_started = time.perf_counter()
        logger.info("Starting Gujarati STT for file %s.", file.filename)
        recognizer = sr.Recognizer()
        texts = []

        try:
            suffix = Path(file.filename).suffix
            contents = file.file.read()
            logger.info(
                "Read %s bytes from uploaded audio file %s.",
                len(contents),
                file.filename,
            )

            with tempfile.TemporaryDirectory() as tmp:
                src_path = os.path.join(tmp, f"input{suffix}")
                dst_path = os.path.join(tmp, "output.wav")
                with open(src_path, "wb") as source_file:
                    source_file.write(contents)
                logger.info("Saved uploaded audio to a temporary file.")

                convert_to_wav(src_path, dst_path)

                with sr.AudioFile(dst_path) as source:
                    logger.info(
                        "Opened converted audio for %s; duration %.1fs.",
                        file.filename,
                        source.DURATION,
                    )
                    chunk_number = 0
                    while True:
                        audio = recognizer.record(source, duration=CHUNK_SECONDS)
                        if not audio.frame_data:
                            logger.info(
                                "Finished reading audio chunks for %s; processed %s chunks.",
                                file.filename,
                                chunk_number,
                            )
                            break
                        chunk_number += 1
                        logger.info(
                            "Recognizing audio chunk %s for %s.",
                            chunk_number,
                            file.filename,
                        )
                        try:
                            recognized_text = recognizer.recognize_google(
                                audio, language=LANGUAGE
                            )
                            texts.append(recognized_text)
                            logger.info(
                                "Recognized chunk %s for %s: %s",
                                chunk_number,
                                file.filename,
                                recognized_text,
                            )
                        except sr.UnknownValueError:
                            logger.warning(
                                "Could not understand audio chunk %s for %s.",
                                chunk_number,
                                file.filename,
                            )
                            continue

            if not texts:
                logger.warning(
                    "Gujarati STT produced no recognized text for %s.",
                    file.filename,
                )
                return ApiResponse.error(
                    error_message="Could not understand the audio.", status_code=422
                )

            raw_transcription = " ".join(texts)
            transcription = normalize_transcription(raw_transcription)
            logger.info(
                "Transcription normalization for %s: raw=%r, normalized=%r.",
                file.filename,
                raw_transcription,
                transcription,
            )
            logger.info(
                "Gujarati STT completed for %s in %.2fs.",
                file.filename,
                time.perf_counter() - request_started,
            )
            return ApiResponse.success(
                data={"text": transcription, "language": LANGUAGE},
                message="Gujarati speech to text completed successfully.",
            )
        except ValueError as exc:
            logger.warning(
                "Invalid or unsupported audio file %s: %s",
                file.filename,
                exc,
            )
            return ApiResponse.error(
                error_message="Invalid or unsupported audio file.", status_code=400
            )
        except sr.RequestError:
            logger.exception(
                "Gujarati speech recognition service request failed for %s.",
                file.filename,
            )
            return ApiResponse.error(
                error_message="Speech recognition service is unavailable.",
                status_code=502,
            )
        except Exception:
            logger.exception(
                "Exception occurred during Gujarati speech recognition for %s.",
                file.filename,
            )
            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )
