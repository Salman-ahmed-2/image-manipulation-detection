"""Dataset integrity scanning utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _record_corrupt_file(image_path: Path, error: Exception) -> None:
	"""Append a corrupt-image failure to the configured log without stopping a scan.

	Args:
		image_path: Path to the image that failed verification.
		error: Exception raised while opening or verifying the image.
	"""
	message = f"{image_path}: {type(error).__name__}: {error}"
	logger.warning("Invalid dataset image: %s", message)
	try:
		Config.CORRUPT_FILES_LOG.parent.mkdir(parents=True, exist_ok=True)
		with Config.CORRUPT_FILES_LOG.open("a", encoding="utf-8") as log_file:
			log_file.write(f"{message}\n")
	except OSError as log_error:
		logger.error(
			"Could not append to corrupt image log %s: %s",
			Config.CORRUPT_FILES_LOG,
			log_error,
		)


def scan_dataset_directory(raw_dir: Path) -> list[dict[str, Any]]:
	"""Recursively inspect supported image files under a raw dataset directory.

	Args:
		raw_dir: Dataset directory to scan. The directory is read-only.

	Returns:
		One metadata dictionary per supported image, including invalid images.
		Invalid image metadata that cannot be read is returned as ``None``.
	"""
	if not raw_dir.is_dir():
		logger.warning("Dataset directory does not exist or is not a directory: %s", raw_dir)
		return []

	records: list[dict[str, Any]] = []
	image_paths = sorted(
		path
		for path in raw_dir.rglob("*")
		if path.is_file() and path.suffix.lower() in Config.DATASET_IMAGE_EXTENSIONS
	)

	for image_path in image_paths:
		record: dict[str, Any] = {
			"filepath": str(image_path),
			"filename": image_path.name,
			"format": None,
			"mode": None,
			"width": None,
			"height": None,
			"channels": None,
			"filesize_bytes": None,
			"is_valid": False,
		}
		try:
			record["filesize_bytes"] = image_path.stat().st_size
			with Image.open(image_path) as image:
				image.verify()
			with Image.open(image_path) as image:
				record.update(
					{
						"format": image.format,
						"mode": image.mode,
						"width": image.width,
						"height": image.height,
						"channels": len(image.getbands()),
						"is_valid": True,
					}
				)
		except (
			OSError,
			SyntaxError,
			ValueError,
			UnidentifiedImageError,
			Image.DecompressionBombError,
		) as error:
			_record_corrupt_file(image_path, error)
			try:
				record["filesize_bytes"] = image_path.stat().st_size
			except OSError:
				pass
		records.append(record)

	logger.info("Scanned %d supported image files in %s", len(records), raw_dir)
	return records
