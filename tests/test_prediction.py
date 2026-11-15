"""Unit tests for ModelLoader and Predictor modules.

Verifies thread-safe in-memory caching, graceful fallback handling when weights
are missing, input tensor dimension validation, and calibrated confidence calculation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
import numpy as np
import pytest

from config import Config
from src.models.model_loader import MockFallbackModel, ModelLoader
from src.models.predictor import Predictor
from src.utils.exceptions import ModelInferenceError


class DummyModel:
    """Mock model that outputs a fixed predetermined probability."""

    def __init__(self, probability: float = 0.85) -> None:
        self.probability = probability

    def predict(self, tensor: np.ndarray, verbose: int = 0) -> np.ndarray:
        batch_size = tensor.shape[0] if tensor.ndim == 4 else 1
        return np.full((batch_size, 1), self.probability, dtype=np.float32)


class ErrorModel:
    """Mock model that raises an internal computation exception."""

    def predict(self, tensor: np.ndarray, verbose: int = 0) -> np.ndarray:
        raise RuntimeError("GPU Out of Memory simulated failure.")


@pytest.fixture(autouse=True)
def clean_model_cache():
    """Ensure clean model loader registry before and after each test."""
    ModelLoader.clear_cache()
    yield
    ModelLoader.clear_cache()


def test_model_loader_graceful_missing_files(caplog, monkeypatch):
    """Test model loader registers mock fallback when weights are missing."""
    monkeypatch.setattr(Config, "MODEL_PATH_CNN", Path("/nonexistent/cnn.keras"))
    monkeypatch.setattr(Config, "MODEL_PATH_MOBILENET", Path("/nonexistent/mobilenet.keras"))
    monkeypatch.setattr(Config, "MODEL_PATH_MOBILENET_V2", Path("/nonexistent/mobilenetv2.keras"))
    with caplog.at_level(logging.WARNING):
        ModelLoader.load_all_models()

    cnn_model = ModelLoader.get_model("cnn")
    mobilenet_model = ModelLoader.get_model("mobilenet")

    assert cnn_model is not None
    assert mobilenet_model is not None
    assert isinstance(cnn_model, MockFallbackModel)
    assert isinstance(mobilenet_model, MockFallbackModel)
    assert ModelLoader.is_fallback("cnn") is True
    assert ModelLoader.is_fallback("mobilenet") is True

    # Check that descriptive warning was logged
    warning_logged = any(
        "not found" in record.message or "Registering fallback" in record.message
        for record in caplog.records
    )
    assert warning_logged is True


def test_model_loader_caching_and_clear():
    """Test ModelLoader caches instances and clears registry properly."""
    dummy = DummyModel(0.7)
    ModelLoader.register_model("custom_test", dummy)

    retrieved = ModelLoader.get_model("custom_test")
    assert retrieved is dummy

    ModelLoader.clear_cache()
    assert ModelLoader.get_model("custom_test") is None


def test_prediction_returns_required_keys_and_types():
    """Test prediction dictionary contains all specified keys and correct data types."""
    dummy_model = DummyModel(probability=0.75)
    predictor = Predictor(model_name="cnn", model=dummy_model)

    synthetic_input = np.zeros((1, 224, 224, 3), dtype=np.float32)
    result = predictor.predict(synthetic_input)

    assert isinstance(result, dict)
    required_keys = {"raw_probability", "verdict_code", "verdict_label", "confidence", "model_used"}
    assert required_keys.issubset(result.keys())

    assert isinstance(result["raw_probability"], float)
    assert isinstance(result["verdict_code"], int)
    assert isinstance(result["verdict_label"], str)
    assert isinstance(result["confidence"], float)
    assert isinstance(result["model_used"], str)

    assert result["model_used"] == "cnn"
    assert result["verdict_code"] == 1
    assert result["verdict_label"] == "Potentially Manipulated"
    assert result["confidence"] == 75.0


@pytest.mark.parametrize(
    "prob,expected_code,expected_label,expected_conf",
    [
        (0.85, 1, "Potentially Manipulated", 85.0),
        (0.999, 1, "Potentially Manipulated", 99.9),
        (0.50, 1, "Potentially Manipulated", 50.0),
        (0.49, 0, "Authentic", 51.0),
        (0.20, 0, "Authentic", 80.0),
        (0.00, 0, "Authentic", 100.0),
        (1.00, 1, "Potentially Manipulated", 100.0),
    ],
)
def test_confidence_computation_and_bounds(prob, expected_code, expected_label, expected_conf):
    """Test confidence score calculation across boundary and normal intervals."""
    dummy_model = DummyModel(probability=prob)
    predictor = Predictor(model_name="mobilenet", model=dummy_model)

    synthetic_input = np.zeros((1, 224, 224, 3), dtype=np.float32)
    result = predictor.predict(synthetic_input)

    assert result["verdict_code"] == expected_code
    assert result["verdict_label"] == expected_label
    assert pytest.approx(result["confidence"], 0.01) == expected_conf

    # Confidence must strictly remain within [50.0, 100.0]
    assert 50.0 <= result["confidence"] <= 100.0


def test_prediction_with_3d_input_array():
    """Test predictor automatically handles 3D array by expanding batch dimension."""
    dummy_model = DummyModel(probability=0.30)
    predictor = Predictor(model_name="mobilenet", model=dummy_model)

    # 3D tensor of shape (224, 224, 3)
    synthetic_3d = np.zeros((224, 224, 3), dtype=np.float32)
    result = predictor.predict(synthetic_3d)

    assert result["verdict_code"] == 0
    assert result["verdict_label"] == "Authentic"
    assert result["confidence"] == 70.0


def test_prediction_invalid_input_type():
    """Test predictor raises ValueError when input is not a numpy array."""
    predictor = Predictor(model_name="mobilenet", model=DummyModel())
    with pytest.raises(ValueError, match="Expected numpy.ndarray input"):
        predictor.predict([[1, 2, 3]])  # type: ignore


def test_prediction_invalid_tensor_shape():
    """Test predictor raises ValueError when tensor dimensions do not match 224x224x3."""
    predictor = Predictor(model_name="mobilenet", model=DummyModel())

    # Invalid 3D shape
    with pytest.raises(ValueError, match="Expected 3D tensor of shape"):
        predictor.predict(np.zeros((100, 100, 3), dtype=np.float32))

    # Invalid 4D shape
    with pytest.raises(ValueError, match="Expected spatial dimensions"):
        predictor.predict(np.zeros((1, 100, 100, 3), dtype=np.float32))

    # Invalid 2D shape
    with pytest.raises(ValueError, match="Expected 4D tensor with shape"):
        predictor.predict(np.zeros((224, 224), dtype=np.float32))


def test_prediction_runtime_inference_error():
    """Test predictor converts internal model execution errors into ModelInferenceError."""
    error_model = ErrorModel()
    predictor = Predictor(model_name="mobilenet", model=error_model)

    synthetic_input = np.zeros((1, 224, 224, 3), dtype=np.float32)
    with pytest.raises(ModelInferenceError, match="Model forward pass failed"):
        predictor.predict(synthetic_input)


def test_mock_fallback_model_behavior():
    """Test MockFallbackModel produces valid probability array."""
    fallback = MockFallbackModel("cnn")
    tensor = np.zeros((2, 224, 224, 3), dtype=np.float32)

    pred = fallback.predict(tensor)
    assert pred.shape == (2, 1)
    assert np.all(pred == 0.50)

    call_pred = fallback(tensor)
    assert call_pred.shape == (2, 1)
