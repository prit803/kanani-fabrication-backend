import base64
import mimetypes
from pathlib import Path

from fastapi import UploadFile


_SUPPORTED_IMAGE_TYPES = {
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
}


class InvalidImageError(ValueError):
    pass


def image_data_uri_from_bytes(content: bytes, content_type: str) -> str:
    if content_type not in _SUPPORTED_IMAGE_TYPES:
        raise InvalidImageError("Only supported raster image files are allowed.")
    if not content:
        raise InvalidImageError("Image file is empty.")
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def image_data_uri_from_upload(upload: UploadFile) -> str:
    content_type = upload.content_type or ""
    if content_type not in _SUPPORTED_IMAGE_TYPES:
        content_type = mimetypes.guess_type(upload.filename or "")[0] or ""
    return image_data_uri_from_bytes(upload.file.read(), content_type)


def image_data_uri_from_file(path: Path) -> str | None:
    content_type = mimetypes.guess_type(path.name)[0] or ""
    if content_type not in _SUPPORTED_IMAGE_TYPES:
        return None
    content = path.read_bytes()
    if not content:
        return None
    return image_data_uri_from_bytes(content, content_type)
