"""Load image inputs and normalize their color mode for model preprocessing."""

from __future__ import annotations

import io
from pathlib import Path
from typing import TypeAlias

from PIL import Image, UnidentifiedImageError

from src.utils.exceptions import CorruptImageError
from src.utils.logger import get_logger

logger = get_logger(__name__)

ImageInput: TypeAlias = str | Path | bytes | Image.Image


def load_image(image_input: ImageInput) -> Image.Image:
    """Load an image and return it as an independent three-channel RGB image.

    Transparent pixels are composited over white so alpha values do not become
    an extra model input channel.

    Args:
        image_input: A filesystem path, encoded image bytes, or Pillow image.

    Returns:
        A loaded RGB Pillow image independent of the input stream.

    Raises:
        CorruptImageError: If the input cannot be identified, opened, or decoded.
        TypeError: If image_input is not one of the supported input types.
    """
    try:
        if isinstance(image_input, Image.Image):
            image_input.load()
            return _convert_to_rgb(image_input)
        if isinstance(image_input, bytes):
            with Image.open(io.BytesIO(image_input)) as image:
                image.load()
                return _convert_to_rgb(image)
        if isinstance(image_input, (str, Path)):
            with Image.open(Path(image_input)) as image:
                image.load()
                return _convert_to_rgb(image)
        raise TypeError("image_input must be a path, bytes, or PIL Image.")
    except (UnidentifiedImageError, OSError, ValueError) as error:
        logger.warning(
            "Unable to decode image input of type %s: %s",
            type(image_input).__name__,
            type(error).__name__,
        )
        raise CorruptImageError("Image input is corrupt or cannot be decoded.") from error


def _convert_to_rgb(image: Image.Image) -> Image.Image:
    """Convert an opened image to RGB, flattening transparency over white.

    Args:
        image: A loaded Pillow image.

    Returns:
        A detached three-channel RGB image.
    """
    if image.mode in {"RGBA", "LA", "PA"} or "transparency" in image.info:
        rgba_image = image.convert("RGBA")
        background = Image.new("RGBA", rgba_image.size, (255, 255, 255, 255))
        return Image.alpha_composite(background, rgba_image).convert("RGB")
    return image.convert("RGB")