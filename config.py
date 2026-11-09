"""Centralized Configuration Module for Image Manipulation Detection System.

All application constants, directories, limits, hyperparameters, and forensic
defaults are defined exclusively in this module. Hardcoded paths or constants
in other modules are strictly prohibited.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, Set, Tuple
from dotenv import load_dotenv

# Ingest environment variables from .env file if present
load_dotenv()


class Config:
    """Master configuration class managing paths, hyperparameters, and limits."""

    # -------------------------------------------------------------------------
    # Base Directories & Filesystem Hierarchy
    # -------------------------------------------------------------------------
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    CASIA_V1_DIR: Path = RAW_DATA_DIR / "casia_v1"
    CASIA_V2_DIR: Path = RAW_DATA_DIR / "casia_v2"
    ANNOTATIONS_DIR: Path = DATA_DIR / "annotations"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    METADATA_DIR: Path = DATA_DIR / "metadata"
    SPLITS_DIR: Path = DATA_DIR / "splits"

    ARTIFACTS_DIR: Path = BASE_DIR / "artifacts"
    MODEL_DIR: Path = ARTIFACTS_DIR / "models"
    PLOTS_DIR: Path = ARTIFACTS_DIR / "plots"
    REPORTS_DIR: Path = ARTIFACTS_DIR / "reports"
    PREDICTIONS_DIR: Path = ARTIFACTS_DIR / "predictions"

    TEMP_DIR: Path = BASE_DIR / "temp"
    UPLOAD_FOLDER: Path = TEMP_DIR / "uploads"

    # -------------------------------------------------------------------------
    # File Ingestion & Security Bounds
    # -------------------------------------------------------------------------
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB maximum upload payload
    ALLOWED_EXTENSIONS: Set[str] = {"jpg", "jpeg", "png"}
    MAX_IMAGE_PIXELS: int = 50_000_000  # Pillow decompression bomb protection
    TEMP_FILE_EXPIRY: int = 1800  # 30 minutes in seconds

    # Magic byte signatures for verification
    MAGIC_BYTES: dict[str, bytes] = {
        "jpeg": b"\xff\xd8\xff",
        "png": b"\x89PNG\r\n\x1a\n",
    }

    # -------------------------------------------------------------------------
    # Deep Learning Hyperparameters & Model Paths
    # -------------------------------------------------------------------------
    INPUT_SHAPE: Tuple[int, int, int] = (224, 224, 3)
    TARGET_SIZE: Tuple[int, int] = (224, 224)
    BATCH_SIZE: int = 32
    DEFAULT_EPOCHS: int = 50
    RANDOM_SEED: int = 42

    ACTIVE_MODEL: str = os.getenv("ACTIVE_MODEL", "mobilenet").lower()
    MODEL_PATH_CNN: Path = MODEL_DIR / "cnn_model.keras"
    MODEL_PATH_MOBILENET: Path = MODEL_DIR / "mobilenet_model.keras"

    # Class definitions
    CLASS_LABELS: dict[int, str] = {
        0: "Authentic",
        1: "Potentially Manipulated",
    }
    CLASSIFICATION_THRESHOLD: float = 0.5

    # -------------------------------------------------------------------------
    # Image Forensics & Error Level Analysis (ELA)
    # -------------------------------------------------------------------------
    ELA_QUALITY: int = 90
    ELA_ENHANCEMENT_FACTOR: float = 10.0
    ELA_DISCLAIMER: str = (
        "ELA visualization is an investigative aid. Bright regions in the ELA image indicate "
        "potential compression inconsistencies and do not constitute definitive "
        "proof of digital manipulation."
    )

    # -------------------------------------------------------------------------
    # Flask Web Application & Security
    # -------------------------------------------------------------------------
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "replace-with-a-secure-random-32-char-key-in-production"
    )
    FLASK_APP: str = os.getenv("FLASK_APP", "app.py")
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "1") == "1"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "5000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def init_app(cls, app: Optional[Any] = None) -> None:
        """Initialize and verify application filesystem hierarchy.

        Ensures all runtime directories exist before execution commences.

        Args:
            app: Optional Flask application instance whose configured upload
                directory should also be created.
        """
        directories = [
            cls.DATA_DIR,
            cls.RAW_DATA_DIR,
            cls.CASIA_V1_DIR,
            cls.CASIA_V2_DIR,
            cls.ANNOTATIONS_DIR,
            cls.PROCESSED_DATA_DIR,
            cls.METADATA_DIR,
            cls.SPLITS_DIR,
            cls.ARTIFACTS_DIR,
            cls.MODEL_DIR,
            cls.PLOTS_DIR,
            cls.REPORTS_DIR,
            cls.PREDICTIONS_DIR,
            cls.TEMP_DIR,
            Path(app.config.get("UPLOAD_FOLDER") or cls.UPLOAD_FOLDER)
            if app is not None
            else cls.UPLOAD_FOLDER,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
