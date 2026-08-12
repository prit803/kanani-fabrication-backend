from sqlalchemy.orm import Session

from app.models.bill_model import Bill
from app.models.vendor_model import Vendor

from app.utils.helper import model_to_dict
from app.utils.logger import get_logger
from app.utils.response import ApiResponse
from jinja2 import Template
from weasyprint import HTML
from pathlib import Path
import threading
from datetime import datetime

from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.bill_model import Bill
from app.models.vendor_model import Vendor
from app.utils.response import ApiResponse
from app.utils.helper import model_to_dict
from app.models.bill_item_model import BillItem
from sqlalchemy import func

logger = get_logger(__name__)


class BillService:

    @staticmethod
    def get_bill(db: Session, bill_id: int | None = None):
        try:

            if bill_id is not None:

                bill = (
                    db.query(Bill)
                    .filter(Bill.bill_id == bill_id, Bill.is_deleted.is_(False))
                    .first()
                )

                if not bill:
                    return ApiResponse.error(
                        error_message="Bill not found.", status_code=404
                    )

                data = model_to_dict(bill)

                total_amount = sum(
                    float(item.amount)
                    for item in bill.bill_items
                    if not item.is_deleted
                )

                data["total_amount"] = total_amount

                return ApiResponse.success(
                    data=data, message="Bill fetched successfully."
                )

            bills = db.query(Bill).filter(Bill.is_deleted.is_(False)).all()

            result = []

            for bill in bills:

                data = model_to_dict(bill)

                total_amount = sum(
                    float(item.amount)
                    for item in bill.bill_items
                    if not item.is_deleted
                )

                data["total_amount"] = total_amount

                result.append(data)

            return ApiResponse.success(
                data=result, message="Bill list fetched successfully."
            )

        except Exception:

            logger.exception("Exception while fetching bill.")

            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )

    @staticmethod
    def save_bill(db: Session, request):
        try:

            vendor = (
                db.query(Vendor)
                .filter(
                    Vendor.vendor_id == request.vendor_id, Vendor.is_deleted.is_(False)
                )
                .first()
            )

            if not vendor:

                return ApiResponse.error(
                    error_message="Vendor not found.", status_code=404
                )

            if request.bill_id:

                bill = (
                    db.query(Bill)
                    .filter(Bill.bill_id == request.bill_id, Bill.is_deleted.is_(False))
                    .first()
                )

                if not bill:

                    return ApiResponse.error(
                        error_message="Bill not found.", status_code=404
                    )

                message = "Bill updated successfully."

            else:

                bill = Bill()

                db.add(bill)

                message = "Bill created successfully."

            bill.vendor_id = request.vendor_id
            bill.bill_date = request.bill_date
            bill.status = request.status

            db.commit()
            db.refresh(bill)

            return ApiResponse.success(data=model_to_dict(bill), message=message)

        except Exception:

            db.rollback()

            logger.exception("Exception while saving bill.")

            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )

    @staticmethod
    def delete_bill(db: Session, bill_id: int):
        try:

            bill = (
                db.query(Bill)
                .filter(Bill.bill_id == bill_id, Bill.is_deleted.is_(False))
                .first()
            )

            if not bill:

                return ApiResponse.error(
                    error_message="Bill not found.", status_code=404
                )

            bill.is_deleted = True

            db.commit()

            return ApiResponse.success(data=None, message="Bill deleted successfully.")

        except Exception:

            db.rollback()

            logger.exception("Exception while deleting bill.")

            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )

    # add inside BillService class

    @staticmethod
    def get_vendor_bill_total(
        db: Session, vendor_id: int, from_date: date, to_date: date
    ):
        try:

            vendor = (
                db.query(Vendor)
                .filter(Vendor.vendor_id == vendor_id, Vendor.is_deleted.is_(False))
                .first()
            )

            if not vendor:
                return ApiResponse.error(
                    error_message="Vendor not found.", status_code=404
                )

            total_amount = (
                db.query(func.coalesce(func.sum(BillItem.amount), 0))
                .join(Bill, Bill.bill_id == BillItem.bill_id)
                .filter(
                    Bill.vendor_id == vendor_id,
                    Bill.bill_date >= from_date,
                    Bill.bill_date <= to_date,
                    Bill.is_deleted.is_(False),
                    BillItem.is_deleted.is_(False),
                )
                .scalar()
            )

            total_bill_count = (
                db.query(Bill)
                .filter(
                    Bill.vendor_id == vendor_id,
                    Bill.bill_date >= from_date,
                    Bill.bill_date <= to_date,
                    Bill.is_deleted.is_(False),
                )
                .count()
            )

            return ApiResponse.success(
                data={
                    "vendor_id": vendor.vendor_id,
                    "vendor_name": vendor.vendor_name,
                    "from_date": str(from_date),
                    "to_date": str(to_date),
                    "total_bill_count": total_bill_count,
                    "total_amount": float(total_amount),
                },
                message="Vendor bill total fetched successfully.",
            )

        except Exception:

            logger.exception("Exception occurred while fetching vendor bill total.")

            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )

    @staticmethod
    def get_bill_pdf_data(db: Session, vendor_id: int, from_date: date, to_date: date):
        try:

            vendor = (
                db.query(Vendor)
                .filter(Vendor.vendor_id == vendor_id, Vendor.is_deleted.is_(False))
                .first()
            )

            if not vendor:
                return ApiResponse.error(
                    error_message="Vendor not found.", status_code=404
                )

            bills = (
                db.query(Bill)
                .filter(
                    Bill.vendor_id == vendor_id,
                    Bill.bill_date >= from_date,
                    Bill.bill_date <= to_date,
                    Bill.is_deleted.is_(False),
                )
                .order_by(Bill.bill_date.asc())
                .all()
            )

            total_amount = 0
            items = []
            sr_no = 1

            for bill in bills:

                for item in bill.bill_items:

                    if item.is_deleted:
                        continue

                    amount = float(item.amount)

                    total_amount += amount

                    items.append(
                        {
                            "sr_no": sr_no,
                            "bill_id": bill.bill_id,
                            "bill_date": bill.bill_date.strftime("%d/%m/%Y"),
                            "description": item.item_description,
                            "quantity": float(item.quantity),
                            "rate": float(item.rate),
                            "amount": amount,
                            "audio_file_url": item.audio_file_url,
                        }
                    )

                    sr_no += 1

            # Prepare data for template rendering
            pdf_data = {
                "vendor_id": vendor.vendor_id,
                "vendor_name": vendor.vendor_name,
                "mobile_number": vendor.mobile_number,
                "shop_name": vendor.shop_name,
                "address": vendor.address,
                "from_date": from_date.strftime("%d/%m/%Y"),
                "to_date": to_date.strftime("%d/%m/%Y"),
                "total_bill_count": len(items),
                "total_amount": total_amount,
                "items": items,
            }

            # Load HTML template (expects Jinja2 placeholders in html/index.html)
            template_path = Path("html") / "index.html"

            if not template_path.exists():
                # Fallback: return data only if template missing
                return ApiResponse.success(
                    data=pdf_data,
                    message="Bill PDF data fetched successfully. (template missing)",
                )

            template_text = template_path.read_text(encoding="utf-8")
            template = Template(template_text)
            rendered_html = template.render(**pdf_data)

            # Ensure output directory exists
            output_dir = Path("storage") / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = (
                f"bill_{vendor.vendor_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            )
            pdf_path = output_dir / filename

            # Convert HTML to PDF using WeasyPrint (cross-platform, no GTK usage here)
            HTML(string=rendered_html, base_url=str(Path.cwd())).write_pdf(
                target=str(pdf_path)
            )

            # Schedule deletion after 1 hour (3600 seconds)
            def _delete_file(path: Path):
                try:
                    if path.exists():
                        path.unlink()
                except Exception:
                    logger.exception("Failed to delete scheduled PDF: %s", str(path))

            timer = threading.Timer(3600, _delete_file, args=(pdf_path,))
            timer.daemon = True
            timer.start()

            return ApiResponse.success(
                data={"pdf_path": str(pdf_path), "expires_in_seconds": 3600},
                message="Bill PDF generated successfully.",
            )

        except Exception:

            logger.exception("Exception while fetching bill pdf data.")

            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )
