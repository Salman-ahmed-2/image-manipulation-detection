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
from PIL import Image

from config import Config
from src.models.model_loader import MockFallbackModel, ModelLoader
from src.models.predictor import Predictor
from src.utils.exceptions import ModelInferenceError, ModelNotLoadedError


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


class DummyImageModel:
    """Image-native model stub returning a fixed AI-generated score."""

    def __init__(self, probability: float = 0.85) -> None:
        self.probability = probability
        self.received_image: Image.Image | None = None

    def predict_image(self, image: Image.Image) -> float:
        self.received_image = image
        return self.probability


@pytest.fixture(autouse=True)
def clean_model_cache():
    """Ensure clean model loader registry before and after each test."""
    ModelLoader.clear_cache()
    yield
    ModelLoader.clear_cache()


def test_model_loader_reports_missing_cifake_file_without_fallback(caplog, monkeypatch):
    """Test model loader records an explicit error and never registers a fallback."""
    missing_path = Path("/nonexistent/cifake_custom_cnn.keras")
    huggingface_load_calls = []

    def record_huggingface_load(cls):
        huggingface_load_calls.append(cls)

    monkeypatch.setattr(Config, "MODEL_PATH_CIFAKE_CNN", missing_path)
    monkeypatch.setattr(
        ModelLoader,
        "_load_huggingface_model",
        classmethod(record_huggingface_load),
    )
    with caplog.at_level(logging.ERROR):
        ModelLoader.load_all_models()

    assert huggingface_load_calls == [ModelLoader]
    assert ModelLoader.get_model(Config.CIFAKE_MODEL_NAME) is None
    assert ModelLoader.get_model("mobilenet") is None
    assert ModelLoader.is_fallback(Config.CIFAKE_MODEL_NAME) is False
    load_error = ModelLoader.get_load_error(Config.CIFAKE_MODEL_NAME)
    assert load_error is not None
    assert str(missing_path) in load_error

    error_logged = any(
        "not found" in record.message for record in caplog.records
    )
    assert error_logged is True

    predictor = Predictor(model_name=Config.CIFAKE_MODEL_NAME)
    with pytest.raises(ModelNotLoadedError, match="not found"):
        predictor.predict(np.zeros((1, *Config.CIFAKE_INPUT_SHAPE), dtype=np.float32))


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


@pytest.mark.parametrize(
    "prob,expected_code,expected_label",
    [
        (0.85, 1, "AI-generated"),
        (0.50, 1, "AI-generated"),
        (0.49, 0, "Real photo"),
        (0.00, 0, "Real photo"),
        (1.00, 1, "AI-generated"),
    ],
)
def test_cifake_class_label_mapping_and_32x32_input(prob, expected_code, expected_label):
    """Test CIFAKE label mapping (0=Real photo, 1=AI-generated) with 32x32 RGB input."""
    dummy_model = DummyModel(probability=prob)
    predictor = Predictor(model_name=Config.CIFAKE_MODEL_NAME, model=dummy_model)

    synthetic_input = np.zeros((1, *Config.CIFAKE_INPUT_SHAPE), dtype=np.float32)
    result = predictor.predict(synthetic_input)

    assert result["verdict_code"] == expected_code
    assert result["verdict_label"] == expected_label
    assert result["raw_probability"] == pytest.approx(prob)
    assert result["model_used"] == Config.CIFAKE_MODEL_NAME


def test_cifake_rejects_non_32x32_tensor():
    """Test CIFAKE predictor rejects tensors that do not match 32x32x3."""
    predictor = Predictor(model_name=Config.CIFAKE_MODEL_NAME, model=DummyModel())
    with pytest.raises(ValueError, match="Expected spatial dimensions"):
        predictor.predict(np.zeros((1, 224, 224, 3), dtype=np.float32))


@pytest.mark.parametrize(
    "prob,expected_code,expected_label",
    [
        (0.85, 1, "AI-generated"),
        (0.49, 0, "Real photo"),
    ],
)
def test_huggingface_prediction_uses_ai_class_score(
    prob: float,
    expected_code: int,
    expected_label: str,
) -> None:
    """Map the Hugging Face FAKE score into the app's shared class labels."""
    model = DummyImageModel(probability=prob)
    predictor = Predictor(model_name=Config.HUGGINGFACE_MODEL_NAME, model=model)
    image = Image.new("RGB", (640, 480), color="blue")

    result = predictor.predict_image(image)

    assert model.received_image is image
    assert result["raw_probability"] == pytest.approx(prob)
    assert result["verdict_code"] == expected_code
    assert result["verdict_label"] == expected_label
    assert result["model_used"] == Config.HUGGINGFACE_MODEL_NAME


def test_huggingface_prediction_wraps_inference_errors() -> None:
    """Convert model-specific image inference failures to a domain exception."""

    class BrokenImageModel:
        """Raise an error while processing the source image."""

        def predict_image(self, image: Image.Image) -> float:
            del image
            raise RuntimeError("processor unavailable")

    predictor = Predictor(
        model_name=Config.HUGGINGFACE_MODEL_NAME,
        model=BrokenImageModel(),
    )

    with pytest.raises(ModelInferenceError, match="Model image inference failed"):
        predictor.predict_image(Image.new("RGB", (32, 32)))


def test_mock_fallback_model_behavior():
    """Test MockFallbackModel produces valid probability array."""
    fallback = MockFallbackModel("cnn")
    tensor = np.zeros((2, 224, 224, 3), dtype=np.float32)

    pred = fallback.predict(tensor)
    assert pred.shape == (2, 1)
    assert np.all(pred == 0.50)

    call_pred = fallback(tensor)
    assert call_pred.shape == (2, 1)
