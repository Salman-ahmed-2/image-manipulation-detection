"""Unit tests for ELA visualization generation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

from PIL import Image
import pytest

from config import Config
from src.preprocessing import ela_generator
from src.preprocessing.ela_generator import ELAGenerator


def _write_synthetic_image(path: Path, image_format: str) -> Path:
	"""Write a small synthetic image for a test case.

	Args:
		path: Destination path for the generated fixture image.
		image_format: Pillow format to use when encoding the image.

	Returns:
		The path containing the generated image.
	"""
	image = Image.new("RGB", (17, 13), color=(40, 120, 200))
	image.save(path, format=image_format, quality=Config.ELA_QUALITY)
	return path


def test_generate_returns_rgb_image_with_source_dimensions(tmp_path: Path) -> None:
	"""Generate an RGB ELA image with the source image dimensions."""
	source_path = _write_synthetic_image(tmp_path / "source.jpg", "JPEG")

	result = ELAGenerator.generate(source_path)

	assert result.size == (17, 13)
	assert result.mode == "RGB"


def test_generate_accepts_pil_image_and_saves_png(tmp_path: Path) -> None:
	"""Convert a caller-provided image to RGB and persist the result as PNG."""
	source_image = Image.new("RGBA", (11, 9), color=(10, 20, 30, 128))
	output_path = tmp_path / "nested" / "ela.png"

	result = ELAGenerator.generate(source_image, output_path=output_path)

	assert result.size == source_image.size
	assert result.mode == "RGB"
	with Image.open(output_path) as saved_image:
		assert saved_image.format == "PNG"
		assert saved_image.mode == "RGB"
		assert saved_image.size == source_image.size


def test_generate_png_logs_diagnostic_warning(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Warn when the PNG source has no original JPEG compression history."""
	source_path = _write_synthetic_image(tmp_path / "source.png", "PNG")
	warning = Mock()
	monkeypatch.setattr(ela_generator.logger, "warning", warning)

	result = ELAGenerator.generate(source_path)

	assert result.size == (17, 13)
	warning.assert_called_once_with(
		"Source image is PNG. ELA on PNG introduces an artificial baseline error across the canvas."
	)


@pytest.mark.parametrize("quality", [0, 100])
def test_generate_rejects_invalid_quality(quality: int) -> None:
	"""Reject JPEG quality values outside the configured supported range."""
	image = Image.new("RGB", (4, 4))

	with pytest.raises(ValueError, match="Quality must be between"):
		ELAGenerator.generate(image, quality=quality)


@pytest.mark.parametrize("enhancement_factor", [0.0, -1.0])
def test_generate_rejects_nonpositive_enhancement(enhancement_factor: float) -> None:
	"""Reject zero or negative difference enhancement factors."""
	image = Image.new("RGB", (4, 4))

	with pytest.raises(ValueError, match="Enhancement factor"):
		ELAGenerator.generate(image, enhancement_factor=enhancement_factor)


def test_generate_raises_for_missing_source_path(tmp_path: Path) -> None:
	"""Raise a clear file error when the requested source does not exist."""
	with pytest.raises(FileNotFoundError):
		ELAGenerator.generate(tmp_path / "missing.jpg")


def test_generate_raises_for_undecodable_source(tmp_path: Path) -> None:
	"""Propagate a decoding error for a file that is not a supported image."""
	source_path = tmp_path / "invalid.jpg"
	source_path.write_bytes(b"not an image")

	with pytest.raises(OSError):
		ELAGenerator.generate(source_path)
