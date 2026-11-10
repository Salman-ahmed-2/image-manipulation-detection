"""Convert resized image pixels into model-ready normalized tensors."""

from __future__ import annotations

import numpy as np
from PIL import Image

from config import Config
from src.preprocessing.image_resizer import resize_image


def normalize_image(image_array: np.ndarray, mode: str = "standard") -> np.ndarray:
    """Convert pixel values to a float32 model-specific normalization range.

    Args:
        image_array: An array of image pixels in the range from zero to
            ``Config.PIXEL_VALUE_MAX``.
        mode: ``"standard"`` scales to [0, 1]; ``"tf"`` and ``"mobilenet"``
            scale to [-1, 1].

    Returns:
        A float32 array normalized for the requested model.

    Raises:
        ValueError: If mode is unsupported or input pixels are invalid/out of range.
    """
    if mode == "standard":
        lower_bound, upper_bound = 0.0, 1.0
        normalized = np.asarray(image_array, dtype=np.float32) / Config.PIXEL_VALUE_MAX
    elif mode in {"tf", "mobilenet"}:
        lower_bound, upper_bound = -1.0, 1.0
        normalized = (
            np.asarray(image_array, dtype=np.float32)
            / (Config.PIXEL_VALUE_MAX / 2)
            - 1.0
        )
    else:
        raise ValueError(f"Unsupported normalization mode: {mode!r}.")

    if normalized.size == 0 or not np.isfinite(normalized).all():
        raise ValueError("Image array must contain finite pixel values.")
    if normalized.min() < lower_bound or normalized.max() > upper_bound:
        raise ValueError(
            f"Pixel values are outside the valid range for normalization mode {mode!r}."
        )
    return normalized


def prepare_tensor(
    image: Image.Image,
    target_size: tuple[int, int] = Config.TARGET_SIZE,
    mode: str = "standard",
) -> np.ndarray:
    """Resize, normalize, and batch an image for model inference.

    Args:
        image: Source Pillow image.
        target_size: Target width and height. Defaults to ``Config.TARGET_SIZE``.
        mode: Normalization mode accepted by :func:`normalize_image`.

    Returns:
        A float32 batch tensor shaped ``(1, height, width, 3)``.

    Raises:
        ValueError: If target_size or mode is invalid, or the pixels cannot be
            normalized.
    """
    resized_image = resize_image(image, target_size=target_size)
    normalized_image = normalize_image(np.asarray(resized_image), mode=mode)
    return np.expand_dims(normalized_image, axis=0)