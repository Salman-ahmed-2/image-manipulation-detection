"""Tests for centralized application configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from config import Config


def test_config_exports_expected_runtime_defaults() -> None:
    """Verify configured paths, runtime limits, model settings, and disclaimer."""
    assert Config.BASE_DIR == Path(__file__).resolve().parents[1]
    assert Config.DATA_DIR == Config.BASE_DIR / "data"
    assert Config.UPLOAD_FOLDER == Config.TEMP_DIR / "uploads"
    assert Config.MAX_CONTENT_LENGTH == 16 * 1024 * 1024
    assert Config.ALLOWED_EXTENSIONS == {"jpg", "jpeg", "png"}
    assert Config.MAX_IMAGE_PIXELS == 50_000_000
    assert Config.TEMP_FILE_EXPIRY == 1800
    assert Config.INPUT_SHAPE == (224, 224, 3)
    assert Config.CIFAKE_INPUT_SHAPE == (32, 32, 3)
    assert Config.CIFAKE_TARGET_SIZE == (32, 32)
    assert Config.HUGGINGFACE_INPUT_SHAPE == (224, 224, 3)
    assert Config.HUGGINGFACE_TARGET_SIZE == (224, 224)
    assert Config.CIFAKE_SUPPORTED_MODELS == (
        Config.CIFAKE_MODEL_NAME,
        Config.HUGGINGFACE_MODEL_NAME,
    )
    assert Config.HUGGINGFACE_MODEL_ID == "dima806/ai_vs_real_image_detection"
    assert Config.HUGGINGFACE_MODEL_REVISION == (
        "5d647683672ffd0080441f4e8b4345934c44cc61"
    )
    assert Config.HUGGINGFACE_FINETUNED_MODEL_DIR == (
        Config.ARTIFACTS_DIR
        / "cifake"
        / "ai_vs_real_genimage_outputs_v3"
        / "huggingface_vit"
    )
    assert Config.CIFAKE_CLASS_LABELS == {0: "Real photo", 1: "AI-generated"}
    assert Config.MODEL_PATH_CIFAKE_CNN == (
        Config.ARTIFACTS_DIR
        / "cifake"
        / "ai_vs_real_genimage_outputs_v3"
        / "cnn"
        / "cifake_custom_cnn_ai_vs_real_genimage_v3.keras"
    )
    assert Config.BATCH_SIZE == 32
    assert Config.DEFAULT_EPOCHS == 50
    assert Config.ACTIVE_MODEL == "cifake_cnn"
    assert Config.ELA_QUALITY == 90
    assert Config.ELA_ENHANCEMENT_FACTOR == 10.0
    assert Config.ELA_DISCLAIMER == (
        "ELA visualization is an investigative aid. Bright regions in the ELA image indicate "
        "potential compression inconsistencies and do not constitute definitive proof of "
        "digital manipulation."
    )
    assert Config.HOST == "127.0.0.1"
    assert Config.PORT == 5000


def test_init_app_creates_configured_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Create the configured directory hierarchy without using repository data."""
    directory_names = (
        "DATA_DIR",
        "RAW_DATA_DIR",
        "CASIA_V1_DIR",
        "CASIA_V2_DIR",
        "ANNOTATIONS_DIR",
        "PROCESSED_DATA_DIR",
        "METADATA_DIR",
        "SPLITS_DIR",
        "ARTIFACTS_DIR",
        "MODEL_DIR",
        "PLOTS_DIR",
        "REPORTS_DIR",
        "PREDICTIONS_DIR",
        "TEMP_DIR",
        "UPLOAD_FOLDER",
    )
    for name in directory_names:
        monkeypatch.setattr(Config, name, tmp_path / name.lower())

    Config.init_app()

    assert all(getattr(Config, name).is_dir() for name in directory_names)


def test_init_app_creates_app_specific_upload_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Create an app-provided upload directory in addition to artifact paths."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path / "default-uploads")

    class TestApp:
        """Minimal Flask-like object exposing upload configuration."""

        config: dict[str, Any] = {"UPLOAD_FOLDER": str(tmp_path / "custom-uploads")}

    Config.init_app(TestApp())

    assert (tmp_path / "custom-uploads").is_dir()
    assert not (tmp_path / "default-uploads").exists()


def test_init_app_propagates_directory_creation_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Do not hide filesystem failures while initializing directories."""
    invalid_directory = tmp_path / "not-a-directory"
    invalid_directory.write_text("file")
    monkeypatch.setattr(Config, "DATA_DIR", invalid_directory / "child")

    with pytest.raises(OSError):
        Config.init_app()
