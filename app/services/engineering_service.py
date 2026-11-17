from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.engineering_model import Engineering
from app.utils.helper import model_to_dict, models_to_list
from app.utils.logger import get_logger
from app.utils.media import InvalidImageError, image_data_uri_from_upload
from app.utils.response import ApiResponse

logger = get_logger(__name__)


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
                engineering.sign_image = image_data_uri_from_upload(sign_image)

            elif engineer_id is None:
                engineering.sign_image = None

            db.commit()
            db.refresh(engineering)

            logger.info(message)
            return ApiResponse.success(data=model_to_dict(engineering), message=message)

        except InvalidImageError as ex:
            db.rollback()
            return ApiResponse.error(error_message=str(ex), status_code=400)

        except Exception:
            db.rollback()
            logger.exception("Exception occurred while saving engineering.")
            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )
