"""Seed the local SQLite database with clean engineering, vendor, bill, and bill-item data.

Usage:
    python scripts/seed_data.py

This script resets the database tables, clears SQLite AUTOINCREMENT counters, and
re-inserts the default seed records required by the app.
"""

import argparse
import sqlite3
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "kanani.db"


def reset_database():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        for table in ["bill_items", "bills", "engineering", "vendors"]:
            connection.execute(f"DELETE FROM {table}")
            sequence_exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'sqlite_sequence'"
            ).fetchone()
            if sequence_exists:
                connection.execute(
                    "DELETE FROM sqlite_sequence WHERE name = ?",
                    (table,),
                )
        connection.execute("PRAGMA foreign_keys = ON")
        connection.commit()

    print(f"Database cleaned and indexes reset: {DB_PATH}")


def seed_engineering(db):
    for item in ENGINEERING:
        db.execute(
            "INSERT INTO engineering (engineer_id, name, pan_number, bank_account_number, is_deleted) VALUES (?, ?, ?, ?, 0)",
            (
                item["engineer_id"],
                item["name"],
                item.get("pan_number"),
                item.get("bank_account_number"),
            ),
        )
    db.commit()
    print(f"Inserted engineering rows: {len(ENGINEERING)}")


def seed_vendors(db):
    for vendor in VENDORS:
        db.execute(
            "INSERT INTO vendors (vendor_id, vendor_name, mobile_number, shop_name, address, status, is_deleted) VALUES (?, ?, ?, ?, ?, ?, 0)",
            (
                vendor["vendor_id"],
                vendor["vendor_name"],
                vendor["mobile_number"],
                vendor.get("shop_name"),
                vendor.get("address"),
                vendor.get("status", "active"),
            ),
        )
    db.commit()
    print(f"Inserted vendor rows: {len(VENDORS)}")


def seed_bills(db):
    for bill in BILLS:
        db.execute(
            "INSERT INTO bills (bill_id, vendor_id, engineer_id, bill_date, status, is_deleted) VALUES (?, ?, ?, ?, ?, 0)",
            (
                bill["bill_id"],
                bill["vendor_id"],
                bill["engineer_id"],
                bill["bill_date"],
                bill["status"],
            ),
        )
    db.commit()
    print(f"Inserted bill rows: {len(BILLS)}")


def seed_bill_items(db):
    inserted = 0
    grouped = defaultdict(list)
    for item in BILL_ITEMS:
        grouped[item["bill_id"]].append(item)

    for bill_id, items in sorted(grouped.items()):
        for item in items:
            amount = Decimal(str(item["quantity"])) * Decimal(str(item["rate"]))
            db.execute(
                "INSERT INTO bill_items (bill_item_id, bill_id, item_description, quantity, rate, amount, audio_file_url, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
                (
                    inserted,
                    bill_id,
                    item["item_description"],
                    float(item["quantity"]),
                    float(item["rate"]),
                    float(amount),
                    item.get("audio_file_url") or None,
                ),
            )
            inserted += 1
    db.commit()
    print(f"Inserted bill item rows: {inserted}")


def main():
    parser = argparse.ArgumentParser(description="Reset and seed local SQLite database")
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Skip clearing the database before seeding",
    )
    args = parser.parse_args()

    if not args.no_reset:
        reset_database()

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        seed_engineering(connection)
        seed_vendors(connection)
        seed_bills(connection)
        seed_bill_items(connection)

    print("Seed completed successfully.")


if __name__ == "__main__":
    main()
