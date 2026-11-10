"""Defensive validation and session-scoped saving for uploaded images."""

from __future__ import annotations

import io
import warnings
from pathlib import Path
from typing import Any
from uuid import uuid4

from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from config import Config
from src.utils.exceptions import (
    CorruptImageError,
    PayloadTooLargeError,
    ValidationError,
)
from src.utils.logger import get_logger


logger = get_logger(__name__)


def _stream_size(file_storage: Any) -> int:
    """Measure an upload stream without changing its current position.

    Args:
        file_storage: Uploaded file-like object with a seekable stream.

    Returns:
        The number of bytes in the stream.

    Raises:
        CorruptImageError: If the upload stream cannot be inspected.
    """
    stream = file_storage.stream
    try:
        position = stream.tell()
        stream.seek(0, io.SEEK_END)
        size = stream.tell()
        stream.seek(position)
    except (AttributeError, OSError, ValueError) as error:
        raise CorruptImageError("Unable to inspect the uploaded image stream.") from error
    return size


def _rewind_stream(stream: Any) -> None:
    """Reset an upload stream to the beginning.

    Args:
        stream: Seekable uploaded file stream.

    Raises:
        CorruptImageError: If the stream cannot be reset after inspection.
    """
    try:
        stream.seek(0)
    except (AttributeError, OSError, ValueError) as error:
        raise CorruptImageError("Unable to rewind the uploaded image stream.") from error


def _validate_upload(file_storage: Any) -> None:
    """Validate file metadata, signature, size, and decoded image dimensions.

    Args:
        file_storage: Uploaded file-like object with ``filename`` and ``stream``.

    Raises:
        ValidationError: If the upload is missing or has an unsupported signature.
        PayloadTooLargeError: If its declared or measured size exceeds the limit.
        CorruptImageError: If its image stream is truncated or cannot be decoded.
    """
    filename = getattr(file_storage, "filename", None)
    if not isinstance(filename, str) or not filename.strip():
        raise ValidationError("No file selected.")

    extension = Path(filename).suffix.lower().lstrip(".")
    allowed_extensions = {item.lower().lstrip(".") for item in Config.ALLOWED_EXTENSIONS}
    if extension not in allowed_extensions:
        raise ValidationError("Unsupported file extension.")

    stream = getattr(file_storage, "stream", None)
    if stream is None:
        raise CorruptImageError("Uploaded image has no readable file stream.")

    declared_size = getattr(file_storage, "content_length", None)
    try:
        declared_size = int(declared_size) if declared_size is not None else 0
    except (TypeError, ValueError):
        declared_size = 0
    if declared_size > Config.MAX_CONTENT_LENGTH:
        raise PayloadTooLargeError("File size exceeds the configured upload limit.")

    size = _stream_size(file_storage)
    if size > Config.MAX_CONTENT_LENGTH:
        raise PayloadTooLargeError("File size exceeds the configured upload limit.")
    if size == 0:
        raise ValidationError("Uploaded file is empty.")

    signature_key = "jpeg" if extension in {"jpg", "jpeg"} else "png"
    expected_signature = Config.MAGIC_BYTES[signature_key]
    try:
        stream.seek(0)
        header = stream.read(32)
    except (AttributeError, OSError, ValueError) as error:
        raise CorruptImageError("Unable to read the uploaded image header.") from error
    finally:
        _rewind_stream(stream)

    if not header.startswith(expected_signature):
        raise ValidationError("File extension does not match the image signature.")

    try:
        stream.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(stream) as image:
                width, height = image.size
                if width * height > Config.MAX_IMAGE_PIXELS:
                    raise CorruptImageError("Image dimensions exceed the configured pixel limit.")
                image.load()
    except CorruptImageError:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
        UnidentifiedImageError,
        ValueError,
    ) as error:
        raise CorruptImageError("Uploaded image is corrupt or cannot be decoded.") from error
    finally:
        _rewind_stream(stream)


def validate_upload(file_storage: Any) -> tuple[bool, str]:
    """Validate a JPEG or PNG upload and return its validity and diagnostic.

    Args:
        file_storage: Uploaded file-like object, such as Werkzeug ``FileStorage``.

    Returns:
        A pair containing the validity flag and an empty string on success or a
        human-readable validation error on failure.
    """
    try:
        _validate_upload(file_storage)
    except ValidationError as error:
        logger.warning("Image upload rejected: %s", error)
        return False, str(error)
    return True, ""


def save_upload_securely(file_storage: Any, session_id: str) -> Path:
    """Validate and save an upload under a sanitized, isolated session path.

    Args:
        file_storage: Uploaded file-like object, such as Werkzeug ``FileStorage``.
        session_id: UUID-like identifier for the temporary upload session.

    Returns:
        The path to the saved upload.

    Raises:
        ValidationError: If the upload or session identifier is invalid.
        PayloadTooLargeError: If the upload exceeds the configured size limit.
        CorruptImageError: If the image cannot be safely decoded.
        OSError: If the file cannot be written to the configured upload directory.
    """
    _validate_upload(file_storage)

    safe_session_id = secure_filename(session_id)
    if not safe_session_id or safe_session_id != session_id:
        raise ValidationError("Invalid upload session identifier.")

    original_name = file_storage.filename
    safe_name = secure_filename(original_name)
    if not safe_name:
        raise ValidationError("Filename contains no usable characters.")

    upload_root = Path(Config.UPLOAD_FOLDER).resolve()
    session_directory = upload_root / safe_session_id
    session_directory.mkdir(parents=True, exist_ok=True)
    resolved_session_directory = session_directory.resolve()
    if not resolved_session_directory.is_relative_to(upload_root):
        raise ValidationError("Upload session directory is outside the configured folder.")

    destination = resolved_session_directory / f"{uuid4().hex}_{safe_name}"
    file_storage.stream.seek(0)
    file_storage.save(destination)
    return destination
