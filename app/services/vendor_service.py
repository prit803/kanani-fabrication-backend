from datetime import datetime
import asyncio
import shutil
from pathlib import Path

from fastapi import UploadFile
from googletrans import Translator
from sqlalchemy.orm import Session

from app.models.vendor_model import Vendor
from app.utils.helper import model_to_dict, models_to_list
from app.utils.logger import get_logger
from app.utils.response import ApiResponse

logger = get_logger(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]
VENDOR_PHOTO_FOLDER = BASE_DIR / "storage" / "vendors"
VENDOR_PHOTO_FOLDER.mkdir(parents=True, exist_ok=True)


async def _translate_to_gu(text: str) -> str:
    translator = Translator()
    result = await translator.translate(text, src="en", dest="gu")
    print(f"Translated '{text}' to Gujarati: '{result.text}'")
    return result.text


def en_to_gu(text: str | None) -> str | None:
    if not text:
        return text
    return asyncio.run(_translate_to_gu(text))


class VendorService:

    @staticmethod
    def get_vendor(db: Session, vendor_id: int | None = None):
        """
        Get Vendor List or Single Vendor
        """

        try:

            logger.info("Fetching vendor data.")

            if vendor_id is not None:

                logger.info(f"Fetching vendor id : {vendor_id}")

                vendor = (
                    db.query(Vendor)
                    .filter(Vendor.vendor_id == vendor_id, Vendor.is_deleted.is_(False))
                    .first()
                )

                if vendor is None:

                    logger.warning(f"Vendor not found. Vendor Id : {vendor_id}")

                    return ApiResponse.error(
                        error_message="Vendor not found.", status_code=404
                    )

                logger.info(f"Vendor fetched successfully. Vendor Id : {vendor_id}")

                return ApiResponse.success(
                    data=model_to_dict(vendor), message="Vendor fetched successfully."
                )

            vendors = (
                db.query(Vendor)
                .filter(Vendor.is_deleted.is_(False))
                .order_by(Vendor.vendor_name.asc())
                .all()
            )

            logger.info(f"Total vendors fetched : {len(vendors)}")

            return ApiResponse.success(
                data=models_to_list(vendors),
                message="Vendor list fetched successfully.",
            )

        except Exception as ex:

            logger.exception("Exception occurred while fetching vendor.")

            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )

    @staticmethod
    def save_vendor(
        db: Session,
        vendor_id: int | None,
        vendor_name: str,
        mobile_number: str,
        shop_name: str | None = None,
        address: str | None = None,
        status: str = "active",
        photo_file: UploadFile | None = None,
    ):
        """
        Create or Update Vendor
        """

        try:

            if vendor_id is not None:

                logger.info(f"Updating vendor. Vendor Id : {vendor_id}")

                vendor = (
                    db.query(Vendor)
                    .filter(Vendor.vendor_id == vendor_id, Vendor.is_deleted.is_(False))
                    .first()
                )

                if vendor is None:

                    logger.warning(f"Vendor not found. Vendor Id : {vendor_id}")

                    return ApiResponse.error(
                        error_message="Vendor not found.", status_code=404
                    )

                message = "Vendor updated successfully."

            else:

                logger.info("Creating new vendor.")

                vendor = Vendor()

                db.add(vendor)

                message = "Vendor created successfully."

            # Save Data

            vendor.vendor_name = en_to_gu(vendor_name.strip())
            vendor.mobile_number = mobile_number.strip()
            vendor.shop_name = en_to_gu(shop_name.strip()) if shop_name else None
            vendor.address = en_to_gu(address.strip()) if address else None

            if photo_file and photo_file.filename:

                safe_file_name = Path(photo_file.filename).name
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                file_extension = Path(safe_file_name).suffix.lower()
                stored_file_name = (
                    f"vendor_{vendor_id or 'new'}_{timestamp}{file_extension}"
                )
                photo_path = VENDOR_PHOTO_FOLDER / stored_file_name

                with open(photo_path, "wb") as buffer:
                    shutil.copyfileobj(photo_file.file, buffer)

                # Store URL path (served by FastAPI or nginx) instead of filesystem path
                vendor.photo_url = f"/storage/vendors/{stored_file_name}"

                logger.info(f"Vendor photo saved at : {photo_path}")

            elif vendor_id is None:

                vendor.photo_url = None

            vendor.status = status

            db.commit()

            db.refresh(vendor)

            logger.info(message)

            return ApiResponse.success(data=model_to_dict(vendor), message=message)

        except Exception as ex:

            db.rollback()

            logger.exception("Exception occurred while saving vendor.")

            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )

    @staticmethod
    def delete_vendor(db: Session, vendor_id: int):
        """
        Soft Delete Vendor
        """

        try:

            logger.info(f"Deleting vendor. Vendor Id : {vendor_id}")

            vendor = (
                db.query(Vendor)
                .filter(Vendor.vendor_id == vendor_id, Vendor.is_deleted.is_(False))
                .first()
            )

            if vendor is None:

                logger.warning(f"Vendor not found. Vendor Id : {vendor_id}")

                return ApiResponse.error(
                    error_message="Vendor not found.", status_code=404
                )

            vendor.is_deleted = True

            db.commit()

            logger.info(f"Vendor deleted successfully. Vendor Id : {vendor_id}")

            return ApiResponse.success(
                data=None, message="Vendor deleted successfully."
            )

        except Exception:

            db.rollback()

            logger.exception("Exception occurred while deleting vendor.")

            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )
