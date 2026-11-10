"""Unit tests for image loading, resizing, and normalization."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from config import Config
from src.preprocessing.image_loader import load_image
from src.preprocessing.image_normalizer import normalize_image, prepare_tensor
from src.preprocessing.image_resizer import resize_image
from src.utils.exceptions import CorruptImageError


def test_load_image_converts_grayscale_to_rgb() -> None:
    """Convert grayscale input to three identical RGB channels."""
    grayscale = Image.new("L", Config.TARGET_SIZE, color=128)

    result = load_image(grayscale)

    assert result.mode == "RGB"
    assert result.getpixel((0, 0)) == (128, 128, 128)


def test_load_image_composites_transparency_over_white() -> None:
    """Flatten fully transparent image pixels to white."""
    rgba = Image.new("RGBA", Config.TARGET_SIZE, color=(20, 90, 160, 0))

    result = load_image(rgba)

    assert result.mode == "RGB"
    assert result.getpixel((0, 0)) == (255, 255, 255)


def test_load_image_accepts_encoded_bytes() -> None:
    """Decode in-memory JPEG bytes and return an independent RGB image."""
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), color=(12, 34, 56)).save(buffer, format="JPEG")

    result = load_image(buffer.getvalue())

    assert result.mode == "RGB"
    assert result.size == (2, 2)


def test_load_image_accepts_path(tmp_path: Path) -> None:
    """Decode a synthetic image saved to a temporary path."""
    image_path = tmp_path / "synthetic.png"
    Image.new("RGB", (3, 2), color=(10, 20, 30)).save(image_path)

    result = load_image(image_path)

    assert result.mode == "RGB"
    assert result.size == (3, 2)


@pytest.mark.parametrize(
    "image_input",
    [b"not an image", Path("missing-preprocessing-image.png")],
)
def test_load_image_rejects_corrupt_or_missing_inputs(
    image_input: bytes | Path,
) -> None:
    """Raise the project validation error for corrupt data and missing paths."""
    with pytest.raises(CorruptImageError):
        load_image(image_input)


def test_resize_image_outputs_requested_size() -> None:
    """Resize an image to the requested dimensions."""
    image = Image.new("RGB", (12, 8), color=(30, 60, 90))

    result = resize_image(image, target_size=(8, 8))

    assert result.mode == "RGB"
    assert result.size == (8, 8)


def test_resize_image_preserves_aspect_ratio_with_padding() -> None:
    """Preserve aspect ratio and fill unused target area with black padding."""
    image = Image.new("RGB", (4, 2), color=(200, 100, 50))

    result = resize_image(image, target_size=(8, 8), keep_aspect_ratio=True)

    assert result.size == (8, 8)
    assert result.getpixel((0, 0)) == (0, 0, 0)
    assert result.getpixel((4, 4)) == (200, 100, 50)


@pytest.mark.parametrize("target_size", [(0, 4), (4, 0), (-1, 4), (4,), (2.5, 4)])
def test_resize_image_rejects_invalid_dimensions(
    target_size: tuple[int, ...],
) -> None:
    """Reject target dimensions that cannot describe a positive image size."""
    with pytest.raises(ValueError):
        resize_image(Image.new("RGB", (2, 2)), target_size=target_size)


def test_normalize_image_standard_mode_returns_float32_unit_range() -> None:
    """Scale standard CNN pixels into [0, 1] float32 values."""
    pixels = np.array([0, Config.PIXEL_VALUE_MAX / 2, Config.PIXEL_VALUE_MAX])

    result = normalize_image(pixels, mode="standard")

    assert result.dtype == np.float32
    assert result.tolist() == pytest.approx([0.0, 0.5, 1.0])


@pytest.mark.parametrize("mode", ["tf", "mobilenet"])
def test_normalize_image_mobilenet_modes_return_signed_unit_range(mode: str) -> None:
    """Scale MobileNet pixels into [-1, 1] float32 values."""
    pixels = np.array([0, Config.PIXEL_VALUE_MAX / 2, Config.PIXEL_VALUE_MAX])

    result = normalize_image(pixels, mode=mode)

    assert result.dtype == np.float32
    assert result.tolist() == pytest.approx([-1.0, 0.0, 1.0])


@pytest.mark.parametrize("mode", ["standard", "mobilenet"])
def test_prepare_tensor_returns_batch_ready_shape_and_range(mode: str) -> None:
    """Produce a normalized, batch-first RGB tensor of the configured shape."""
    image = Image.new("RGB", Config.TARGET_SIZE, color=(25, 100, 255))

    result = prepare_tensor(image, mode=mode)

    assert result.shape == (1, *Config.INPUT_SHAPE)
    assert result.dtype == np.float32
    assert result.min() >= (-1.0 if mode == "mobilenet" else 0.0)
    assert result.max() <= 1.0


def test_normalize_image_rejects_unsupported_mode_and_out_of_range_pixels() -> None:
    """Reject invalid modes and pixel values outside the supported input range."""
    with pytest.raises(ValueError, match="Unsupported normalization mode"):
        normalize_image(np.array([0]), mode="unknown")
    with pytest.raises(ValueError, match="outside the valid range"):
        normalize_image(np.array([Config.PIXEL_VALUE_MAX + 1]), mode="standard")