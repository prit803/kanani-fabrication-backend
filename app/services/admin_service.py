from app.utils.response import ApiResponse


class AdminService:
    @staticmethod
    def delete_database():
        return ApiResponse.error(
            error_message="Database-file operations are not supported for PostgreSQL.",
            status_code=501,
        )

    @staticmethod
    def upload_database():
        return ApiResponse.error(
            error_message="Database-file operations are not supported for PostgreSQL.",
            status_code=501,
        )
