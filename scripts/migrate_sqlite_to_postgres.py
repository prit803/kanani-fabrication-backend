"""Copy the application's SQLite tables into an empty PostgreSQL database."""

import argparse
import sys
from pathlib import Path

from sqlalchemy import MetaData, Table, URL, create_engine, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import Base, engine, sync_postgres_sequences
from app.models.bill_item_model import BillItem
from app.models.bill_model import Bill
from app.models.engineering_model import Engineering
from app.models.vendor_model import Vendor


MIGRATION_MODELS = (Engineering, Vendor, Bill, BillItem)
TABLE_NAMES = tuple(model.__tablename__ for model in MIGRATION_MODELS)


def migrate_sqlite_to_postgres(source_path: Path, target_engine: Engine) -> dict[str, int]:
    if not source_path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {source_path}")

    source_engine = create_engine(
        URL.create("sqlite", database=str(source_path.resolve()))
    )
    try:
        source_inspector = inspect(source_engine)
        missing_tables = [
            name for name in TABLE_NAMES if not source_inspector.has_table(name)
        ]
        if missing_tables:
            raise RuntimeError(
                "SQLite database is missing required tables: "
                + ", ".join(missing_tables)
            )

        Base.metadata.create_all(target_engine)
        source_metadata = MetaData()
        copied_counts: dict[str, int] = {}

        with source_engine.connect() as source_connection:
            with target_engine.begin() as target_connection:
                target_inspector = inspect(target_connection)
                existing_rows = {
                    name: target_connection.exec_driver_sql(
                        f'SELECT COUNT(*) FROM "{name}"'
                    ).scalar_one()
                    for name in TABLE_NAMES
                    if target_inspector.has_table(name)
                }
                populated_tables = [
                    name for name, count in existing_rows.items() if count
                ]
                if populated_tables:
                    raise RuntimeError(
                        "PostgreSQL migration target must be empty. "
                        "Rows already exist in: " + ", ".join(populated_tables)
                    )

                for table_name in TABLE_NAMES:
                    source_table = Table(
                        table_name,
                        source_metadata,
                        autoload_with=source_engine,
                    )
                    target_table = Base.metadata.tables[table_name]
                    shared_columns = [
                        column.name
                        for column in target_table.columns
                        if column.name in source_table.c
                    ]
                    missing_required = [
                        column.name
                        for column in target_table.columns
                        if not column.nullable
                        and column.default is None
                        and column.server_default is None
                        and not column.autoincrement
                        and column.name not in shared_columns
                    ]
                    if missing_required:
                        raise RuntimeError(
                            f"SQLite table {table_name!r} is missing required "
                            "columns: "
                            + ", ".join(missing_required)
                        )

                    rows = source_connection.execute(
                        select(*(source_table.c[name] for name in shared_columns))
                    )
                    copied = 0
                    while batch := rows.fetchmany(500):
                        target_connection.execute(
                            target_table.insert(),
                            [
                                {
                                    name: row._mapping[name]
                                    for name in shared_columns
                                }
                                for row in batch
                            ],
                        )
                        copied += len(batch)
                    copied_counts[table_name] = copied

                sync_postgres_sequences(target_connection)

        return copied_counts
    finally:
        source_engine.dispose()


def check_target_connection(target_engine: Engine) -> None:
    try:
        with target_engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except OperationalError as exc:
        original_error = str(exc.orig).lower()
        if "resolve host" in original_error or "getaddrinfo failed" in original_error:
            raise RuntimeError(
                "The PostgreSQL hostname could not be resolved. Verify that the "
                "Supabase project is active and copy its exact database host from "
                "the dashboard's Connect settings. Supabase direct database "
                "endpoints use IPv6 unless the project has the IPv4 add-on; on an "
                "IPv4-only network, select Session Pooler and copy its host, port, "
                "and username from Connect. Also check the computer's DNS, VPN, "
                "and network access. No migration data was written."
            ) from exc
        raise RuntimeError(
            "Could not connect to PostgreSQL. Verify the database host, port, "
            "credentials, SSL settings, and network access. No migration data "
            "was written."
        ) from exc


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy kanani.db into an empty configured PostgreSQL database"
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=PROJECT_ROOT / "kanani.db",
        help="Path to the SQLite database (default: kanani.db)",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm that the configured PostgreSQL database is the intended target",
    )
    args = parser.parse_args()
    if not args.confirm:
        parser.error("migration writes to PostgreSQL; pass --confirm to proceed")
    if engine.dialect.name != "postgresql":
        parser.error("the configured DATABASE_URL must point to PostgreSQL")

    try:
        check_target_connection(engine)
    except RuntimeError as exc:
        parser.exit(status=1, message=f"Error: {exc}\n")

    copied_counts = migrate_sqlite_to_postgres(args.source, engine)
    for table_name, count in copied_counts.items():
        print(f"{table_name}: copied {count} rows")
    print("SQLite data migration completed.")


if __name__ == "__main__":
    main()
