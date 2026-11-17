import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from sqlalchemy import URL, create_engine, func, select, text
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
_dotenv_settings = dotenv_values(ENV_FILE)
load_dotenv(ENV_FILE)


def _database_url() -> URL:
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        url = make_url(configured_url)
        if url.drivername in {"postgres", "postgresql"}:
            url = url.set(drivername="postgresql+psycopg")
        if (
            url.host
            and url.host.endswith((".supabase.co", ".pooler.supabase.com"))
            and "sslmode" not in url.query
        ):
            url = url.update_query_dict({"sslmode": "require"})
        return url

    def setting(
        environment_names: tuple[str, ...],
        file_names: tuple[str, ...],
    ) -> str | None:
        for name in environment_names:
            value = os.getenv(name)
            if value:
                return value
        for name in file_names:
            value = _dotenv_settings.get(name)
            if value:
                return str(value)
        return None

    host = setting(("PGHOST", "DB_HOST"), ("PGHOST", "DB_HOST", "HOST"))
    port = setting(("PGPORT", "DB_PORT"), ("PGPORT", "DB_PORT", "PORT")) or "5432"
    database = setting(
        ("PGDATABASE", "DB_DATABASE", "DATABASE"),
        ("PGDATABASE", "DB_DATABASE", "DATABASE"),
    )
    username = setting(("PGUSER", "DB_USER"), ("PGUSER", "DB_USER", "USER"))
    password = setting(
        ("PGPASSWORD", "DB_PASSWORD"), ("PGPASSWORD", "DB_PASSWORD", "PASSWORD")
    )
    missing = [
        name
        for name, value in (
            ("HOST", host),
            ("DATABASE", database),
            ("USER", username),
            ("PASSWORD", password),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "PostgreSQL configuration is incomplete. Set DATABASE_URL or the "
            "HOST, PORT, DATABASE, USER, and PASSWORD values in .env or the "
            "deployment environment. "
            f"Missing: {', '.join(missing)}"
        )

    if host is None or database is None or username is None or password is None:
        raise RuntimeError("PostgreSQL configuration is incomplete.")

    query = (
        {"sslmode": "require"}
        if host.endswith((".supabase.co", ".pooler.supabase.com"))
        else {}
    )
    return URL.create(
        "postgresql+psycopg",
        username=username,
        password=password,
        host=host,
        port=int(port),
        database=database,
        query=query,
    )


DATABASE_URL = _database_url()
_engine_options = {"pool_pre_ping": True}
if DATABASE_URL.get_backend_name() == "sqlite":
    _engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_options)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def sync_postgres_sequences(connection: Connection) -> None:
    if connection.dialect.name != "postgresql":
        return

    for table in Base.metadata.sorted_tables:
        primary_key = table.autoincrement_column
        if primary_key is None:
            continue

        sequence = connection.scalar(
            select(func.pg_get_serial_sequence(table.name, primary_key.name))
        )
        if not sequence:
            continue

        maximum_id = connection.scalar(select(func.max(primary_key)))
        sequence_value = max(maximum_id or 0, 1)
        connection.execute(
            text(
                "SELECT setval(CAST(:sequence_name AS regclass), "
                ":sequence_value, :is_called)"
            ),
            {
                "sequence_name": sequence,
                "sequence_value": sequence_value,
                "is_called": maximum_id is not None and maximum_id >= 1,
            },
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
