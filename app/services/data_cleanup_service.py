import os
from pathlib import Path

from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import sync_postgres_sequences
from app.models.bill_item_model import BillItem
from app.models.bill_model import Bill
from app.models.engineering_model import Engineering
from app.models.vendor_model import Vendor
from app.utils.logger import get_logger
from app.utils.response import ApiResponse

logger = get_logger(__name__)
STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage"
DATA_MODELS = (BillItem, Bill, Vendor, Engineering)


def _is_link_or_junction(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", None)
    return path.is_symlink() or (is_junction is not None and is_junction())


def _delete_storage_files(storage_dir: Path) -> int:
    if not storage_dir.exists():
        return 0
    if _is_link_or_junction(storage_dir):
        raise OSError("Refusing to delete files through a storage directory link.")

    deleted_files = 0
    for current_root, directories, filenames in os.walk(storage_dir, followlinks=False):
        directories[:] = [
            name
            for name in directories
            if not _is_link_or_junction(Path(current_root) / name)
        ]
        for filename in filenames:
            file_path = Path(current_root) / filename
            if _is_link_or_junction(file_path) or not file_path.is_file():
                continue
            file_path.unlink()
            deleted_files += 1
    return deleted_files


def clean_application_data(db: Session) -> JSONResponse:
    try:
        with db.begin():
            deleted_rows = {
                model.__tablename__: int(
                    db.query(model).delete(synchronize_session=False) or 0
                )
                for model in DATA_MODELS
            }
            if db.bind is not None:
                sync_postgres_sequences(db.connection())
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to clear application database tables.")
        return ApiResponse.error(
            error_message="Database cleanup failed. No storage files were removed.",
            status_code=500,
        )

    try:
        deleted_files = _delete_storage_files(STORAGE_DIR)
    except OSError:
        logger.exception(
            "Database cleanup completed, but some storage files could not be removed."
        )
        return ApiResponse.error(
            error_message=(
                "Database rows were erased, but storage-file cleanup failed. "
                "Check the server file permissions and retry."
            ),
            status_code=500,
            data={"deleted_rows": deleted_rows},
        )

    return ApiResponse.success(
        data={"deleted_rows": deleted_rows, "deleted_files": deleted_files},
        message="Application database data and storage files were erased.",
    )


def configured_clean_data_key() -> str | None:
    return os.getenv("CLEAN_DATA_API_KEY")
