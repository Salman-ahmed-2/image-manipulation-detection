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



# Ingest environment variables from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


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
    DATASET_IMAGE_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".tif"}
    ANNOTATIONS_DIR: Path = DATA_DIR / "annotations"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    METADATA_DIR: Path = DATA_DIR / "metadata"
    DATASET_INVENTORY_PATH: Path = METADATA_DIR / "dataset_inventory.csv"
    DATASET_LABELS_PATH: Path = METADATA_DIR / "dataset_labels.csv"
    DATASET_SPLIT_PATH: Path = METADATA_DIR / "dataset_split.csv"
    CORRUPT_FILES_LOG: Path = METADATA_DIR / "corrupt_files.log"
    SPLITS_DIR: Path = DATA_DIR / "splits"

    CASIA_V1_VERSION: str = "CASIA_v1"
    CASIA_V2_VERSION: str = "CASIA_v2"
    AUTHENTIC_LABEL: int = 0
    MANIPULATED_LABEL: int = 1
    AUTHENTIC_LABEL_NAME: str = "Authentic"
    MANIPULATED_LABEL_NAME: str = "Manipulated"
    AUTHENTIC_PREFIX: str = "Au_"
    TAMPERED_PREFIX: str = "Tp_"
    COPY_MOVE_PREFIX: str = "Tp_S_"
    SPLICING_PREFIXES: tuple[str, ...] = ("Tp_D_", "Sp_")
    PRISTINE_MANIPULATION_TYPE: str = "Pristine"
    COPY_MOVE_MANIPULATION_TYPE: str = "Copy-Move"
    SPLICING_MANIPULATION_TYPE: str = "Splicing"
    GENERAL_MANIPULATION_TYPE: str = "General"
    DATASET_INVENTORY_COLUMNS: tuple[str, ...] = (
        "image_id",
        "filepath",
        "filename",
        "dataset_version",
        "format",
        "width",
        "height",
        "channels",
        "filesize_bytes",
        "is_valid",
    )
    DATASET_LABEL_COLUMNS: tuple[str, ...] = (
        "image_id",
        "filename",
        "label",
        "label_name",
        "manipulation_type",
        "group_id",
        "dataset_version",
    )
    DATASET_SPLIT_COLUMNS: tuple[str, ...] = (
        "image_id",
        "filename",
        "label",
        "label_name",
        "group_id",
        "split",
        "dataset_version",
    )
    DATASET_SPLIT_NAMES: tuple[str, ...] = ("train", "validation", "test")
    DATASET_TRAIN_RATIO: float = 0.70
    DATASET_VALIDATION_RATIO: float = 0.15
    DATASET_TEST_RATIO: float = 0.15
    DATASET_MINIMUM_GROUPS: int = 4
    EVALUATION_MODEL_CHOICES: tuple[str, ...] = ("cnn", "mobilenet", "both")
    RESULTS_TEMPLATE_PATH: Path = BASE_DIR / "docs" / "reports" / "RESULTS_TEMPLATE.md"
    PLOT_DPI: int = 150

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
    PIXEL_VALUE_MAX: float = 255.0
    MAX_ANALYSIS_LATENCY_SECONDS: float = 5.0
    PERFORMANCE_TEST_ITERATIONS: int = 10

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
    MOBILENET_WEIGHTS: str = "imagenet"
    MOBILENET_BASE_MODEL_NAME: str = "mobilenetv2_base"
    MOBILENET_MODEL_NAME: str = "mobilenet_classifier"
    MOBILENET_NORMALIZATION_MODE: str = "mobilenet"
    MOBILENET_HEAD_UNITS: tuple[int, int] = (256, 128)
    MOBILENET_HEAD_DROPOUT_RATES: tuple[float, float] = (0.4, 0.3)
    MOBILENET_OUTPUT_UNITS: int = 1
    MOBILENET_INITIAL_LEARNING_RATE: float = 1e-3
    MOBILENET_FINE_TUNE_LEARNING_RATE: float = 1e-5
    MOBILENET_LAYERS_TO_UNFREEZE: int = 30
    MOBILENET_WARMUP_EPOCHS: int = 15
    MOBILENET_FINE_TUNE_EPOCHS: int = 25
    MOBILENET_EARLY_STOPPING_PATIENCE: int = 5

    ACTIVE_MODEL: str = os.getenv("ACTIVE_MODEL", "cifake_cnn").lower()
    MODEL_PATH_CNN: Path = MODEL_DIR / "cnn_model.keras"
    MODEL_PATH_MOBILENET: Path = MODEL_DIR / "mobilenet_model.keras"
    # Preferred export filename from Colab training (takes precedence over MODEL_PATH_MOBILENET)
    MODEL_PATH_MOBILENET_V2: Path = MODEL_DIR / "mobilenetv2.keras"

    # CIFAKE Real-vs-AI-Generated classification configuration
    CIFAKE_MODEL_DIR: Path = ARTIFACTS_DIR / "cifake" / "cifake_training_outputs" / "models"
    MODEL_PATH_CIFAKE_CNN: Path = CIFAKE_MODEL_DIR / "cifake_custom_cnn.keras"
    CIFAKE_MODEL_NAME: str = "cifake_cnn"
    HUGGINGFACE_MODEL_NAME: str = "huggingface_vit"
    HUGGINGFACE_MODEL_ID: str = "dima806/ai_vs_real_image_detection"
    HUGGINGFACE_MODEL_REVISION: str = "5d647683672ffd0080441f4e8b4345934c44cc61"
    HUGGINGFACE_FINETUNED_MODEL_DIR: Path = (
        ARTIFACTS_DIR / "cifake" / "ai_vs_real_finetuning_outputs" / "huggingface_vit"
    )
    CIFAKE_SUPPORTED_MODELS: tuple[str, ...] = (
        CIFAKE_MODEL_NAME,
        HUGGINGFACE_MODEL_NAME,
    )
    CIFAKE_MODEL_DISPLAY_NAMES: dict[str, str] = {
        CIFAKE_MODEL_NAME: "CIFAKE Custom CNN",
        HUGGINGFACE_MODEL_NAME: "Fine-tuned Hugging Face ViT",
    }
    CIFAKE_MODEL_PREPROCESSING: dict[str, str] = {
        CIFAKE_MODEL_NAME: "32x32 RGB, bilinear resize, pixel values scaled to [0, 1]",
        HUGGINGFACE_MODEL_NAME: (
            "224x224 RGB, resized and normalized by the Hugging Face image processor"
        ),
    }
    CIFAKE_MODEL_SCORE_TYPES: dict[str, str] = {
        CIFAKE_MODEL_NAME: "sigmoid",
        HUGGINGFACE_MODEL_NAME: "softmax",
    }
    CIFAKE_INPUT_SHAPE: Tuple[int, int, int] = (32, 32, 3)
    CIFAKE_TARGET_SIZE: Tuple[int, int] = (32, 32)
    CIFAKE_NORMALIZATION_MODE: str = "standard"
    HUGGINGFACE_INPUT_SHAPE: Tuple[int, int, int] = (224, 224, 3)
    HUGGINGFACE_TARGET_SIZE: Tuple[int, int] = (224, 224)
    HUGGINGFACE_LIMITATION_NOTICE: str = (
        "This ViT was fine-tuned on a Kaggle real-vs-AI image dataset. It scored 78.1% "
        "accuracy on a 146-image random held-out split from that dataset; this small "
        "same-source evaluation does not establish accuracy on unseen generators or "
        "arbitrary real-world images."
    )
    CIFAKE_CLASS_LABELS: dict[int, str] = {
        0: "Real photo",
        1: "AI-generated",
    }
    CIFAKE_LIMITATION_NOTICE: str = (
        "Limitation notice: This model was trained and evaluated on CIFAKE's 32x32 "
        "CIFAR-10-style photos and generated images (95.3% accuracy on CIFAKE's "
        "20,000-image held-out test set). Its performance on arbitrary real-world "
        "photos or images from other generators has not been established, and it "
        "should not be treated as a reliable universal AI-image detector."
    )
    CIFAKE_REPORT_TITLE: str = "CIFAKE AI-GENERATED VS. REAL IMAGE CLASSIFIER"
    CIFAKE_REPORT_SUBTITLE: str = "Automated Classification Summary Report"

    # Class definitions (retained for CASIA dataset/training scripts)
    CLASS_LABELS: dict[int, str] = {
        0: "Authentic",
        1: "Potentially Manipulated",
    }
    CLASSIFICATION_THRESHOLD: float = 0.5

    # -------------------------------------------------------------------------
    # Image Forensics & Error Level Analysis (ELA)
    # -------------------------------------------------------------------------
    ELA_MIN_QUALITY: int = 1
    ELA_MAX_QUALITY: int = 95
    ELA_QUALITY: int = 90
    ELA_ENHANCEMENT_FACTOR: float = 10.0
    ELA_DISCLAIMER: str = (
        "ELA visualization is an investigative aid. Bright regions in the ELA image indicate "
        "potential compression inconsistencies and do not constitute definitive "
        "proof of digital manipulation."
    )
    FORENSIC_REPORT_TITLE: str = "IMAGE MANIPULATION DETECTION SYSTEM"
    FORENSIC_REPORT_SUBTITLE: str = "Automated Preliminary Forensic Screening Report"
    FORENSIC_REPORT_DISCLAIMER: str = (
        "This report is generated by an automated deep-learning system for PRELIMINARY "
        "SCREENING purposes only. The prediction does not constitute professional forensic "
        "analysis or legal evidence. ELA visualization is an investigative aid and does "
        "not definitively prove or disprove image manipulation."
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
    LOG_FILE: Optional[Path] = ARTIFACTS_DIR / "app.log"
    ENABLE_FILE_LOGGING: bool = os.getenv("ENABLE_FILE_LOGGING", "0") == "1"

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
