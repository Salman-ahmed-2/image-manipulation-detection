"""Unit tests for secure file validation and shared image utilities."""

from __future__ import annotations

import io
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage

from config import Config
from src.utils.exceptions import (
    AppError,
    CorruptImageError,
    ModelInferenceError,
    ModelNotLoadedError,
    PayloadTooLargeError,
    ReportGenerationError,
    ValidationError,
)
from src.utils.file_validator import (
    cleanup_session_directory,
    save_upload_securely,
    validate_upload,
)
from src.utils.image_utils import bytes_to_pil, ensure_rgb, pil_to_bytes
from src.utils.logger import get_logger


def _image_bytes(image_format: str, mode: str = "RGB") -> bytes:
    """Create a small synthetic image in memory.

    Args:
        image_format: Pillow format used to encode the image.
        mode: Image mode to construct.

    Returns:
        Encoded image data.
    """
    image = Image.new(mode, (12, 10), color=0 if mode == "L" else (20, 80, 140))
    buffer = io.BytesIO()
    image.save(buffer, format=image_format)
    return buffer.getvalue()


def _upload(content: bytes, filename: str) -> FileStorage:
    """Wrap in-memory bytes as an uploaded file.

    Args:
        content: Upload content.
        filename: Client-provided upload filename.

    Returns:
        Werkzeug file storage positioned at the start of the stream.
    """
    return FileStorage(stream=io.BytesIO(content), filename=filename)


@pytest.mark.parametrize(
    ("image_format", "filename"),
    [("JPEG", "photo.jpg"), ("JPEG", "photo.jpeg"), ("PNG", "photo.png")],
)
def test_validate_upload_accepts_supported_images(image_format: str, filename: str) -> None:
    """Accept real JPEG and PNG signatures when the extension matches."""
    upload = _upload(_image_bytes(image_format), filename)

    assert validate_upload(upload) == (True, "")
    assert upload.stream.tell() == 0


@pytest.mark.parametrize("filename", ["document.pdf", "program.exe"])
def test_validate_upload_rejects_unsupported_extensions(filename: str) -> None:
    """Reject non-image extensions before attempting image decoding."""
    assert validate_upload(_upload(b"not an image", filename))[0] is False


def test_validate_upload_rejects_empty_file() -> None:
    """Reject empty uploads with a useful diagnostic."""
    valid, message = validate_upload(_upload(b"", "empty.jpg"))

    assert valid is False
    assert "empty" in message.lower()


