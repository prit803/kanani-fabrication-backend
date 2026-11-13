from fastapi import APIRouter
from app.services.admin_service import AdminService

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.delete("/database")
def delete_database():
    return AdminService.delete_database()

@router.post("/database")
def upload_database():
    return AdminService.upload_database()