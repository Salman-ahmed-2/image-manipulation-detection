"""Pillow image conversion helpers shared by preprocessing modules."""

from __future__ import annotations

import io

from PIL import Image


def ensure_rgb(image: Image.Image) -> Image.Image:
    """Return an image converted to three-channel RGB mode.

    Args:
        image: Pillow image in any supported mode.

    Returns:
        The original image if already RGB, otherwise an RGB conversion.
    """
    if image.mode == "RGB":
        return image
    return image.convert("RGB")


def bytes_to_pil(image_bytes: bytes) -> Image.Image:
    """Decode image bytes into a detached Pillow image.

    Args:
        image_bytes: Encoded image content.

    Returns:
        A loaded Pillow image independent of the temporary byte stream.

    Raises:
        PIL.UnidentifiedImageError: If the bytes do not contain a supported image.
        OSError: If the image data cannot be read.
    """
    with Image.open(io.BytesIO(image_bytes)) as image:
        image.load()
        return image.copy()


def pil_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """Encode a Pillow image into an in-memory byte string.

    Args:
        image: Pillow image to encode.
        format: Output image format supported by Pillow. Defaults to PNG.

    Returns:
        Encoded image bytes.

    Raises:
        ValueError: If Pillow does not support the requested format or image mode.
        OSError: If image encoding fails.
    """
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()
