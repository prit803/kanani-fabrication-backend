from fastapi import FastAPI
from sqlalchemy import inspect, text

from app.database import Base, SessionLocal, engine

from app.models.engineering_model import Engineering
from app.models.vendor_model import Vendor
from app.routes.vendor_routes import router as vendor_router
from app.routes.bill_routes import router as bill_router
from app.routes.bill_item_routes import router as bill_item_router
from app.routes.engineering_routes import router as engineering_router
from app.routes.stt_routes import router as stt_router
from app.routes.gujarati_stt_routes import router as gujarati_stt_router
from app.routes.admin_routes import router as admin_router
from app.routes.data_admin_routes import router as data_admin_router
from app.routes.dashboard_routes import router as dashboard_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.utils.media import image_data_uri_from_file

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
    if inspector.has_table("engineering") and engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE engineering ALTER COLUMN sign_image TYPE TEXT")
            )


migrate_database_schema()


def seed_default_engineers():
    from sqlalchemy.orm import Session

    db: Session = SessionLocal()
    try:
        defaults = {0: "કાનાણી", 1: "કુમાર"}
        for engineer_id, name in defaults.items():
            engineer = db.get(Engineering, engineer_id)
            if engineer is None:
                db.add(Engineering(engineer_id=engineer_id, name=name))
        db.commit()
    finally:
        db.close()


def migrate_legacy_image_data():
    from sqlalchemy.orm import Session

    project_root = Path(__file__).resolve().parent.parent

    db: Session = SessionLocal()
    try:
        changed = False
        for model, column_name in (
            (Engineering, "sign_image"),
            (Vendor, "photo_url"),
        ):
            for record in db.query(model).all():
                old_value = (getattr(record, column_name) or "").strip()
                if not old_value or old_value.startswith("data:image/"):
                    continue

                if old_value.startswith("/storage/"):
                    relative_path = old_value.lstrip("/")
                elif old_value.startswith(("/app/images/", "app/images/")):
                    relative_path = old_value.lstrip("/")
                elif old_value.startswith("storage/"):
                    relative_path = old_value
                else:
                    continue

                image_path = (project_root / relative_path).resolve()
                if (
                    project_root.resolve() not in image_path.parents
                    or not image_path.is_file()
                ):
                    continue
                data_uri = image_data_uri_from_file(image_path)
                if data_uri:
                    setattr(record, column_name, data_uri)
                    changed = True

        if changed:
            db.commit()
    finally:
        db.close()


seed_default_engineers()
migrate_legacy_image_data()

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


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(vendor_router)
app.include_router(bill_router)
app.include_router(bill_item_router)
app.include_router(engineering_router)
app.include_router(stt_router)
app.include_router(gujarati_stt_router)
app.include_router(dashboard_router)
app.include_router(data_admin_router)
# app.include_router(admin_router)

# Mount storage folder so files under `storage/` are served at `/storage`.
# Example: a vendor image stored at `storage/vendors/1.jpg` will be
# accessible at `/storage/vendors/1.jpg`.
project_root = Path(__file__).resolve().parent.parent
storage_dir = project_root / "storage"
storage_dir.mkdir(parents=True, exist_ok=True)

app.mount("/storage", StaticFiles(directory=str(storage_dir)), name="storage")
