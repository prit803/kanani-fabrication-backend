import logging
import os
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
import speech_recognition as sr
from fastapi import UploadFile

from app.utils.response import ApiResponse

logger = logging.getLogger(__name__)

LANGUAGE = "gu-IN"
CHUNK_SECONDS = 30


def convert_to_wav(src_path: str, dst_path: str) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
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
        raise ValueError(result.stderr.decode(errors="ignore"))


class GujaratiSTTService:
    @staticmethod
    def speech_to_text_upload(file: UploadFile):
        if not file.filename:
            return ApiResponse.error(
                error_message="Audio file name is required.", status_code=400
            )

        recognizer = sr.Recognizer()
        texts = []

        try:
            suffix = Path(file.filename).suffix
            contents = file.file.read()

            with tempfile.TemporaryDirectory() as tmp:
                src_path = os.path.join(tmp, f"input{suffix}")
                dst_path = os.path.join(tmp, "output.wav")
                with open(src_path, "wb") as source_file:
                    source_file.write(contents)

                convert_to_wav(src_path, dst_path)

                with sr.AudioFile(dst_path) as source:
                    logger.info(
                        "Received %s, duration %.1fs",
                        file.filename,
                        source.DURATION,
                    )
                    while True:
                        audio = recognizer.record(source, duration=CHUNK_SECONDS)
                        if not audio.frame_data:
                            break
                        try:
                            texts.append(
                                recognizer.recognize_google(audio, language=LANGUAGE)
                            )
                        except sr.UnknownValueError:
                            continue

            if not texts:
                return ApiResponse.error(
                    error_message="Could not understand the audio.", status_code=422
                )

            return ApiResponse.success(
                data={"text": " ".join(texts), "language": LANGUAGE},
                message="Gujarati speech to text completed successfully.",
            )
        except ValueError:
            logger.warning("Invalid or unsupported audio file: %s", file.filename)
            return ApiResponse.error(
                error_message="Invalid or unsupported audio file.", status_code=400
            )
        except sr.RequestError:
            logger.exception("Gujarati speech recognition service request failed.")
            return ApiResponse.error(
                error_message="Speech recognition service is unavailable.",
                status_code=502,
            )
        except Exception:
            logger.exception("Exception occurred during Gujarati speech recognition.")
            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )
