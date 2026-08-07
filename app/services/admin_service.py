from pathlib import Path
import os

from app.utils.response import ApiResponse
from app.utils.logger import get_logger

import shutil
from pathlib import Path
from fastapi import UploadFile


logger = get_logger(__name__)


class AdminService:

    @staticmethod
    def delete_database():

        try:

            db_path = Path("kanani.db")

            if not db_path.exists():

                return ApiResponse.error(
                    error_message="Database file not found.",
                    status_code=404
                )

            os.remove(db_path)

            logger.info("Database deleted successfully.")

            return ApiResponse.success(
                data=None,
                message="Database deleted successfully."
            )

        except Exception:

            logger.exception(
                "Error deleting database."
            )

            return ApiResponse.error(
                error_message="Internal Server Error.",
                status_code=500
            )

    @staticmethod
    def upload_database(
        file: UploadFile
    ):

        try:

            if not file.filename.endswith(".db"):

                return ApiResponse.error(
                    error_message="Only .db file is allowed.",
                    status_code=400
                )

            db_path = Path("kanani.db")

            if db_path.exists():
                db_path.unlink()

            with open(db_path, "wb") as buffer:
                shutil.copyfileobj(
                    file.file,
                    buffer
                )

            logger.info(
                "Database uploaded successfully."
            )

            return ApiResponse.success(
                data=None,
                message="Database uploaded successfully."
            )

        except Exception:

            logger.exception(
                "Error uploading database."
            )

            return ApiResponse.error(
                error_message="Internal Server Error.",
                status_code=500
            )