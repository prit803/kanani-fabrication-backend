import secrets
from typing import Literal

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_cleanup_service import (
    clean_application_data,
    configured_clean_data_key,
)
from app.utils.response import ApiResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


class CleanDataRequest(BaseModel):
    confirmation: Literal["DELETE ALL DATA"]


@router.post("/clean-data")
def clean_data(
    request: CleanDataRequest,
    clean_data_key: str | None = Header(default=None, alias="X-Clean-Data-Key"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    configured_key = configured_clean_data_key()
    if not configured_key:
        return ApiResponse.error(
            error_message="Data cleanup is not configured on this server.",
            status_code=503,
        )
    if clean_data_key is None or not secrets.compare_digest(
        clean_data_key,
        configured_key,
    ):
        return ApiResponse.error(
            error_message="A valid X-Clean-Data-Key header is required.",
            status_code=401,
        )

    return clean_application_data(db)
