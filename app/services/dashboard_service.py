from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.bill_item_model import BillItem
from app.models.bill_model import Bill
from app.models.engineering_model import Engineering
from app.models.vendor_model import Vendor
from app.utils.logger import get_logger
from app.utils.response import ApiResponse

logger = get_logger(__name__)


class DashboardService:
    @staticmethod
    def get_dashboard(
        db: Session,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        try:
            bill_filters = [
                Bill.is_deleted.is_(False),
                Vendor.is_deleted.is_(False),
            ]

            if from_date is not None:
                bill_filters.append(Bill.bill_date >= from_date)
            if to_date is not None:
                bill_filters.append(Bill.bill_date <= to_date)

            bill_query = db.query(Bill).join(Vendor).filter(*bill_filters)

            total_bills = bill_query.count()
            pending_bills = bill_query.filter(Bill.status == "pending").count()
            paid_bills = bill_query.filter(Bill.status == "paid").count()

            amount_query = (
                db.query(
                    Bill.status,
                    func.coalesce(func.sum(BillItem.amount), 0),
                )
                .join(Vendor, Vendor.vendor_id == Bill.vendor_id)
                .outerjoin(
                    BillItem,
                    (BillItem.bill_id == Bill.bill_id)
                    & BillItem.is_deleted.is_(False),
                )
                .filter(*bill_filters)
                .group_by(Bill.status)
            )
            amounts_by_status = {
                status: float(amount or 0) for status, amount in amount_query.all()
            }

            total_amount = sum(amounts_by_status.values())
            pending_amount = amounts_by_status.get("pending", 0.0)
            paid_amount = amounts_by_status.get("paid", 0.0)

            total_vendors = (
                db.query(Vendor)
                .filter(Vendor.is_deleted.is_(False))
                .count()
            )
            total_engineers = (
                db.query(Engineering)
                .filter(Engineering.is_deleted.is_(False))
                .count()
            )

            month_expression = func.strftime("%Y-%m", Bill.bill_date)
            monthly_rows = (
                db.query(
                    month_expression.label("month"),
                    func.count(func.distinct(Bill.bill_id)).label("bill_count"),
                    func.coalesce(func.sum(BillItem.amount), 0).label("total_amount"),
                )
                .join(Vendor, Vendor.vendor_id == Bill.vendor_id)
                .outerjoin(
                    BillItem,
                    (BillItem.bill_id == Bill.bill_id)
                    & BillItem.is_deleted.is_(False),
                )
                .filter(*bill_filters)
                .group_by(month_expression)
                .order_by(month_expression.desc())
                .all()
            )

            top_vendor_rows = (
                db.query(
                    Vendor.vendor_id,
                    Vendor.vendor_name,
                    func.count(func.distinct(Bill.bill_id)).label("bill_count"),
                    func.coalesce(func.sum(BillItem.amount), 0).label("total_amount"),
                )
                .join(Bill, Bill.vendor_id == Vendor.vendor_id)
                .outerjoin(
                    BillItem,
                    (BillItem.bill_id == Bill.bill_id)
                    & BillItem.is_deleted.is_(False),
                )
                .filter(*bill_filters)
                .group_by(Vendor.vendor_id, Vendor.vendor_name)
                .order_by(func.sum(BillItem.amount).desc())
                .limit(5)
                .all()
            )

            recent_bills = (
                bill_query.options(
                    joinedload(Bill.vendor),
                    joinedload(Bill.bill_items),
                )
                .order_by(Bill.bill_date.desc(), Bill.bill_id.desc())
                .limit(5)
                .all()
            )

            data = {
                "summary": {
                    "total_bills": total_bills,
                    "pending_bills": pending_bills,
                    "paid_bills": paid_bills,
                    "total_amount": total_amount,
                    "pending_amount": pending_amount,
                    "paid_amount": paid_amount,
                    "total_vendors": total_vendors,
                    "total_engineers": total_engineers,
                },
                "monthly_summary": [
                    {
                        "month": row.month,
                        "bill_count": row.bill_count,
                        "total_amount": float(row.total_amount or 0),
                    }
                    for row in monthly_rows
                ],
                "top_vendors": [
                    {
                        "vendor_id": row.vendor_id,
                        "vendor_name": row.vendor_name,
                        "bill_count": row.bill_count,
                        "total_amount": float(row.total_amount or 0),
                    }
                    for row in top_vendor_rows
                ],
                "recent_bills": [
                    {
                        "bill_id": bill.bill_id,
                        "bill_date": bill.bill_date.isoformat(),
                        "status": bill.status,
                        "vendor_name": bill.vendor.vendor_name,
                        "total_amount": float(
                            sum(
                                item.amount
                                for item in bill.bill_items
                                if not item.is_deleted
                            )
                            or 0
                        ),
                    }
                    for bill in recent_bills
                ],
            }

            return ApiResponse.success(
                data=data,
                message="Dashboard data fetched successfully.",
            )
        except Exception:
            logger.exception("Exception occurred while fetching dashboard data.")
            return ApiResponse.error(
                error_message="Internal Server Error.", status_code=500
            )
