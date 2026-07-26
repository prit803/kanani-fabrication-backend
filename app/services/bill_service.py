from sqlalchemy.orm import Session

from app.models.bill_model import Bill
from app.models.vendor_model import Vendor

from app.utils.helper import (
    model_to_dict,
    models_to_list
)
from app.utils.logger import get_logger
from app.utils.response import ApiResponse


logger = get_logger(__name__)


class BillService:

    @staticmethod
    def get_bill(
        db: Session,
        bill_id: int | None = None
    ):
        """
        Get Bill List or Single Bill
        """

        try:

            logger.info("Fetching bill data.")

            if bill_id is not None:

                logger.info(
                    f"Fetching bill id : {bill_id}"
                )

                bill = (
                    db.query(Bill)
                    .filter(
                        Bill.bill_id == bill_id,
                        Bill.is_deleted.is_(False)
                    )
                    .first()
                )

                if bill is None:

                    logger.warning(
                        f"Bill not found. Bill Id : {bill_id}"
                    )

                    return ApiResponse.error(
                        error_message="Bill not found.",
                        status_code=404
                    )

                data = model_to_dict(bill)

                if bill.vendor:

                    data["vendor"] = model_to_dict(
                        bill.vendor
                    )

                logger.info(
                    f"Bill fetched successfully. Bill Id : {bill_id}"
                )

                return ApiResponse.success(
                    data=data,
                    message="Bill fetched successfully."
                )

            bills = (
                db.query(Bill)
                .filter(
                    Bill.is_deleted.is_(False)
                )
                .order_by(
                    Bill.bill_date.desc(),
                    Bill.bill_id.desc()
                )
                .all()
            )

            response = []

            for bill in bills:

                item = model_to_dict(bill)

                if bill.vendor:

                    item["vendor"] = model_to_dict(
                        bill.vendor
                    )

                response.append(item)

            logger.info(
                f"Total bills fetched : {len(response)}"
            )

            return ApiResponse.success(
                data=response,
                message="Bill list fetched successfully."
            )

        except Exception:

            logger.exception(
                "Exception occurred while fetching bill."
            )

            return ApiResponse.error(
                error_message="Internal Server Error.",
                status_code=500
            )

    @staticmethod
    def save_bill(
        db: Session,
        request
    ):
        """
        Create or Update Bill
        """

        try:

            # -----------------------------
            # Validate Vendor
            # -----------------------------
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

            # -----------------------------
            # Update Bill
            # -----------------------------
            if request.bill_id is not None:

                logger.info(
                    f"Updating bill. Bill Id : {request.bill_id}"
                )

                bill = (
                    db.query(Bill)
                    .filter(
                        Bill.bill_id == request.bill_id,
                        Bill.is_deleted.is_(False)
                    )
                    .first()
                )

                if bill is None:

                    logger.warning(
                        f"Bill not found. Bill Id : {request.bill_id}"
                    )

                    return ApiResponse.error(
                        error_message="Bill not found.",
                        status_code=404
                    )

                message = "Bill updated successfully."

            # -----------------------------
            # Create Bill
            # -----------------------------
            else:

                logger.info("Creating new bill.")

                bill = Bill()

                db.add(bill)

                message = "Bill created successfully."

            # -----------------------------
            # Save Data
            # -----------------------------
            bill.vendor_id = request.vendor_id

            bill.bill_text_gujarati = (
                request.bill_text_gujarati.strip()
                if request.bill_text_gujarati
                else None
            )

            bill.amount = request.amount

            bill.bill_date = request.bill_date

            bill.status = request.status

            bill.audio_file_url = (
                request.audio_file_url.strip()
                if request.audio_file_url
                else None
            )

            db.commit()

            db.refresh(bill)

            response = model_to_dict(bill)

            response["vendor"] = model_to_dict(vendor)

            logger.info(message)

            return ApiResponse.success(
                data=response,
                message=message
            )

        except Exception:

            db.rollback()

            logger.exception(
                "Exception occurred while saving bill."
            )

            return ApiResponse.error(
                error_message="Internal Server Error.",
                status_code=500
            )


    