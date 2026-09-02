from fastapi import FastAPI
from sqlalchemy import inspect, text

from app.database import Base, SessionLocal, engine

from app.models.engineering_model import Engineering
from app.routes.vendor_routes import router as vendor_router
from app.routes.bill_routes import router as bill_router
from app.routes.bill_item_routes import router as bill_item_router
from app.routes.engineering_routes import router as engineering_router
from app.routes.stt_routes import router as stt_router
from app.routes.admin_routes import router as admin_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

Base.metadata.create_all(bind=engine)


def migrate_database_schema():
    inspector = inspect(engine)
    if inspector.has_table("bills"):
        bill_columns = [column["name"] for column in inspector.get_columns("bills")]
        if "engineer_id" not in bill_columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE bills ADD COLUMN engineer_id INTEGER")
                )


migrate_database_schema()


def seed_default_engineers():
    from sqlalchemy.orm import Session

    db: Session = SessionLocal()
    try:
        defaults = ["કાનાણી", "કુમાર"]
        for name in defaults:
            exists = db.query(Engineering).filter(Engineering.name == name).first()
            if not exists:
                db.add(Engineering(name=name))
        db.commit()
    finally:
        db.close()


def migrate_engineering_sign_images():
    from sqlalchemy.orm import Session

    project_root = Path(__file__).resolve().parent.parent
    new_dir = project_root / "storage" / "engineering"
    marker_file = new_dir / ".legacy_sign_image_migration_done"

    if marker_file.exists():
        return

    new_dir.mkdir(parents=True, exist_ok=True)

    db: Session = SessionLocal()
    try:
        engineers = (
            db.query(Engineering).filter(Engineering.is_deleted.is_(False)).all()
        )

        for engineering in engineers:
            old_value = (engineering.sign_image or "").strip()
            if not old_value:
                continue

            if old_value.startswith("/storage/"):
                continue

            old_path = project_root / old_value.lstrip("/")
            new_filename = (
                Path(old_value).name
                if Path(old_value).name
                else f"engineering_{engineering.engineer_id}.png"
            )

            if old_path.exists():
                target_path = new_dir / new_filename
                if not target_path.exists():
                    target_path.write_bytes(old_path.read_bytes())
                engineering.sign_image = f"/storage/engineering/{new_filename}"
            elif old_value.startswith("/app/images/") or old_value.startswith(
                "app/images/"
            ):
                moved_name = Path(old_value).name
                old_file = project_root / "app" / "images" / moved_name
                if old_file.exists():
                    target_path = new_dir / moved_name
                    if not target_path.exists():
                        target_path.write_bytes(old_file.read_bytes())
                    engineering.sign_image = f"/storage/engineering/{moved_name}"

        db.commit()
    finally:
        db.close()

    marker_file.write_text("done", encoding="utf-8")


seed_default_engineers()
migrate_engineering_sign_images()

app = FastAPI(title="Kanani Fabrication Works API")

app.cross_origin_origins = ["*"]  # Allow all origins for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=app.cross_origin_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Kanani Fabrication Works FastAPI Running"}


app.include_router(vendor_router)
app.include_router(bill_router)
app.include_router(bill_item_router)
app.include_router(engineering_router)
app.include_router(stt_router)
# app.include_router(admin_router)

# Mount storage folder so files under `storage/` are served at `/storage`.
# Example: a vendor image stored at `storage/vendors/1.jpg` will be
# accessible at `/storage/vendors/1.jpg`.
project_root = Path(__file__).resolve().parent.parent
storage_dir = project_root / "storage"
storage_dir.mkdir(parents=True, exist_ok=True)

app.mount("/storage", StaticFiles(directory=str(storage_dir)), name="storage")
