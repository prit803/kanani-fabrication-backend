import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("DATABASE_URL", "sqlite://")

from sqlalchemy import URL, create_engine, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, _database_url
from app.models.bill_item_model import BillItem
from app.models.bill_model import Bill
from app.models.engineering_model import Engineering
from app.models.vendor_model import Vendor
from scripts.migrate_sqlite_to_postgres import (
    check_target_connection,
    migrate_sqlite_to_postgres,
)
from scripts.seed_kumar_sample_data import seed_kumar_sample_data


class DatabaseMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_path = Path(self.temp_dir.name) / "source.db"
        self.source_engine = create_engine(
            URL.create("sqlite", database=str(self.source_path))
        )
        Base.metadata.create_all(bind=self.source_engine)
        with Session(self.source_engine) as db:
            db.add_all(
                [
                    Engineering(engineer_id=0, name="Engineer", is_deleted=False),
                    Vendor(
                        vendor_id=1,
                        vendor_name="Vendor",
                        mobile_number="1234567890",
                        status="active",
                        is_deleted=False,
                    ),
                ]
            )
            db.add(
                Bill(
                    bill_id=0,
                    vendor_id=1,
                    engineer_id=0,
                    bill_date=date(2026, 8, 7),
                    status="pending",
                    is_deleted=False,
                )
            )
            db.add(
                BillItem(
                    bill_item_id=0,
                    bill_id=0,
                    item_description="Fabrication",
                    quantity=Decimal("2"),
                    rate=Decimal("150"),
                    amount=Decimal("300"),
                    is_deleted=False,
                )
            )
            db.commit()

        self.target_engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    def tearDown(self):
        self.target_engine.dispose()
        self.source_engine.dispose()
        self.temp_dir.cleanup()

    def test_copies_data_and_preserves_relationships_and_ids(self):
        copied_counts = migrate_sqlite_to_postgres(
            self.source_path,
            self.target_engine,
        )

        self.assertEqual(
            copied_counts,
            {"engineering": 1, "vendors": 1, "bills": 1, "bill_items": 1},
        )
        with Session(self.target_engine) as db:
            item = db.scalar(select(BillItem).where(BillItem.bill_item_id == 0))
            self.assertIsNotNone(item)
            self.assertEqual(item.bill_id, 0)
            self.assertEqual(item.amount, Decimal("300.00"))
            self.assertEqual(item.bill.vendor.vendor_name, "Vendor")

    def test_refuses_a_populated_target_without_modifying_it(self):
        Base.metadata.create_all(bind=self.target_engine)
        with Session(self.target_engine) as db:
            db.add(
                Vendor(
                    vendor_id=9,
                    vendor_name="Existing",
                    mobile_number="0000000000",
                    status="active",
                    is_deleted=False,
                )
            )
            db.commit()

        with self.assertRaisesRegex(RuntimeError, "must be empty"):
            migrate_sqlite_to_postgres(self.source_path, self.target_engine)

        with Session(self.target_engine) as db:
            vendors = db.scalars(select(Vendor)).all()
            self.assertEqual([vendor.vendor_name for vendor in vendors], ["Existing"])
            self.assertEqual(db.scalars(select(Bill)).all(), [])

    def test_dns_failure_has_actionable_error_without_connection_traceback(self):
        target_engine = Mock()
        target_engine.connect.side_effect = OperationalError(
            "SELECT 1",
            {},
            OSError("failed to resolve host: getaddrinfo failed"),
        )

        with self.assertRaisesRegex(
            RuntimeError, "Supabase project is active.*No migration data was written"
        ):
            check_target_connection(target_engine)

    def test_pooler_database_url_enables_ssl(self):
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": (
                    "postgresql://postgres.project-ref:secret@"
                    "aws-0-region.pooler.supabase.com:5432/postgres"
                )
            },
        ):
            database_url = _database_url()

        self.assertEqual(database_url.drivername, "postgresql+psycopg")
        self.assertEqual(database_url.query["sslmode"], "require")

    def test_bill_status_enum_compiles_for_postgresql(self):
        bill_status_type = Bill.__table__.c.status.type
        self.assertEqual(bill_status_type.name, "bill_status")
        self.assertIn(
            "bill_status",
            str(bill_status_type.compile(dialect=postgresql.dialect())),
        )

    def test_kumar_sample_seed_creates_three_vendors_fifteen_bills_and_is_idempotent(self):
        Base.metadata.create_all(bind=self.target_engine)
        with Session(self.target_engine) as db:
            db.add(Engineering(engineer_id=1, name="કુમાર", is_deleted=False))
            db.commit()
        session_factory = sessionmaker(
            bind=self.target_engine,
            expire_on_commit=False,
        )

        totals = seed_kumar_sample_data(session_factory, self.target_engine)

        self.assertEqual(
            totals,
            {
                "vendors_created": 3,
                "bills_created": 15,
                "bill_items_created": 130,
            },
        )
        with Session(self.target_engine) as db:
            self.assertEqual(db.query(Vendor).count(), 3)
            self.assertEqual(db.query(Bill).count(), 15)
            self.assertEqual(db.query(BillItem).count(), 130)
            self.assertEqual(
                db.query(Bill.engineer_id, Bill.vendor_id)
                .group_by(Bill.engineer_id, Bill.vendor_id)
                .count(),
                3,
            )
            for vendor in db.scalars(select(Vendor)).all():
                self.assertEqual(
                    db.query(Bill)
                    .filter(
                        Bill.vendor_id == vendor.vendor_id,
                        Bill.engineer_id == 1,
                    )
                    .count(),
                    5,
                )

        repeated_totals = seed_kumar_sample_data(
            session_factory,
            self.target_engine,
        )
        self.assertEqual(
            repeated_totals,
            {"vendors_created": 0, "bills_created": 0, "bill_items_created": 0},
        )

    def test_kumar_sample_seed_rolls_back_if_existing_bills_conflict(self):
        Base.metadata.create_all(bind=self.target_engine)
        with Session(self.target_engine) as db:
            db.add_all(
                [
                    Engineering(engineer_id=1, name="કુમાર", is_deleted=False),
                    Vendor(
                        vendor_name="Rameshbhai Patel",
                        mobile_number="9876543210",
                        status="active",
                        is_deleted=False,
                    ),
                ]
            )
            db.flush()
            db.add(
                Bill(
                    vendor_id=1,
                    engineer_id=1,
                    bill_date=date(2026, 8, 7),
                    status="pending",
                    is_deleted=False,
                )
            )
            db.commit()

        session_factory = sessionmaker(
            bind=self.target_engine,
            expire_on_commit=False,
        )
        with self.assertRaisesRegex(RuntimeError, "already has 1 active Kumar bill"):
            seed_kumar_sample_data(session_factory, self.target_engine)

        with Session(self.target_engine) as db:
            self.assertEqual(db.query(Vendor).count(), 1)
            self.assertEqual(db.query(Bill).count(), 1)
            self.assertEqual(db.query(BillItem).count(), 0)


if __name__ == "__main__":
    unittest.main()
