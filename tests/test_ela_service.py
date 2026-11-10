"""Unit tests for the ELA service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest
from PIL import Image

from config import Config
from src.preprocessing.ela_generator import ELAGenerator
from src.services.ela_service import ELAService
from src.utils.exceptions import ValidationError


def test_generate_and_save_creates_session_scoped_png(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Save generated ELA output under the configured upload folder."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    source_path = tmp_path / "source.png"
    Image.new("RGB", (12, 8), color=(30, 80, 120)).save(source_path)

    result = ELAService().generate_and_save(source_path, "session-123")

    assert result == tmp_path / "session-123" / "ela_result.png"
    with Image.open(result) as image:
        assert image.format == "PNG"
        assert image.size == (12, 8)


def test_generate_and_save_rejects_unsafe_session_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject identifiers that could write ELA output outside the upload folder."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)

    with pytest.raises(ValidationError, match="session"):
        ELAService().generate_and_save(tmp_path / "source.png", "../outside")


def test_generate_and_save_surfaces_generator_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Preserve explicit generator failures instead of returning a fake result."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    generate = Mock(side_effect=ValueError("Invalid ELA quality."))
    monkeypatch.setattr(ELAGenerator, "generate", generate)

    with pytest.raises(ValueError, match="Invalid ELA quality"):
        ELAService().generate_and_save(tmp_path / "source.png", "session-123")

    generate.assert_called_once()
