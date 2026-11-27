"""Resize images to the configured model dimensions."""

from __future__ import annotations

from numbers import Integral

from PIL import Image, ImageOps

from config import Config


def resize_image(
    image: Image.Image,
    target_size: tuple[int, int] = Config.TARGET_SIZE,
    keep_aspect_ratio: bool = False,
    resample: Image.Resampling = Image.Resampling.BICUBIC,
) -> Image.Image:
    """Resize an image using the requested resampling filter, optionally padding to fit.

    Args:
        image: Source Pillow image.
        target_size: Target width and height. Defaults to ``Config.TARGET_SIZE``.
        keep_aspect_ratio: If true, preserve the source ratio and center-pad the
            resized image with the configured padding color.
        resample: Pillow resampling filter. Defaults to ``Image.Resampling.BICUBIC``.

    Returns:
        An RGB image with dimensions ``target_size``.

    Raises:
        ValueError: If target_size is not a pair of positive integer dimensions.
    """
    if (
        len(target_size) != 2
        or any(not isinstance(dimension, Integral) or isinstance(dimension, bool)
               or dimension <= 0 for dimension in target_size)
    ):
        raise ValueError("target_size must contain two positive integer dimensions.")

    width, height = (int(dimension) for dimension in target_size)
    rgb_image = image.convert("RGB")
    if not keep_aspect_ratio:
        return rgb_image.resize(
            (width, height),
            resample=resample,
        )

    resized_image = ImageOps.contain(
        rgb_image,
        (width, height),
        method=resample,
    )
    canvas = Image.new("RGB", (width, height), color="black")
    left = (width - resized_image.width) // 2
    top = (height - resized_image.height) // 2
    canvas.paste(resized_image, (left, top))
    return canvas