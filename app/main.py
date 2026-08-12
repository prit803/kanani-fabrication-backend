from fastapi import FastAPI

from app.database import Base, engine

from app.routes.vendor_routes import router as vendor_router
from app.routes.bill_routes import router as bill_router
from app.routes.bill_item_routes import router as bill_item_router
from app.routes.stt_routes import router as stt_router
from app.routes.admin_routes import router as admin_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

Base.metadata.create_all(bind=engine)

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
app.include_router(stt_router)
# app.include_router(admin_router)

# Mount storage folder so files under `storage/` are served at `/storage`.
# Example: a vendor image stored at `storage/vendors/1.jpg` will be
# accessible at `/storage/vendors/1.jpg`.
project_root = Path(__file__).resolve().parent.parent
storage_dir = project_root / "storage"
storage_dir.mkdir(parents=True, exist_ok=True)

app.mount("/storage", StaticFiles(directory=str(storage_dir)), name="storage")
