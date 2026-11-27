"""Pytest configuration and shared fixtures for Image Manipulation Detection System."""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from typing import Iterator
from unittest.mock import Mock

import pytest
from flask import Flask
from flask.testing import FlaskClient
from PIL import Image

# Ensure project root is present in Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from config import Config
from src.models.model_loader import MockFallbackModel, ModelLoader
from src.models.predictor import Predictor


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Flask]:
    """Create an isolated Flask application with CPU-only fallback models.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory unique to the current test.

    Yields:
        A Flask application configured for testing.
    """
    upload_folder = tmp_path / "uploads"
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", upload_folder)

    def register_test_models() -> None:
        """Register a lightweight callable model without loading trained weights."""

        class _TestCIFAKEModel:
            """Deterministic 32x32 test model stub."""

            def predict(self, tensor, verbose: int = 0):  # noqa: ANN001, ANN202
                import numpy as np

                del verbose
                batch_size = tensor.shape[0] if getattr(tensor, "ndim", 0) == 4 else 1
                return np.full((batch_size, 1), 0.25, dtype=np.float32)

        ModelLoader.register_model(Config.CIFAKE_MODEL_NAME, _TestCIFAKEModel())

        class _TestHuggingFaceModel:
            """Deterministic image-native test model stub."""

            def predict_image(self, image):  # noqa: ANN001, ANN201
                del image
                return 0.75

        ModelLoader.register_model(
            Config.HUGGINGFACE_MODEL_NAME,
            _TestHuggingFaceModel(),
        )

    monkeypatch.setattr(ModelLoader, "load_all_models", register_test_models)
    ModelLoader.clear_cache()
    test_app = create_app(Config)
    test_app.config.update(
        TESTING=True,
        MAX_CONTENT_LENGTH=Config.MAX_CONTENT_LENGTH,
    )
    yield test_app
    ModelLoader.clear_cache()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Return a Flask test client for the isolated application.

    Args:
        app: Flask application fixture.

    Returns:
        A test client bound to the application.
    """
    return app.test_client()


@pytest.fixture
def synthetic_jpeg_bytes() -> bytes:
    """Create an in-memory 100-by-100 RGB JPEG image.

    Returns:
        Encoded JPEG image bytes.
    """
    image = Image.new("RGB", (100, 100), color=(80, 120, 160))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def synthetic_png_bytes() -> bytes:
    """Create an in-memory 100-by-100 RGB PNG image.

    Returns:
        Encoded PNG image bytes.
    """
    image = Image.new("RGB", (100, 100), color=(80, 120, 160))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def synthetic_corrupt_bytes() -> bytes:
    """Provide invalid image data resembling a disguised executable payload.

    Returns:
        Bytes that do not match a supported image signature.
    """
    return b"MZ\x90\x00synthetic executable payload"


@pytest.fixture
def synthetic_oversized_bytes() -> bytes:
    """Create a payload one byte larger than the configured upload limit.

    Returns:
        An oversized byte string for HTTP size-limit tests.
    """
    return b"\x00" * (Config.MAX_CONTENT_LENGTH + 1)


@pytest.fixture
def mock_predictor(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Replace neural inference with a deterministic result for integration tests.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        A mock callable installed as ``Predictor.predict``.
    """
    predictor = Mock(
        return_value={
            "raw_probability": 0.934,
            "verdict_code": 1,
            "verdict_label": "AI-generated",
            "confidence": 93.4,
            "model_used": Config.CIFAKE_MODEL_NAME,
        }
    )
    monkeypatch.setattr(Predictor, "predict", predictor)
    return predictor