def test_validate_upload_rejects_oversized_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject files larger than the configured maximum without decoding them."""
    monkeypatch.setattr(Config, "MAX_CONTENT_LENGTH", 64)
    upload = _upload(_image_bytes("JPEG") + b"x" * 65, "large.jpg")

    valid, message = validate_upload(upload)

    assert valid is False
    assert "size" in message.lower() or "limit" in message.lower()


@pytest.mark.parametrize(
    ("content", "filename"),
    [(_image_bytes("PNG"), "spoofed.jpg"), (_image_bytes("JPEG"), "spoofed.png")],
)
def test_validate_upload_rejects_spoofed_extensions(content: bytes, filename: str) -> None:
    """Reject image data whose magic bytes disagree with the filename extension."""
    valid, message = validate_upload(_upload(content, filename))

    assert valid is False
    assert "signature" in message.lower()


def test_validate_upload_rejects_corrupt_image_stream() -> None:
    """Reject matching image signatures when Pillow cannot decode the payload."""
    valid, message = validate_upload(_upload(b"\xff\xd8\xff" + b"bad data", "bad.jpg"))

    assert valid is False
    assert "corrupt" in message.lower() or "decode" in message.lower()


def test_save_upload_sanitizes_filename_and_uses_unique_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Save valid files under a session folder using sanitized unique names."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    content = _image_bytes("JPEG")
    session_id = str(uuid4())
    first = save_upload_securely(_upload(content, "../../unsafe image.jpg"), session_id)
    second = save_upload_securely(_upload(content, "../../unsafe image.jpg"), session_id)

    assert first.parent == tmp_path.resolve() / session_id
    assert first.is_file()
    assert first.read_bytes() == content
    assert first.name.endswith("_unsafe_image.jpg")
    assert second != first


def test_save_upload_rejects_unsafe_session_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not allow a session identifier to escape the configured upload folder."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)

    with pytest.raises(ValidationError, match="session"):
        save_upload_securely(_upload(_image_bytes("PNG"), "image.png"), "../outside")


def test_cleanup_session_directory_removes_only_the_requested_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Remove the requested session's files without touching neighboring sessions."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    session_directory = tmp_path / "session-1"
    other_session_directory = tmp_path / "session-2"
    session_directory.mkdir()
    other_session_directory.mkdir()
    (session_directory / "upload.jpg").write_bytes(b"synthetic image")
    (other_session_directory / "upload.jpg").write_bytes(b"keep")

    assert cleanup_session_directory("session-1") is True
    assert not session_directory.exists()
    assert (other_session_directory / "upload.jpg").exists()


def test_cleanup_session_directory_rejects_unsafe_and_missing_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Do not allow cleanup paths outside the upload folder or claim missing folders removed."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path / "uploads")
    outside_directory = tmp_path / "outside"
    outside_directory.mkdir()

    assert cleanup_session_directory("../outside") is False
    assert cleanup_session_directory("missing") is False
    assert outside_directory.exists()


@pytest.mark.parametrize("mode", ["L", "RGBA", "CMYK"])
def test_ensure_rgb_converts_to_three_channels(mode: str) -> None:
    """Convert grayscale, alpha, and CMYK images to RGB."""
    color = 128 if mode == "L" else (20, 80, 140, 200) if mode == "RGBA" else (20, 80, 140, 0)
    converted = ensure_rgb(Image.new(mode, (2, 2), color=color))

    assert converted.mode == "RGB"
    assert converted.getbands() == ("R", "G", "B")


def test_image_byte_helpers_round_trip() -> None:
    """Encode and decode images without relying on disk files."""
    original = Image.new("RGB", (3, 4), color=(25, 50, 75))

    decoded = bytes_to_pil(pil_to_bytes(original))

    assert decoded.mode == "RGB"
    assert decoded.size == original.size
    assert decoded.getpixel((0, 0)) == original.getpixel((0, 0))


def test_domain_exception_hierarchy() -> None:
    """Keep all domain exceptions rooted in AppError with validation subtypes."""
    assert issubclass(ValidationError, AppError)
    assert issubclass(PayloadTooLargeError, ValidationError)
    assert issubclass(CorruptImageError, ValidationError)
    assert issubclass(ModelInferenceError, AppError)
    assert issubclass(ModelNotLoadedError, ModelInferenceError)
    assert issubclass(ReportGenerationError, AppError)


def test_get_logger_writes_formatted_records_to_stdout_and_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Configure stdout logging and the optional configured file handler."""
    log_file = tmp_path / "artifacts" / "app.log"
    monkeypatch.setattr(Config, "LOG_FILE", log_file)
    monkeypatch.setattr(Config, "ENABLE_FILE_LOGGING", True)
    monkeypatch.setattr(Config, "LOG_LEVEL", "INFO")
    logger = get_logger(f"test_logger_{uuid4().hex}")

    logger.info("validation record")

    assert "INFO     |" in capsys.readouterr().out
    assert "validation record" in log_file.read_text(encoding="utf-8")
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()


def test_validate_upload_uses_configured_pixel_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject images exceeding the centrally configured decoded pixel cap."""
    monkeypatch.setattr(Config, "MAX_IMAGE_PIXELS", 10)

    valid, message = validate_upload(_upload(_image_bytes("PNG"), "large.png"))

    assert valid is False
    assert "pixel" in message.lower()
