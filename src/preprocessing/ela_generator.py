"""Generate Error Level Analysis visualizations using Pillow."""

from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Optional, Union

from PIL import Image, ImageChops, ImageEnhance

from config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ELAGenerator:
	"""Generate Error Level Analysis visualizations for digital images."""

	@staticmethod
	def generate(
		image_input: Union[str, Path, Image.Image],
		output_path: Optional[Union[str, Path]] = None,
		quality: int = Config.ELA_QUALITY,
		enhancement_factor: float = Config.ELA_ENHANCEMENT_FACTOR,
	) -> Image.Image:
		"""Generate an ELA visualization by recompressing an image as JPEG.

		Args:
			image_input: File path or pre-loaded PIL Image object to analyze.
			output_path: Optional destination for the resulting PNG visualization.
			quality: JPEG recompression quality factor from 1 through 95.
			enhancement_factor: Brightness multiplier applied to pixel differences.

		Returns:
			An RGB PIL Image containing the enhanced ELA visualization.

		Raises:
			FileNotFoundError: If the input image path does not exist.
			ValueError: If quality or enhancement_factor is outside its valid range.
			IOError: If the source image cannot be decoded.
			TypeError: If image_input is not a path or PIL Image object.
		"""
		if not Config.ELA_MIN_QUALITY <= quality <= Config.ELA_MAX_QUALITY:
			raise ValueError(
				f"Quality must be between {Config.ELA_MIN_QUALITY} and "
				f"{Config.ELA_MAX_QUALITY}, received: {quality}"
			)
		if not math.isfinite(enhancement_factor) or enhancement_factor <= 0:
			raise ValueError("Enhancement factor must be a finite value greater than zero.")

		is_png = False
		if isinstance(image_input, (str, Path)):
			source_path = Path(image_input)
			if not source_path.exists():
				raise FileNotFoundError(f"Source image not found: {source_path}")
			is_png = source_path.suffix.lower() == ".png"
			with Image.open(source_path) as source_image:
				original_rgb = source_image.convert("RGB")
		elif isinstance(image_input, Image.Image):
			is_png = image_input.format == "PNG"
			original_rgb = image_input.convert("RGB")
		else:
			raise TypeError("image_input must be a file path or PIL Image object.")

		if is_png:
			logger.warning(
				"Source image is PNG. ELA on PNG introduces an artificial baseline error "
				"across the canvas."
			)

		with io.BytesIO() as buffer:
			original_rgb.save(buffer, format="JPEG", quality=quality)
			buffer.seek(0)
			with Image.open(buffer) as recompressed_image:
				recompressed_image.load()
				diff_image = ImageChops.difference(
					original_rgb, recompressed_image.convert("RGB")
				)

		ela_image = ImageEnhance.Brightness(diff_image).enhance(enhancement_factor)

		if output_path is not None:
			destination = Path(output_path)
			destination.parent.mkdir(parents=True, exist_ok=True)
			ela_image.save(destination, format="PNG")

		return ela_image
