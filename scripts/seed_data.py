"""Seed the configured database with engineering, vendor, bill, and bill-item data.

Usage:
    python scripts/seed_data.py

This script resets the database tables, resets generated ID sequences, and
re-inserts the default seed records required by the app.
"""

import argparse
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal, engine, sync_postgres_sequences
from app.models.bill_item_model import BillItem
from app.models.bill_model import Bill
from app.models.engineering_model import Engineering
from app.models.vendor_model import Vendor

ENGINEERING = [
    {
        "engineer_id": 0,
        "name": "કાનાણી",
        "pan_number": "ABCDE1234F",
        "bank_account_number": "1234567890123456",
    },
    {
        "engineer_id": 1,
        "name": "કુમાર",
        "pan_number": "FGHIJ5678K",
        "bank_account_number": "6543210987654321",
    },
]

VENDORS = [
    {
        "vendor_id": 0,
        "vendor_name": "Rameshbhai Patel",
        "mobile_number": "9876543210",
        "shop_name": "Shree Ram Fabrication Works",
        "address": "GIDC Phase 1, Vatva, Ahmedabad, Gujarat",
        "status": "active",
    },
    {
        "vendor_id": 1,
        "vendor_name": "Maheshbhai Solanki",
        "mobile_number": "9825012345",
        "shop_name": "Om Steel Fabrication",
        "address": "Naroda GIDC, Ahmedabad, Gujarat",
        "status": "active",
    },
    {
        "vendor_id": 2,
        "vendor_name": "Jigneshbhai Chauhan",
        "mobile_number": "9909123456",
        "shop_name": "Jay Ambe Engineering & Fabrication",
        "address": "Makarpura GIDC, Vadodara, Gujarat",
        "status": "active",
    },
]

BILLS = [
    {
        "bill_id": 0,
        "vendor_id": 0,
        "bill_date": "2026-08-07",
        "status": "pending",
        "engineer_id": 0,
    },
    {
        "bill_id": 1,
        "vendor_id": 1,
        "bill_date": "2026-08-07",
        "status": "pending",
        "engineer_id": 0,
    },
    {
        "bill_id": 2,
        "vendor_id": 2,
        "bill_date": "2026-08-07",
        "status": "pending",
        "engineer_id": 0,
    },
]


def build_bill_items(bill_id, item_count, item_prefix):
    return [
        {
            "bill_id": bill_id,
            "item_description": f"{item_prefix} {item_number}",
            "quantity": item_number,
            "rate": 100 * item_number,
            "audio_file_url": "",
        }
        for item_number in range(1, item_count + 1)
    ]


BILL_ITEMS = (
    build_bill_items(0, 15, "એમએસ ફેબ્રિકેશન આઇટમ")
    + build_bill_items(1, 9, "વેલ્ડિંગ અને કટિંગ આઇટમ")
    + build_bill_items(2, 2, "મજૂરી આઇટમ")
)


def reset_database(db):
    for model in (BillItem, Bill, Vendor, Engineering):
        db.query(model).delete(synchronize_session=False)


def seed_engineering(db):
    db.add_all(
        [
            Engineering(
                engineer_id=item["engineer_id"],
                name=item["name"],
                pan_number=item.get("pan_number"),
                bank_account_number=item.get("bank_account_number"),
                is_deleted=False,
            )
            for item in ENGINEERING
        ]
    )
    print(f"Inserted engineering rows: {len(ENGINEERING)}")


def seed_vendors(db):
    db.add_all(
        [
            Vendor(
                vendor_id=vendor["vendor_id"],
                vendor_name=vendor["vendor_name"],
                mobile_number=vendor["mobile_number"],
                shop_name=vendor.get("shop_name"),
                address=vendor.get("address"),
                status=vendor.get("status", "active"),
                is_deleted=False,
            )
            for vendor in VENDORS
        ]
    )
    print(f"Inserted vendor rows: {len(VENDORS)}")


def seed_bills(db):
    db.add_all(
        [
            Bill(
                bill_id=bill["bill_id"],
                vendor_id=bill["vendor_id"],
                engineer_id=bill["engineer_id"],
                bill_date=date.fromisoformat(bill["bill_date"]),
                status=bill["status"],
                is_deleted=False,
            )
            for bill in BILLS
        ]
    )
    print(f"Inserted bill rows: {len(BILLS)}")


def seed_bill_items(db):
    inserted = 0
    grouped = defaultdict(list)
    for item in BILL_ITEMS:
        grouped[item["bill_id"]].append(item)

    for bill_id, items in sorted(grouped.items()):
        for item in items:
            amount = Decimal(str(item["quantity"])) * Decimal(str(item["rate"]))
            db.add(
                BillItem(
                    bill_item_id=inserted,
                    bill_id=bill_id,
                    item_description=item["item_description"],
                    quantity=Decimal(str(item["quantity"])),
                    rate=Decimal(str(item["rate"])),
                    amount=amount,
                    audio_file_url=item.get("audio_file_url") or None,
                    is_deleted=False,
                )
            )
            inserted += 1
    print(f"Inserted bill item rows: {inserted}")


def main():
    parser = argparse.ArgumentParser(
        description="Reset and seed the database configured in .env"
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Skip clearing the database before seeding",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if not args.no_reset:
            reset_database(db)

        seed_engineering(db)
        seed_vendors(db)
        seed_bills(db)
        seed_bill_items(db)
        db.commit()
        if not args.no_reset:
            print("Configured database tables cleaned.")
        with engine.begin() as connection:
            sync_postgres_sequences(connection)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"Seed completed successfully using {engine.dialect.name}.")


if __name__ == "__main__":
    main()
