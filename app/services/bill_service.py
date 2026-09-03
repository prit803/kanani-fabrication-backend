from datetime import date, datetime
import threading
from pathlib import Path

from jinja2 import Template
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bill_item_model import BillItem
from app.models.bill_model import Bill
from app.models.engineering_model import Engineering
from app.models.vendor_model import Vendor
from app.utils.helper import model_to_dict
from app.utils.logger import get_logger
from app.utils.response import ApiResponse

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

                if bill.vendor:
                    data["vendor"] = model_to_dict(bill.vendor)

                if bill.engineer:
                    data["engineer"] = model_to_dict(bill.engineer)

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

                if bill.vendor:
                    data["vendor"] = model_to_dict(bill.vendor)

                if bill.engineer:
                    data["engineer"] = model_to_dict(bill.engineer)

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
            bill.engineer_id = getattr(request, "engineer_id", None) or bill.engineer_id
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
    def get_bill_pdf_data(
        db: Session,
        vendor_id: int,
        from_date: date,
        to_date: date,
        engineer_id: int | None = None,
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

            bills = (
                db.query(Bill)
                .filter(
                    Bill.vendor_id == vendor_id,
                    Bill.bill_date >= from_date,
                    Bill.bill_date <= to_date,
                    Bill.is_deleted.is_(False),
                )
                .order_by(Bill.bill_date.asc(), Bill.bill_id.asc())
            )

            if engineer_id is not None:
                bills = bills.filter(Bill.engineer_id == engineer_id)

            bills = bills.all()

            engineer = None
            if engineer_id is not None:
                engineer = (
                    db.query(Engineering)
                    .filter(
                        Engineering.engineer_id == engineer_id,
                        Engineering.is_deleted.is_(False),
                    )
                    .first()
                )

            if engineer is None:
                for bill in bills:
                    if bill.engineer_id is None:
                        continue
                    engineer = (
                        db.query(Engineering)
                        .filter(
                            Engineering.engineer_id == bill.engineer_id,
                            Engineering.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if engineer is not None:
                        break

            if engineer is None:
                engineer = (
                    db.query(Engineering)
                    .filter(
                        Engineering.name == "કાનાણી", Engineering.is_deleted.is_(False)
                    )
                    .first()
                )

            total_amount = 0
            items = []
            sr_no = 1

            def format_number(value):
                if value is None:
                    return 0
                value = float(value)
                return int(value) if value.is_integer() else value

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
                            "quantity": format_number(item.quantity),
                            "rate": format_number(item.rate),
                            "amount": format_number(amount),
                            "audio_file_url": item.audio_file_url,
                        }
                    )
                    sr_no += 1

            bill_no = "N/A"
            if bills:
                bill_no = str(bills[0].bill_id)

            project_root = Path(__file__).resolve().parents[2]
            sign_image_path = ""
            if engineer and engineer.sign_image:
                stored_sign_image = engineer.sign_image.strip()
                if stored_sign_image.startswith("/storage/"):
                    stored_sign_image = stored_sign_image.lstrip("/")

                sign_image_file = project_root / stored_sign_image
                if sign_image_file.is_file():
                    sign_image_path = sign_image_file.as_uri()

            pdf_data = {
                "vendor_id": vendor.vendor_id,
                "vendor_name": vendor.vendor_name,
                "mobile_number": vendor.mobile_number,
                "shop_name": vendor.shop_name,
                "address": vendor.address,
                "from_date": from_date.strftime("%d/%m/%Y"),
                "to_date": to_date.strftime("%d/%m/%Y"),
                "total_bill_count": len(bills),
                "total_amount": format_number(total_amount),
                "bill_no": bill_no,
                "engineering_name": (
                    engineer.name if engineer else "કાનાણી એન્જિનિયરिंग વર્ક્સ"
                ),
                "engineering_pan_number": engineer.pan_number if engineer else "",
                "engineering_bank_account_number": (
                    engineer.bank_account_number if engineer else ""
                ),
                "engineering_sign_image": sign_image_path,
                "items": items,
            }

            gujarati_digit_translation = str.maketrans("0123456789", "૦૧૨૩૪૫૬૭૮૯")

            gujarati_number_fields = {
                "bill_no",
                "from_date",
                "to_date",
                "sr_no",
                "bill_date",
                "quantity",
                "rate",
                "amount",
                "total_amount",
            }

            def convert_render_numbers(value, key=None):
                if key in {"engineering_sign_image", "audio_file_url"}:
                    return value
                if isinstance(value, dict):
                    return {
                        item_key: convert_render_numbers(item_value, item_key)
                        for item_key, item_value in value.items()
                    }
                if isinstance(value, list):
                    return [convert_render_numbers(item) for item in value]
                if key in gujarati_number_fields and isinstance(
                    value, (int, float, str)
                ):
                    return str(value).translate(gujarati_digit_translation)
                return value

            render_pdf_data = convert_render_numbers(pdf_data)
            api_pdf_data = pdf_data

            template_path = project_root / "html" / "index.html"

            if not template_path.exists():
                return ApiResponse.success(
                    data={**api_pdf_data, "pdf_url": None, "expires_in_seconds": 3600},
                    message="Bill PDF data fetched successfully. (template missing)",
                )

            template_text = template_path.read_text(encoding="utf-8")
            rendered_html = Template(template_text).render(**render_pdf_data)

            output_dir = project_root / "storage" / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = (
                f"bill_{vendor.vendor_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            )
            pdf_path = output_dir / filename
            pdf_url = f"/storage/output/{filename}"

            try:
                from weasyprint import HTML

                HTML(string=rendered_html, base_url=str(project_root)).write_pdf(
                    target=str(pdf_path)
                )
            except Exception as exc:
                logger.warning(
                    "PDF generation unavailable on this system; skipping file creation. %s",
                    str(exc),
                )
                return ApiResponse.success(
                    data={**api_pdf_data, "pdf_url": None, "expires_in_seconds": 0},
                    message="Bill PDF data fetched successfully. PDF generation is unavailable on this system.",
                )

            def _delete_file(path: Path):
                try:
                    if path.exists():
                        path.unlink()
                except Exception:
                    logger.exception("Failed to delete scheduled PDF: %s", str(path))

            timer = threading.Timer(3600, _delete_file, args=(pdf_path,))
            timer.daemon = True
            timer.start()

            response_data = {
                **api_pdf_data,
                "pdf_url": pdf_url,
                "expires_in_seconds": 3600,
            }

            return ApiResponse.success(
                data=response_data,
                message="Bill PDF data fetched successfully.",
            )

        except Exception:

            logger.exception("Exception while fetching bill pdf data.")

            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )
