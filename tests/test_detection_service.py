"""Unit tests for end-to-end detection service orchestration."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import numpy as np
import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage

from config import Config
from src.services import detection_service
from src.services.detection_service import DetectionService
from src.utils.exceptions import CorruptImageError, ModelInferenceError, ValidationError


class StubPredictor:
    """Return a deterministic result while recording the inference tensor."""

    def __init__(self, model_name: str) -> None:
        """Initialize a stub predictor for a named model.

        Args:
            model_name: Model identifier reported in the prediction result.
        """
        self.model_name = model_name
        self.tensor: np.ndarray | None = None

    def predict(self, tensor: np.ndarray) -> dict[str, Any]:
        """Record the tensor and return a stable prediction.

        Args:
            tensor: Batched, normalized image tensor.

        Returns:
            Prediction fields consumed by ``DetectionService``.
        """
        self.tensor = tensor
        return {
            "raw_probability": 0.942,
            "verdict_code": 1,
            "verdict_label": "Potentially Manipulated",
            "confidence": 94.2,
            "model_used": self.model_name,
        }


def _upload(image_format: str = "JPEG", filename: str = "photo.jpg") -> FileStorage:
    """Create an in-memory upload containing a synthetic RGB image.

    Args:
        image_format: Image encoding format used for the fixture.
        filename: Filename presented by the upload object.

    Returns:
        A Werkzeug file storage object positioned at the start of its stream.
    """
    buffer = io.BytesIO()
    Image.new("RGB", (18, 12), color=(30, 80, 120)).save(buffer, format=image_format)
    buffer.seek(0)
    return FileStorage(stream=buffer, filename=filename)


def test_detection_service_initializes_with_active_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Construct the default service without eagerly loading model weights."""
    predictor = Mock()
    monkeypatch.setattr(detection_service, "Predictor", predictor)

    service = DetectionService()

    assert service.model_name == Config.ACTIVE_MODEL
    predictor.assert_called_once_with(model_name=Config.ACTIVE_MODEL)


def test_analyze_image_returns_prediction_paths_and_disclaimer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run the full pipeline on a synthetic upload and aggregate all result fields."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    predictors: list[StubPredictor] = []

    def create_predictor(model_name: str) -> StubPredictor:
        """Create and record a deterministic predictor.

        Args:
            model_name: Identifier selected for this analysis.

        Returns:
            The predictor stub used by the service.
        """
        predictor = StubPredictor(model_name)
        predictors.append(predictor)
        return predictor

    monkeypatch.setattr(detection_service, "Predictor", create_predictor)
    service = DetectionService(model_name="cnn")
    upload = _upload()

    result = service.analyze_image(upload, "session-123", model_choice="mobilenet")

    original_path = Path(result["original_image_path"])
    ela_path = Path(result["ela_image_path"])
    assert original_path.parent == tmp_path / "session-123"
    assert original_path.name.endswith("_orig.jpg")
    assert original_path.is_file()
    assert ela_path == tmp_path / "session-123" / "ela_result.png"
    assert ela_path.is_file()
    assert result["session_id"] == "session-123"
    assert result["original_filename"] == "photo.jpg"
    assert result["verdict_label"] == "Potentially Manipulated"
    assert result["verdict_code"] == 1
    assert result["confidence"] == 94.2
    assert result["raw_probability"] == 0.942
    assert result["model_used"] == "mobilenet"
    assert result["disclaimer"] == Config.ELA_DISCLAIMER
    assert result["timestamp"]
    assert len(predictors) == 2
    assert predictors[-1].tensor is not None
    assert predictors[-1].tensor.shape == (1, *Config.INPUT_SHAPE)
    assert predictors[-1].tensor.min() >= -1.0
    assert predictors[-1].tensor.max() <= 1.0


def test_analyze_image_rejects_invalid_upload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Surface validation failures and do not produce analysis artifacts."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    service = DetectionService(model_name="cnn")

    with pytest.raises(ValidationError, match="extension"):
        service.analyze_image(_upload(filename="document.pdf"), "session-123")

    assert not (tmp_path / "session-123").exists()


def test_analyze_image_surfaces_corrupt_image_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Surface corrupt-image domain errors raised by upload validation."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    service = DetectionService(model_name="cnn")
    corrupt_upload = FileStorage(
        stream=io.BytesIO(b"\xff\xd8\xff" + b"invalid image data"),
        filename="corrupt.jpg",
    )

    with pytest.raises(CorruptImageError, match="corrupt"):
        service.analyze_image(corrupt_upload, "session-123")


def test_analyze_image_surfaces_model_inference_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Preserve domain inference errors for the caller to handle."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    predictor = Mock()
    predictor.predict.side_effect = ModelInferenceError("Inference unavailable.")
    monkeypatch.setattr(detection_service, "Predictor", Mock(return_value=predictor))
    service = DetectionService(model_name="cnn")

    with pytest.raises(ModelInferenceError, match="Inference unavailable"):
        service.analyze_image(_upload(), "session-123")
