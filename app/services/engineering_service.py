import shutil
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.engineering_model import Engineering
from app.utils.helper import model_to_dict, models_to_list
from app.utils.logger import get_logger
from app.utils.response import ApiResponse

logger = get_logger(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]
ENGINEERING_IMAGE_FOLDER = BASE_DIR / "storage" / "engineering"
ENGINEERING_IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)


class EngineeringService:

    @staticmethod
    def get_engineering(db: Session, engineer_id: int | None = None):
        """
        Get Engineering List or Single Engineering record.
        """

        try:
            logger.info("Fetching engineering data.")

            if engineer_id is not None:
                logger.info(f"Fetching engineer id : {engineer_id}")

                engineering = (
                    db.query(Engineering)
                    .filter(
                        Engineering.engineer_id == engineer_id,
                        Engineering.is_deleted.is_(False),
                    )
                    .first()
                )

                if engineering is None:
                    logger.warning(
                        f"Engineering not found. Engineer Id : {engineer_id}"
                    )
                    return ApiResponse.error(
                        error_message="Engineering not found.", status_code=404
                    )

                logger.info(
                    f"Engineering fetched successfully. Engineer Id : {engineer_id}"
                )
                return ApiResponse.success(
                    data=model_to_dict(engineering),
                    message="Engineering fetched successfully.",
                )

            engineers = (
                db.query(Engineering)
                .filter(Engineering.is_deleted.is_(False))
                .order_by(Engineering.name.asc())
                .all()
            )

            logger.info(f"Total engineers fetched : {len(engineers)}")
            return ApiResponse.success(
                data=models_to_list(engineers),
                message="Engineering list fetched successfully.",
            )

        except Exception:
            logger.exception("Exception occurred while fetching engineering data.")
            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )

    @staticmethod
    def save_engineering(
        db: Session,
        engineer_id: int | None,
        name: str,
        pan_number: str | None = None,
        bank_account_number: str | None = None,
        sign_image: UploadFile | None = None,
    ):
        """
        Create or Update Engineering in one API call.
        """

        try:
            if not name or not name.strip():
                return ApiResponse.error(
                    error_message="Name is required.", status_code=400
                )

            if engineer_id is not None:
                engineering = (
                    db.query(Engineering)
                    .filter(
                        Engineering.engineer_id == engineer_id,
                        Engineering.is_deleted.is_(False),
                    )
                    .first()
                )

                if engineering is None:
                    logger.warning(
                        f"Engineering not found. Engineer Id : {engineer_id}"
                    )
                    return ApiResponse.error(
                        error_message="Engineering not found.", status_code=404
                    )

                message = "Engineering updated successfully."
            else:
                engineering = Engineering()
                db.add(engineering)
                message = "Engineering created successfully."

            engineering.name = name.strip()
            engineering.pan_number = pan_number.strip() if pan_number else None
            engineering.bank_account_number = (
                bank_account_number.strip() if bank_account_number else None
            )

            if sign_image and sign_image.filename:
                safe_file_name = Path(sign_image.filename).name
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                file_extension = Path(safe_file_name).suffix.lower()
                stored_file_name = (
                    f"engineering_{engineer_id or 'new'}_{timestamp}{file_extension}"
                )
                image_path = ENGINEERING_IMAGE_FOLDER / stored_file_name

                with open(image_path, "wb") as buffer:
                    shutil.copyfileobj(sign_image.file, buffer)

                engineering.sign_image = f"/storage/engineering/{stored_file_name}"

            elif engineer_id is None:
                engineering.sign_image = None

            db.commit()
            db.refresh(engineering)

            logger.info(message)
            return ApiResponse.success(data=model_to_dict(engineering), message=message)

        except Exception:
            db.rollback()
            logger.exception("Exception occurred while saving engineering.")
            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )
