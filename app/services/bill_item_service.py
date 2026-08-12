from sqlalchemy.orm import Session

from app.models.bill_item_model import BillItem
from app.models.bill_model import Bill
from app.models.vendor_model import Vendor
from pathlib import Path
from datetime import date

from app.utils.helper import model_to_dict, models_to_list
from app.utils.logger import get_logger
from app.utils.response import ApiResponse

logger = get_logger(__name__)


class BillItemService:

    @staticmethod
    def get_bill_item(
        db: Session, bill_item_id: int | None = None, bill_id: int | None = None
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

                logger.info(f"Fetching bill item id : {bill_item_id}")

                bill_item = (
                    db.query(BillItem)
                    .filter(
                        BillItem.bill_item_id == bill_item_id,
                        BillItem.is_deleted.is_(False),
                    )
                    .first()
                )

                if bill_item is None:

                    logger.warning(
                        f"Bill Item not found. Bill Item Id : {bill_item_id}"
                    )

                    return ApiResponse.error(
                        error_message="Bill Item not found.", status_code=404
                    )

                response = model_to_dict(bill_item)

                if bill_item.bill:

                    response["bill"] = model_to_dict(bill_item.bill)

                logger.info(
                    f"Bill Item fetched successfully. Bill Item Id : {bill_item_id}"
                )

                return ApiResponse.success(
                    data=response, message="Bill Item fetched successfully."
                )

            # ----------------------------------------
            # Get Bill Items By Bill Id
            # ----------------------------------------

            query = db.query(BillItem).filter(BillItem.is_deleted.is_(False))

            if bill_id is not None:

                logger.info(f"Fetching bill items for Bill Id : {bill_id}")

                query = query.filter(BillItem.bill_id == bill_id)

            bill_items = query.order_by(BillItem.bill_item_id.asc()).all()

            response = []

            for item in bill_items:

                row = model_to_dict(item)

                if item.bill:

                    row["bill"] = model_to_dict(item.bill)

                response.append(row)

            logger.info(f"Total bill items fetched : {len(response)}")

            return ApiResponse.success(
                data=response, message="Bill Item list fetched successfully."
            )

        except Exception:

            logger.exception("Exception occurred while fetching bill items.")

            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )

    @staticmethod
    def save_bill_item(db: Session, request):
        """
        Create or Update multiple Bill Items in one API call.

        If `request.bill_id` is not provided, a new Bill will be created
        using `request.vendor_id`, `request.bill_date` (defaults to today)
        and `request.status`.
        """

        try:

            # Determine or create Bill
            bill = None

            if getattr(request, "bill_id", None):
                bill = (
                    db.query(Bill)
                    .filter(Bill.bill_id == request.bill_id, Bill.is_deleted.is_(False))
                    .first()
                )

                if bill is None:
                    logger.warning(f"Bill not found. Bill Id : {request.bill_id}")

                    return ApiResponse.error(
                        error_message="Bill not found.", status_code=404
                    )

            else:
                # Create new bill - vendor must be provided and exist
                if not getattr(request, "vendor_id", None):
                    return ApiResponse.error(
                        error_message="vendor_id is required when creating a new bill.",
                        status_code=400,
                    )

                vendor = (
                    db.query(Vendor)
                    .filter(
                        Vendor.vendor_id == request.vendor_id,
                        Vendor.is_deleted.is_(False),
                    )
                    .first()
                )

                if not vendor:
                    return ApiResponse.error(
                        error_message="Vendor not found.", status_code=404
                    )

                bill = Bill()
                bill.vendor_id = request.vendor_id
                bill.bill_date = getattr(request, "bill_date", None) or date.today()
                if getattr(request, "status", None):
                    bill.status = request.status

                db.add(bill)
                # flush to get bill_id for the items
                db.commit()
                db.refresh(bill)

            processed_items = []

            for item_req in request.items:

                # Update existing bill item
                if getattr(item_req, "bill_item_id", None) is not None:

                    bill_item = (
                        db.query(BillItem)
                        .filter(
                            BillItem.bill_item_id == item_req.bill_item_id,
                            BillItem.is_deleted.is_(False),
                        )
                        .first()
                    )

                    if bill_item is None:
                        logger.warning(f"Bill Item not found : {item_req.bill_item_id}")

                        return ApiResponse.error(
                            error_message=f"Bill Item not found: {item_req.bill_item_id}",
                            status_code=404,
                        )

                else:
                    bill_item = BillItem()
                    db.add(bill_item)

                # Save fields
                bill_item.bill_id = bill.bill_id
                bill_item.item_description = item_req.item_description.strip()
                bill_item.quantity = item_req.quantity
                bill_item.rate = item_req.rate
                bill_item.amount = item_req.quantity * item_req.rate

                # Normalize audio file path to storage URL if necessary
                audio_val = getattr(item_req, "audio_file_url", None)
                if audio_val:
                    # If already a storage URL, keep as-is
                    if str(audio_val).startswith("/storage"):
                        bill_item.audio_file_url = str(audio_val)
                    else:
                        p = Path(str(audio_val))
                        parts = p.parts
                        if "storage" in parts:
                            idx = parts.index("storage")
                            rel = Path(*parts[idx:])
                            bill_item.audio_file_url = f"/{rel.as_posix()}"
                        else:
                            # fallback: store only file name under stt input
                            bill_item.audio_file_url = f"/storage/stt/input/{p.name}"

                # flush so we can refresh later
                db.commit()
                db.refresh(bill_item)

                processed_items.append(bill_item)

            # Prepare response
            response_items = []

            for bi in processed_items:
                row = model_to_dict(bi)
                row["bill"] = model_to_dict(bill)
                response_items.append(row)

            message = "Bill items processed successfully."

            logger.info(message)

            return ApiResponse.success(
                data={"bill_id": bill.bill_id, "items": response_items}, message=message
            )

        except Exception:

            db.rollback()

            logger.exception("Exception occurred while saving Bill Item(s).")

            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )

    @staticmethod
    def delete_bill_item(db: Session, bill_item_id: int):
        """
        Soft Delete Bill Item
        """

        try:

            logger.info(f"Deleting Bill Item. Bill Item Id : {bill_item_id}")

            bill_item = (
                db.query(BillItem)
                .filter(
                    BillItem.bill_item_id == bill_item_id,
                    BillItem.is_deleted.is_(False),
                )
                .first()
            )

            if bill_item is None:

                logger.warning(f"Bill Item not found. Bill Item Id : {bill_item_id}")

                return ApiResponse.error(
                    error_message="Bill Item not found.", status_code=404
                )

            bill_item.is_deleted = True

            db.commit()

            logger.info(
                f"Bill Item deleted successfully. Bill Item Id : {bill_item_id}"
            )

            return ApiResponse.success(
                data=None, message="Bill Item deleted successfully."
            )

        except Exception:

            db.rollback()

            logger.exception("Exception occurred while deleting Bill Item.")

            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )
