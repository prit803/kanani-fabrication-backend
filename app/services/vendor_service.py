from sqlalchemy.orm import Session

from app.models.vendor_model import Vendor
from app.schemas.vendor_schema import VendorRequest
from app.utils.helper import model_to_dict, models_to_list
from app.utils.logger import get_logger
from app.utils.response import ApiResponse

logger = get_logger(__name__)


class VendorService:

    @staticmethod
    def get_vendor(
        db: Session,
        vendor_id: int | None = None
    ):
        """
        Get Vendor List or Single Vendor
        """

        try:

            logger.info("Fetching vendor data.")

            if vendor_id is not None:

                logger.info(f"Fetching vendor id : {vendor_id}")

                vendor = (
                    db.query(Vendor)
                    .filter(
                        Vendor.vendor_id == vendor_id,
                        Vendor.is_deleted.is_(False)
                    )
                    .first()
                )

                if vendor is None:

                    logger.warning(
                        f"Vendor not found. Vendor Id : {vendor_id}"
                    )

                    return ApiResponse.error(
                        error_message="Vendor not found.",
                        status_code=404
                    )

                logger.info(
                    f"Vendor fetched successfully. Vendor Id : {vendor_id}"
                )

                return ApiResponse.success(
                    data=model_to_dict(vendor),
                    message="Vendor fetched successfully."
                )

            vendors = (
                db.query(Vendor)
                .filter(
                    Vendor.is_deleted.is_(False)
                )
                .order_by(
                    Vendor.vendor_name.asc()
                )
                .all()
            )

            logger.info(
                f"Total vendors fetched : {len(vendors)}"
            )

            return ApiResponse.success(
                data=models_to_list(vendors),
                message="Vendor list fetched successfully."
            )

        except Exception as ex:

            logger.exception(
                "Exception occurred while fetching vendor."
            )

            return ApiResponse.error(
                error_message="Internal Server Error.",
                status_code=500
            )

    @staticmethod
    def save_vendor(
        db: Session,
        request: VendorRequest
    ):
        """
        Create or Update Vendor
        """

        try:

            if request.vendor_id is not None:

                logger.info(
                    f"Updating vendor. Vendor Id : {request.vendor_id}"
                )

                vendor = (
                    db.query(Vendor)
                    .filter(
                        Vendor.vendor_id == request.vendor_id,
                        Vendor.is_deleted.is_(False)
                    )
                    .first()
                )

                if vendor is None:

                    logger.warning(
                        f"Vendor not found. Vendor Id : {request.vendor_id}"
                    )

                    return ApiResponse.error(
                        error_message="Vendor not found.",
                        status_code=404
                    )

                message = "Vendor updated successfully."

            else:

                logger.info("Creating new vendor.")

                vendor = Vendor()

                db.add(vendor)

                message = "Vendor created successfully."

            # Save Data

            vendor.vendor_name = request.vendor_name.strip()
            vendor.mobile_number = request.mobile_number.strip()
            vendor.shop_name = (
                request.shop_name.strip()
                if request.shop_name
                else None
            )

            vendor.address = (
                request.address.strip()
                if request.address
                else None
            )

            vendor.photo_url = request.photo_url

            vendor.status = request.status

            db.commit()

            db.refresh(vendor)

            logger.info(message)

            return ApiResponse.success(
                data=model_to_dict(vendor),
                message=message
            )

        except Exception as ex:

            db.rollback()

            logger.exception(
                "Exception occurred while saving vendor."
            )

            return ApiResponse.error(
                error_message="Internal Server Error.",
                status_code=500
            )

    @staticmethod
    def delete_vendor(
        db: Session,
        vendor_id: int
    ):
        """
        Soft Delete Vendor
        """

        try:

            logger.info(
                f"Deleting vendor. Vendor Id : {vendor_id}"
            )

            vendor = (
                db.query(Vendor)
                .filter(
                    Vendor.vendor_id == vendor_id,
                    Vendor.is_deleted.is_(False)
                )
                .first()
            )

            if vendor is None:

                logger.warning(
                    f"Vendor not found. Vendor Id : {vendor_id}"
                )

                return ApiResponse.error(
                    error_message="Vendor not found.",
                    status_code=404
                )

            vendor.is_deleted = True

            db.commit()

            logger.info(
                f"Vendor deleted successfully. Vendor Id : {vendor_id}"
            )

            return ApiResponse.success(
                data=None,
                message="Vendor deleted successfully."
            )

        except Exception:

            db.rollback()

            logger.exception(
                "Exception occurred while deleting vendor."
            )

            return ApiResponse.error(
                error_message="Internal Server Error.",
                status_code=500
            )