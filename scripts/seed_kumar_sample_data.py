"""Add the three sample vendors and five sample bills each, assigned to Kumar."""

import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import SessionLocal, engine, sync_postgres_sequences
from app.models.bill_item_model import BillItem
from app.models.bill_model import Bill
from app.models.engineering_model import Engineering
from app.models.vendor_model import Vendor
from scripts.seed_data import BILL_ITEMS, BILLS, VENDORS

BILLS_PER_VENDOR = 5
KUMAR_ENGINEER_ID = 1


def _item_signature(items):
    return sorted(
        (
            item.item_description,
            Decimal(str(item.quantity)),
            Decimal(str(item.rate)),
            Decimal(str(item.amount)),
        )
        for item in items
    )


def seed_kumar_sample_data(
    session_factory: sessionmaker[Session], target_engine: Engine
) -> dict[str, int]:
    seeded_items_by_bill = defaultdict(list)
    for item in BILL_ITEMS:
        seeded_items_by_bill[item["bill_id"]].append(item)

    totals = {"vendors_created": 0, "bills_created": 0, "bill_items_created": 0}

    with session_factory.begin() as db:
        engineer = db.get(Engineering, KUMAR_ENGINEER_ID)
        if engineer is None or engineer.is_deleted:
            raise RuntimeError(
                "Active Kumar engineer (engineer_id=1) was not found. "
                "No sample data was written."
            )

        for vendor_data, seed_bill in zip(VENDORS, BILLS, strict=True):
            matching_vendors = db.scalars(
                select(Vendor).where(
                    Vendor.vendor_name == vendor_data["vendor_name"]
                )
            ).all()
            if len(matching_vendors) > 1:
                raise RuntimeError(
                    f"Multiple vendors named {vendor_data['vendor_name']!r} exist. "
                    "Resolve duplicates before seeding."
                )

            if matching_vendors:
                vendor = matching_vendors[0]
                if vendor.is_deleted:
                    raise RuntimeError(
                        f"Sample vendor {vendor.vendor_name!r} is deleted. "
                        "Restore it before seeding."
                    )
            else:
                vendor = Vendor(
                    vendor_name=vendor_data["vendor_name"],
                    mobile_number=vendor_data["mobile_number"],
                    shop_name=vendor_data.get("shop_name"),
                    address=vendor_data.get("address"),
                    status=vendor_data.get("status", "active"),
                    is_deleted=False,
                )
                db.add(vendor)
                db.flush()
                totals["vendors_created"] += 1

            existing_bills = db.scalars(
                select(Bill).where(
                    Bill.vendor_id == vendor.vendor_id,
                    Bill.engineer_id == KUMAR_ENGINEER_ID,
                    Bill.is_deleted.is_(False),
                )
            ).all()

            seeded_items = seeded_items_by_bill[seed_bill["bill_id"]]
            expected_item_signature = sorted(
                (
                    item["item_description"],
                    Decimal(str(item["quantity"])),
                    Decimal(str(item["rate"])),
                    Decimal(str(item["quantity"])) * Decimal(str(item["rate"])),
                )
                for item in seeded_items
            )

            if len(existing_bills) == BILLS_PER_VENDOR:
                if all(
                    bill.bill_date == date.fromisoformat(seed_bill["bill_date"])
                    and bill.status == seed_bill["status"]
                    and _item_signature(
                        db.scalars(
                            select(BillItem).where(
                                BillItem.bill_id == bill.bill_id,
                                BillItem.is_deleted.is_(False),
                            )
                        ).all()
                    )
                    == expected_item_signature
                    for bill in existing_bills
                ):
                    continue
                raise RuntimeError(
                    f"Existing Kumar bills for {vendor.vendor_name!r} do not "
                    "match the sample seed. No sample data was written."
                )

            if existing_bills:
                raise RuntimeError(
                    f"{vendor.vendor_name!r} already has "
                    f"{len(existing_bills)} active Kumar bill(s). Expected none "
                    f"or {BILLS_PER_VENDOR} matching sample bills; no sample data "
                    "was written."
                )

            for _ in range(BILLS_PER_VENDOR):
                bill = Bill(
                    vendor_id=vendor.vendor_id,
                    engineer_id=KUMAR_ENGINEER_ID,
                    bill_date=date.fromisoformat(seed_bill["bill_date"]),
                    status=seed_bill["status"],
                    is_deleted=False,
                )
                db.add(bill)
                db.flush()

                db.add_all(
                    [
                        BillItem(
                            bill_id=bill.bill_id,
                            item_description=item["item_description"],
                            quantity=Decimal(str(item["quantity"])),
                            rate=Decimal(str(item["rate"])),
                            amount=(
                                Decimal(str(item["quantity"]))
                                * Decimal(str(item["rate"]))
                            ),
                            audio_file_url=item.get("audio_file_url") or None,
                            is_deleted=False,
                        )
                        for item in seeded_items
                    ]
                )
                totals["bills_created"] += 1
                totals["bill_items_created"] += len(seeded_items)

    with target_engine.begin() as connection:
        sync_postgres_sequences(connection)

    return totals


def main() -> None:
    totals = seed_kumar_sample_data(SessionLocal, engine)
    for name, count in totals.items():
        print(f"{name.replace('_', ' ')}: {count}")
    print(f"Sample data ready using {engine.dialect.name}.")


if __name__ == "__main__":
    main()
