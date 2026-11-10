"""Scan CASIA raw directories and export dataset metadata catalogs."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd

from config import Config
from src.data.dataset_loader import extract_label_from_filename
from src.data.dataset_splitter import DatasetSplitter
from src.data.dataset_validator import scan_dataset_directory
from src.utils.logger import get_logger

logger = get_logger(__name__)

def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
	"""Write metadata rows with a stable column order.

	Args:
		path: Destination CSV path.
		columns: Ordered CSV column names.
		rows: Metadata records to serialize.
	"""
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", newline="", encoding="utf-8") as csv_file:
		writer = csv.DictWriter(csv_file, fieldnames=columns, extrasaction="ignore")
		writer.writeheader()
		writer.writerows(rows)


def prepare_dataset() -> tuple[int, int]:
	"""Scan both configured CASIA directories and write inventory and label CSVs.

	Returns:
		A tuple containing the number of inventory rows and valid labeled rows.
	"""
	inventory: list[dict[str, Any]] = []
	labels: list[dict[str, Any]] = []
	datasets = (
		(Config.CASIA_V1_DIR, Config.CASIA_V1_VERSION),
		(Config.CASIA_V2_DIR, Config.CASIA_V2_VERSION),
	)

	for raw_dir, dataset_version in datasets:
		for scanned_record in scan_dataset_directory(raw_dir):
			image_path = Path(scanned_record["filepath"])
			relative_path = image_path.relative_to(raw_dir).as_posix()
			image_id = f"{dataset_version}:{relative_path}"
			try:
				filepath = image_path.relative_to(Config.BASE_DIR).as_posix()
			except ValueError:
				filepath = image_path.as_posix()

			inventory.append(
				{
					"image_id": image_id,
					"filepath": filepath,
					"filename": scanned_record["filename"],
					"dataset_version": dataset_version,
					"format": scanned_record["format"],
					"width": scanned_record["width"],
					"height": scanned_record["height"],
					"channels": scanned_record["channels"],
					"filesize_bytes": scanned_record["filesize_bytes"],
					"is_valid": scanned_record["is_valid"],
				}
			)

			if not scanned_record["is_valid"]:
				continue
			try:
				label_info = extract_label_from_filename(scanned_record["filename"])
			except ValueError:
				continue
			labels.append(
				{
					"image_id": image_id,
					"filename": scanned_record["filename"],
					"label": label_info["label"],
					"label_name": label_info["label_name"],
					"manipulation_type": label_info["manipulation_type"],
					"group_id": label_info["group_id"],
					"dataset_version": dataset_version,
				}
			)

	_write_csv(Config.DATASET_INVENTORY_PATH, Config.DATASET_INVENTORY_COLUMNS, inventory)
	_write_csv(Config.DATASET_LABELS_PATH, Config.DATASET_LABEL_COLUMNS, labels)
	label_df = pd.read_csv(Config.DATASET_LABELS_PATH)
	splitter = DatasetSplitter(
		train_ratio=Config.DATASET_TRAIN_RATIO,
		val_ratio=Config.DATASET_VALIDATION_RATIO,
		test_ratio=Config.DATASET_TEST_RATIO,
		random_state=Config.RANDOM_SEED,
	)
	split_df = splitter.split_dataframe(label_df)
	split_df = split_df.loc[:, Config.DATASET_SPLIT_COLUMNS]
	split_df.to_csv(Config.DATASET_SPLIT_PATH, index=False)
	for split_name in Config.DATASET_SPLIT_NAMES:
		partition = split_df[split_df["split"] == split_name]
		authentic_count = partition["label_name"].eq(Config.AUTHENTIC_LABEL_NAME).sum()
		manipulated_count = partition["label_name"].eq(Config.MANIPULATED_LABEL_NAME).sum()
		logger.info(
			"Dataset split '%s': total=%d, authentic=%d, manipulated=%d",
			split_name,
			len(partition),
			authentic_count,
			manipulated_count,
		)
	logger.info(
		"Wrote %d inventory rows, %d label rows, and %d split rows to %s",
		len(inventory),
		len(labels),
		len(split_df),
		Config.METADATA_DIR,
	)
	return len(inventory), len(labels)


def main() -> int:
	"""Run the dataset catalog generation command.

	Returns:
		A process exit code of zero when catalog generation succeeds.
	"""
	prepare_dataset()
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
