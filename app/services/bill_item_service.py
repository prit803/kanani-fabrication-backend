from sqlalchemy.orm import Session

from app.models.bill_item_model import BillItem
from app.models.bill_model import Bill

from app.utils.helper import (
    model_to_dict,
    models_to_list
)
from app.utils.logger import get_logger
from app.utils.response import ApiResponse


logger = get_logger(__name__)


class BillItemService:

    @staticmethod
    def get_bill_item(
        db: Session,
        bill_item_id: int | None = None,
        bill_id: int | None = None
    ):
        """
        Get Bill Item List / Single Bill Item
        """

        try:

            logger.info("Fetching bill item data.")

            # ----------------------------------------
            # Get Single Bill Item
            # ----------------------------------------

            if bill_item_id is not None:

                logger.info(
                    f"Fetching bill item id : {bill_item_id}"
                )

                bill_item = (
                    db.query(BillItem)
                    .filter(
                        BillItem.bill_item_id == bill_item_id,
                        BillItem.is_deleted.is_(False)
                    )
                    .first()
                )

                if bill_item is None:

                    logger.warning(
                        f"Bill Item not found. Bill Item Id : {bill_item_id}"
                    )

                    return ApiResponse.error(
                        error_message="Bill Item not found.",
                        status_code=404
                    )

                response = model_to_dict(bill_item)

                if bill_item.bill:

                    response["bill"] = model_to_dict(
                        bill_item.bill
                    )

                logger.info(
                    f"Bill Item fetched successfully. Bill Item Id : {bill_item_id}"
                )

                return ApiResponse.success(
                    data=response,
                    message="Bill Item fetched successfully."
                )

            # ----------------------------------------
            # Get Bill Items By Bill Id
            # ----------------------------------------

            query = (
                db.query(BillItem)
                .filter(
                    BillItem.is_deleted.is_(False)
                )
            )

            if bill_id is not None:

                logger.info(
                    f"Fetching bill items for Bill Id : {bill_id}"
                )

                query = query.filter(
                    BillItem.bill_id == bill_id
                )

            bill_items = (
                query
                .order_by(
                    BillItem.bill_item_id.asc()
                )
                .all()
            )

            response = []

            for item in bill_items:

                row = model_to_dict(item)

                if item.bill:

                    row["bill"] = model_to_dict(
                        item.bill
                    )

                response.append(row)

            logger.info(
                f"Total bill items fetched : {len(response)}"
            )

            return ApiResponse.success(
                data=response,
                message="Bill Item list fetched successfully."
            )

        except Exception:

            logger.exception(
                "Exception occurred while fetching bill items."
            )

            return ApiResponse.error(
                error_message="Internal Server Error.",
                status_code=500
            )

    @staticmethod
    def save_bill_item(
        db: Session,
        request
    ):
        """
        Create or Update Bill Item
        """

        try:

            # ----------------------------------------
            # Validate Bill
            # ----------------------------------------

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

            # ----------------------------------------
            # Update
            # ----------------------------------------

            if request.bill_item_id is not None:

                logger.info(
                    f"Updating Bill Item : {request.bill_item_id}"
                )

                bill_item = (
                    db.query(BillItem)
                    .filter(
                        BillItem.bill_item_id == request.bill_item_id,
                        BillItem.is_deleted.is_(False)
                    )
                    .first()
                )

                if bill_item is None:

                    logger.warning(
                        f"Bill Item not found : {request.bill_item_id}"
                    )

                    return ApiResponse.error(
                        error_message="Bill Item not found.",
                        status_code=404
                    )

                message = "Bill Item updated successfully."

            # ----------------------------------------
            # Create
            # ----------------------------------------

            else:

                logger.info(
                    "Creating new Bill Item."
                )

                bill_item = BillItem()

                db.add(bill_item)

                message = "Bill Item created successfully."

            # ----------------------------------------
            # Save Data
            # ----------------------------------------

            bill_item.bill_id = request.bill_id

            bill_item.item_description = (
                request.item_description.strip()
            )

            bill_item.quantity = request.quantity

            bill_item.rate = request.rate

            bill_item.amount = request.quantity * request.rate

            db.commit()

            db.refresh(bill_item)

            response = model_to_dict(
                bill_item
            )

            response["bill"] = model_to_dict(
                bill
            )

            logger.info(message)

            return ApiResponse.success(
                data=response,
                message=message
            )

        except Exception:

            db.rollback()

            logger.exception(
                "Exception occurred while saving Bill Item."
            )

            return ApiResponse.error(
                error_message="Internal Server Error.",
                status_code=500
            )


    @staticmethod
    def delete_bill_item(
        db: Session,
        bill_item_id: int
    ):
        """
        Soft Delete Bill Item
        """

        try:

            logger.info(
                f"Deleting Bill Item. Bill Item Id : {bill_item_id}"
            )

            bill_item = (
                db.query(BillItem)
                .filter(
                    BillItem.bill_item_id == bill_item_id,
                    BillItem.is_deleted.is_(False)
                )
                .first()
            )

            if bill_item is None:

                logger.warning(
                    f"Bill Item not found. Bill Item Id : {bill_item_id}"
                )

                return ApiResponse.error(
                    error_message="Bill Item not found.",
                    status_code=404
                )

            bill_item.is_deleted = True

            db.commit()

            logger.info(
                f"Bill Item deleted successfully. Bill Item Id : {bill_item_id}"
            )

            return ApiResponse.success(
                data=None,
                message="Bill Item deleted successfully."
            )

        except Exception:

            db.rollback()

            logger.exception(
                "Exception occurred while deleting Bill Item."
            )

            return ApiResponse.error(
                error_message="Internal Server Error.",
                status_code=500
            )