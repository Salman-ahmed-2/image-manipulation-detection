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
from src.utils.image_metadata import MetadataAssessment


class StubPredictor:
    """Return a deterministic result while recording the inference tensor."""

    def __init__(self, model_name: str) -> None:
        """Initialize a stub predictor for a named model.

        Args:
            model_name: Model identifier reported in the prediction result.
        """
        self.model_name = model_name
        self.tensor: np.ndarray | None = None
        self.image: Image.Image | None = None

    def predict(self, tensor: np.ndarray) -> dict[str, Any]:
        """Record the tensor and return a stable CIFAKE prediction.

        Args:
            tensor: Batched, normalized image tensor.

        Returns:
            Prediction fields consumed by ``DetectionService``.
        """
        self.tensor = tensor
        return {
            "raw_probability": 0.942,
            "verdict_code": 1,
            "verdict_label": "AI-generated",
            "confidence": 94.2,
            "model_used": self.model_name,
        }

    def predict_image(self, image: Image.Image) -> dict[str, Any]:
        """Record a source image and return a stable Hugging Face model result."""
        self.image = image
        return {
            "raw_probability": 0.81,
            "verdict_code": 1,
            "verdict_label": "AI-generated",
            "confidence": 81.0,
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


def test_analyze_image_returns_prediction_paths_and_limitation_notice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run the CIFAKE pipeline on a synthetic upload without ELA artifacts."""
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
    service = DetectionService()
    upload = _upload()

    result = service.analyze_image(upload, "session-123")

    original_path = Path(result["original_image_path"])
    assert original_path.parent == tmp_path / "session-123"
    assert original_path.name.endswith("_orig.jpg")
    assert original_path.is_file()
    assert "ela_image_path" not in result
    assert not (tmp_path / "session-123" / "ela_result.png").exists()
    assert result["session_id"] == "session-123"
    assert result["original_filename"] == "photo.jpg"
    assert result["verdict_label"] == "AI-generated"
    assert result["verdict_code"] == 1
    assert result["raw_probability"] == 0.942
    assert result["model_used"] == Config.CIFAKE_MODEL_NAME
    assert result["image_dimensions"] == (18, 12)
    assert result["input_colorspace"] == "RGB"
    assert result["latency_ms"] >= 0
    assert result["disclaimer"] == Config.CIFAKE_LIMITATION_NOTICE
    assert result["timestamp"]
    assert "stage1_result" in result
    assert result["stage1_result"]["status"] == "no_signal"
    assert len(predictors) == 1
    assert predictors[-1].tensor is not None
    assert predictors[-1].tensor.shape == (1, *Config.CIFAKE_INPUT_SHAPE)
    assert predictors[-1].tensor.dtype == np.float32
    assert predictors[-1].tensor.min() >= 0.0
    assert predictors[-1].tensor.max() <= 1.0


def test_analyze_image_rejects_unsupported_model_choice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject CASIA/MobileNet model names when only CIFAKE Custom CNN is enabled."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    service = DetectionService()

    with pytest.raises(ValidationError, match="Unsupported model choice"):
        service.analyze_image(_upload(), "session-123", model_choice="mobilenet")


def test_analyze_image_uses_huggingface_processor_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pass the original decoded image to the Hugging Face processor path."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    predictors: list[StubPredictor] = []

    def create_predictor(model_name: str) -> StubPredictor:
        predictor = StubPredictor(model_name)
        predictors.append(predictor)
        return predictor

    monkeypatch.setattr(detection_service, "Predictor", create_predictor)
    result = DetectionService(model_name=Config.HUGGINGFACE_MODEL_NAME).analyze_image(
        _upload(),
        "session-hf",
        model_choice=Config.HUGGINGFACE_MODEL_NAME,
    )

    assert len(predictors) == 1
    assert predictors[0].tensor is None
    assert predictors[0].image is not None
    assert predictors[0].image.mode == "RGB"
    assert predictors[0].image.size == (18, 12)
    assert result["raw_probability"] == 0.81
    assert result["model_display_name"] == Config.CIFAKE_MODEL_DISPLAY_NAMES[
        Config.HUGGINGFACE_MODEL_NAME
    ]
    assert result["preprocessing_description"] == Config.CIFAKE_MODEL_PREPROCESSING[
        Config.HUGGINGFACE_MODEL_NAME
    ]
    assert result["disclaimer"] == Config.HUGGINGFACE_LIMITATION_NOTICE


def test_trusted_c2pa_ai_claim_skips_model_inference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A trusted AI-origin claim produces a provenance result without a model score."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    predictors: list[StubPredictor] = []

    def create_predictor(model_name: str) -> StubPredictor:
        predictor = StubPredictor(model_name)
        predictors.append(predictor)
        return predictor

    monkeypatch.setattr(detection_service, "Predictor", create_predictor)
    monkeypatch.setattr(
        detection_service,
        "inspect_image_metadata",
        lambda path: MetadataAssessment("Trusted", True, ()),
    )

    result = DetectionService().analyze_image(_upload(), "session-c2pa")

    assert result["verdict_label"] == "AI-generated"
    assert result["classification_source"] == "verified_c2pa"
    assert result["raw_probability"] is None
    assert result["model_used"] is None
    assert result["metadata_assessment"]["c2pa_validation_state"] == "Trusted"
    assert predictors[0].tensor is None
    assert predictors[0].image is None


def test_untrusted_c2pa_claim_still_runs_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A valid but untrusted claim and EXIF clues do not bypass model inference."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    predictors: list[StubPredictor] = []

    def create_predictor(model_name: str) -> StubPredictor:
        predictor = StubPredictor(model_name)
        predictors.append(predictor)
        return predictor

    monkeypatch.setattr(detection_service, "Predictor", create_predictor)
    monkeypatch.setattr(
        detection_service,
        "inspect_image_metadata",
        lambda path: MetadataAssessment(
            "Valid",
            False,
            ("Metadata mentions ComfyUI (unverified).",),
        ),
    )

    result = DetectionService().analyze_image(_upload(), "session-untrusted-c2pa")

    assert result["classification_source"] == "model"
    assert result["raw_probability"] == 0.942
    assert result["metadata_assessment"]["metadata_clues"] == [
        "Metadata mentions ComfyUI (unverified)."
    ]
    assert predictors[0].tensor is not None


def test_analyze_image_rejects_invalid_upload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Surface validation failures and do not produce analysis artifacts."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    service = DetectionService()

    with pytest.raises(ValidationError, match="extension"):
        service.analyze_image(_upload(filename="document.pdf"), "session-123")

    assert not (tmp_path / "session-123").exists()


def test_analyze_image_surfaces_corrupt_image_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Surface corrupt-image domain errors raised by upload validation."""
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    service = DetectionService()
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
    service = DetectionService()

    with pytest.raises(ModelInferenceError, match="Inference unavailable"):
        service.analyze_image(_upload(), "session-123")


def test_stage1_strong_metadata_shortcircuits_model_inference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Strong PNG generation metadata skips Stage 2 ML inference."""
    from PIL import PngImagePlugin

    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    predictors: list[StubPredictor] = []

    def create_predictor(model_name: str) -> StubPredictor:
        predictor = StubPredictor(model_name)
        predictors.append(predictor)
        return predictor

    monkeypatch.setattr(detection_service, "Predictor", create_predictor)

    buffer = io.BytesIO()
    png_info = PngImagePlugin.PngInfo()
    png_info.add_text("parameters", "Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 123")
    Image.new("RGB", (18, 12), color=(30, 80, 120)).save(buffer, format="PNG", pnginfo=png_info)
    buffer.seek(0)
    upload = FileStorage(stream=buffer, filename="sd.png")

    result = DetectionService().analyze_image(upload, "session-stage1")

    assert result["classification_source"] == "metadata"
    assert result["verdict_label"] == "AI-generated"
    assert result["raw_probability"] is None
    assert result["model_used"] is None
    assert result["disclaimer"] == Config.STAGE1_METADATA_NOTICE
    assert result["stage1_result"]["route_to_stage2"] is False
    assert predictors[0].tensor is None
    assert predictors[0].image is None
