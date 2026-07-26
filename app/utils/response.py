from typing import Any, Optional
from fastapi.responses import JSONResponse


class ApiResponse:
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = 200,
    ):
        """
        Success Response

        {
            "success": true,
            "message": "...",
            "errorMessage": null,
            "data": {}
        }
        """

        return JSONResponse(
            status_code=status_code,
            content={
                "success": True,
                "message": message,
                "errorMessage": None,
                "data": data,
            },
        )

    @staticmethod
    def error(
        error_message: str = "Something went wrong.",
        status_code: int = 400,
        data: Optional[Any] = None,
    ):
        """
        Error Response

        {
            "success": false,
            "message": null,
            "errorMessage": "...",
            "data": null
        }
        """

        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": None,
                "errorMessage": error_message,
                "data": data,
            },
        )