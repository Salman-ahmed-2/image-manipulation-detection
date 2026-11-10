"""CASIA filename label extraction utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

_AUTHENTIC_PATTERN = re.compile(r"^(?:Au|Sp)_([A-Za-z]{3})_(\d+)")
_SOURCE_IDENTIFIER_PATTERN = re.compile(r"(?<![A-Za-z0-9])([A-Za-z]{3}\d+)(?![A-Za-z0-9])")


def _extract_group_id(filename: str) -> str:
	"""Extract a CASIA source identifier or a unique filename fallback.

	Args:
		filename: Image filename or path.

	Returns:
		The first source identifier found in the filename, normalized to lowercase.
	"""
	basename = Path(filename).name
	stem = Path(basename).stem
	category_match = _AUTHENTIC_PATTERN.match(stem)
	if category_match:
		return f"{category_match.group(1)}{category_match.group(2)}".lower()

	source_match = _SOURCE_IDENTIFIER_PATTERN.search(stem)
	if source_match:
		return source_match.group(1).lower()
	return stem.lower()


def extract_label_from_filename(filename: str) -> dict[str, Any]:
	"""Map a CASIA filename prefix to its binary and manipulation labels.

	Args:
		filename: CASIA image filename, optionally including a directory path.

	Returns:
		A dictionary containing ``label``, ``label_name``, ``manipulation_type``,
		and ``group_id``.

	Raises:
		ValueError: If the filename does not use a recognized CASIA prefix.
	"""
	basename = Path(filename).name
	if basename.startswith(Config.AUTHENTIC_PREFIX):
		label = Config.AUTHENTIC_LABEL
		label_name = Config.AUTHENTIC_LABEL_NAME
		manipulation_type = Config.PRISTINE_MANIPULATION_TYPE
	elif basename.startswith(Config.COPY_MOVE_PREFIX):
		label = Config.MANIPULATED_LABEL
		label_name = Config.MANIPULATED_LABEL_NAME
		manipulation_type = Config.COPY_MOVE_MANIPULATION_TYPE
	elif basename.startswith(Config.SPLICING_PREFIXES):
		label = Config.MANIPULATED_LABEL
		label_name = Config.MANIPULATED_LABEL_NAME
		manipulation_type = Config.SPLICING_MANIPULATION_TYPE
	elif basename.startswith(Config.TAMPERED_PREFIX):
		label = Config.MANIPULATED_LABEL
		label_name = Config.MANIPULATED_LABEL_NAME
		manipulation_type = Config.GENERAL_MANIPULATION_TYPE
	else:
		logger.warning("Skipping filename with unrecognized CASIA label prefix: %s", filename)
		raise ValueError(f"Unrecognized CASIA filename prefix: {filename}")

	return {
		"label": label,
		"label_name": label_name,
		"manipulation_type": manipulation_type,
		"group_id": _extract_group_id(basename),
	}
