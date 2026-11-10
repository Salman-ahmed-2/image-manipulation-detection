"""Tests for CASIA dataset scanning, labels, and metadata exports."""

from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import Mock

import pytest
from PIL import Image

from config import Config
from scripts import prepare_dataset as prepare_dataset_script
from src.data.dataset_loader import extract_label_from_filename
from src.data.dataset_validator import scan_dataset_directory


@pytest.mark.parametrize(
	("filename", "label", "label_name", "manipulation_type", "group_id"),
	[
		("Au_ani_0001.jpg", 0, "Authentic", "Pristine", "ani0001"),
		(
			"Tp_S_CRN_M_N_nat10129_nat10129_00123.jpg",
			1,
			"Manipulated",
			"Copy-Move",
			"nat10129",
		),
		(
			"Tp_D_CRN_S_N_ani00073_ani00068_00192.jpg",
			1,
			"Manipulated",
			"Splicing",
			"ani00073",
		),
		("Tp_00123.jpg", 1, "Manipulated", "General", "tp_00123"),
		("Sp_ani_0001.jpg", 1, "Manipulated", "Splicing", "ani0001"),
	],
)
def test_extract_label_from_filename(
	filename: str,
	label: int,
	label_name: str,
	manipulation_type: str,
	group_id: str,
) -> None:
	"""Known CASIA prefixes produce the required class and group metadata."""
	result = extract_label_from_filename(filename)

	assert result == {
		"label": label,
		"label_name": label_name,
		"manipulation_type": manipulation_type,
		"group_id": group_id,
	}


def test_extract_label_from_filename_rejects_unknown_prefix(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Unknown filename prefixes warn and raise instead of receiving an assumed label."""
	warning = Mock()
	monkeypatch.setattr("src.data.dataset_loader.logger.warning", warning)

	with pytest.raises(ValueError, match="Unrecognized CASIA filename prefix"):
		extract_label_from_filename("unknown_image.jpg")

	warning.assert_called_once()


def test_scan_dataset_directory_records_metadata_and_corrupt_files(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The scanner returns valid image metadata and logs corrupt image failures."""
	valid_path = tmp_path / "Au_ani_0001.tif"
	Image.new("RGB", (7, 5), color=(1, 2, 3)).save(valid_path, format="TIFF")
	corrupt_path = tmp_path / "Tp_D_broken.jpg"
	corrupt_path.write_bytes(b"not a decodable image")
	corrupt_log = tmp_path / "logs" / "corrupt_files.log"
	monkeypatch.setattr(Config, "CORRUPT_FILES_LOG", corrupt_log)

	records = scan_dataset_directory(tmp_path)

	assert len(records) == 2
	valid_record = next(record for record in records if record["filename"] == valid_path.name)
	assert valid_record["is_valid"] is True
	assert valid_record["format"] == "TIFF"
	assert valid_record["mode"] == "RGB"
	assert (valid_record["width"], valid_record["height"], valid_record["channels"]) == (7, 5, 3)
	assert valid_record["filesize_bytes"] == valid_path.stat().st_size

	corrupt_record = next(record for record in records if record["filename"] == corrupt_path.name)
	assert corrupt_record["is_valid"] is False
	assert corrupt_record["filesize_bytes"] == corrupt_path.stat().st_size
	assert corrupt_path.name in corrupt_log.read_text(encoding="utf-8")


def test_prepare_dataset_writes_inventory_and_labels(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Catalog generation writes both schemas and excludes invalid or unknown labels."""
	casia_v1_dir = tmp_path / "casia_v1"
	casia_v2_dir = tmp_path / "casia_v2"
	casia_v1_dir.mkdir()
	casia_v2_dir.mkdir()
	Image.new("RGB", (3, 2)).save(casia_v1_dir / "Au_ani_0001.jpg", format="JPEG")
	Image.new("L", (4, 3)).save(
		casia_v2_dir / "Tp_S_CRN_M_N_nat10129_nat10129_00123.png", format="PNG"
	)
	Image.new("RGB", (2, 2)).save(casia_v2_dir / "unknown.png", format="PNG")
	(casia_v2_dir / "Tp_D_broken.jpg").write_bytes(b"bad image")
	inventory_path = tmp_path / "metadata" / "dataset_inventory.csv"
	labels_path = tmp_path / "metadata" / "dataset_labels.csv"
	monkeypatch.setattr(Config, "BASE_DIR", tmp_path)
	monkeypatch.setattr(Config, "CASIA_V1_DIR", casia_v1_dir)
	monkeypatch.setattr(Config, "CASIA_V2_DIR", casia_v2_dir)
	monkeypatch.setattr(Config, "DATASET_INVENTORY_PATH", inventory_path)
	monkeypatch.setattr(Config, "DATASET_LABELS_PATH", labels_path)
	monkeypatch.setattr(Config, "CORRUPT_FILES_LOG", tmp_path / "metadata" / "corrupt_files.log")

	assert prepare_dataset_script.prepare_dataset() == (4, 2)

	with inventory_path.open(encoding="utf-8", newline="") as csv_file:
		inventory_rows = list(csv.DictReader(csv_file))
	with labels_path.open(encoding="utf-8", newline="") as csv_file:
		label_rows = list(csv.DictReader(csv_file))

	assert len(inventory_rows) == 4
	assert set(inventory_rows[0]) == {
		"image_id", "filepath", "filename", "dataset_version", "format", "width",
		"height", "channels", "filesize_bytes", "is_valid",
	}
	assert len(label_rows) == 2
	tampered_label = next(row for row in label_rows if row["label"] == "1")
	assert tampered_label["manipulation_type"] == "Copy-Move"
	assert tampered_label["group_id"] == "nat10129"
