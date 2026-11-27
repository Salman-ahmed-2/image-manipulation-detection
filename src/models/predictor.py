"""Predictor engine executing forward passes and computing calibrated confidence metrics.

Translates raw neural network Sigmoid probability outputs into human-interpretable
authenticity verdicts and calibrated confidence percentages.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import numpy as np
from PIL import Image

from config import Config
from src.models.model_loader import MockFallbackModel, ModelLoader
from src.utils.exceptions import ModelInferenceError, ModelNotLoadedError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Predictor:
    """Inference engine executing model predictions and computing model scores."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        model: Optional[Any] = None,
    ) -> None:
        """Initialize the predictor.

        Args:
            model_name: Identifier for the model architecture (e.g. ``'cifake_cnn'``).
                Defaults to ``Config.ACTIVE_MODEL``.
            model: Optional direct model instance for overriding or testing.
        """
        self.model_name = (model_name or Config.ACTIVE_MODEL).lower()
        self._model = model

    @property
    def _expected_input_shape(self) -> tuple[int, int, int]:
        """Return the expected spatial/channel shape for the configured model."""
        if self.model_name == Config.HUGGINGFACE_MODEL_NAME:
            return Config.HUGGINGFACE_INPUT_SHAPE
        if self.model_name == Config.CIFAKE_MODEL_NAME:
            return Config.CIFAKE_INPUT_SHAPE
        return Config.INPUT_SHAPE

    @property
    def _class_labels(self) -> dict[int, str]:
        """Return class label mapping for the configured model."""
        if self.model_name in Config.CIFAKE_SUPPORTED_MODELS:
            return Config.CIFAKE_CLASS_LABELS
        return Config.CLASS_LABELS

    @property
    def model(self) -> Any:
        """Retrieve the pre-loaded model instance without silent fallbacks.

        Returns:
            The loaded model instance.

        Raises:
            ModelNotLoadedError: If the model is missing or failed to load.
        """
        if self._model is not None:
            return self._model

        loaded_model = ModelLoader.get_model(self.model_name)
        if loaded_model is None:
            load_error = ModelLoader.get_load_error(self.model_name)
            if load_error is None:
                logger.info(
                    "Model '%s' not cached. Invoking ModelLoader.load_all_models().",
                    self.model_name,
                )
                ModelLoader.load_all_models()
                loaded_model = ModelLoader.get_model(self.model_name)
                load_error = ModelLoader.get_load_error(self.model_name)

            if loaded_model is None:
                raise ModelNotLoadedError(
                    load_error
                    or f"Model '{self.model_name}' is not loaded into memory."
                )

        if isinstance(loaded_model, MockFallbackModel):
            raise ModelNotLoadedError(
                f"Model '{self.model_name}' is unavailable; fallback predictions are disabled."
            )

        return loaded_model

    def predict(self, preprocessed_tensor: np.ndarray) -> Dict[str, Any]:
        """Execute model prediction and return the sigmoid score and class label.

        Args:
            preprocessed_tensor: 4D numpy array with shape ``(1, H, W, 3)``
                or 3D array ``(H, W, 3)``.

        Returns:
            dict with keys:
                'raw_probability': float (0.0 to 1.0, sigmoid score for AI-generated)
                'verdict_code': int (0 for Real photo, 1 for AI-generated)
                'verdict_label': str ("Real photo" or "AI-generated")
                'confidence': float (class score percentage 50.0 to 100.0)
                'model_used': str

        Raises:
            ValueError: If input tensor has invalid dimensions or type.
            ModelNotLoadedError: If the model is not loaded.
            ModelInferenceError: If forward pass execution fails.
        """
        if not isinstance(preprocessed_tensor, np.ndarray):
            raise ValueError(
                f"Expected numpy.ndarray input, received: {type(preprocessed_tensor).__name__}"
            )

        expected_shape = self._expected_input_shape

        # Allow 3D tensor by expanding batch dimension
        if preprocessed_tensor.ndim == 3:
            if preprocessed_tensor.shape != expected_shape:
                raise ValueError(
                    f"Expected 3D tensor of shape {expected_shape}, "
                    f"received shape: {preprocessed_tensor.shape}"
                )
            preprocessed_tensor = np.expand_dims(preprocessed_tensor, axis=0)

        if preprocessed_tensor.ndim != 4:
            raise ValueError(
                f"Expected 4D tensor with shape (N, {expected_shape[0]}, "
                f"{expected_shape[1]}, {expected_shape[2]}), "
                f"received shape: {preprocessed_tensor.shape}"
            )

        if preprocessed_tensor.shape[1:] != expected_shape:
            raise ValueError(
                f"Expected spatial dimensions {expected_shape}, "
                f"received {preprocessed_tensor.shape[1:]}"
            )

        active_model = self.model

        try:
            if hasattr(active_model, "predict"):
                raw_output = active_model.predict(preprocessed_tensor, verbose=0)
            elif callable(active_model):
                raw_output = active_model(preprocessed_tensor)
            else:
                raise ModelInferenceError(
                    f"Active model for '{self.model_name}' has no predict or call method."
                )

            # Convert output to scalar float
            if isinstance(raw_output, np.ndarray):
                raw_prob = float(raw_output.flat[0])
            elif hasattr(raw_output, "numpy"):
                raw_prob = float(raw_output.numpy().flat[0])
            else:
                raw_prob = float(raw_output)

            if not np.isfinite(raw_prob):
                raise ModelInferenceError("Model returned a non-finite probability.")

        except Exception as exc:
            if isinstance(exc, (ValueError, ModelInferenceError)):
                raise
            logger.error("Inference execution failed on model '%s': %s", self.model_name, exc)
            raise ModelInferenceError(f"Model forward pass failed: {exc}") from exc

        return self._format_prediction(raw_prob)

    def predict_image(self, image: Image.Image) -> Dict[str, Any]:
        """Run an image-native classifier using its own Hugging Face processor.

        Args:
            image: Source image in any Pillow-supported mode.

        Returns:
            The standard prediction result dictionary.

        Raises:
            ValueError: If image is not a Pillow image.
            ModelNotLoadedError: If the selected model is unavailable.
            ModelInferenceError: If image processing or inference fails.
        """
        if not isinstance(image, Image.Image):
            raise ValueError(f"Expected PIL Image input, received: {type(image).__name__}")

        active_model = self.model
        image_predictor = getattr(active_model, "predict_image", None)
        if not callable(image_predictor):
            raise ModelInferenceError(
                f"Active model '{self.model_name}' does not support image-native inference."
            )

        try:
            raw_prob = float(image_predictor(image))
            if not np.isfinite(raw_prob):
                raise ModelInferenceError("Model returned a non-finite probability.")
        except ModelInferenceError:
            raise
        except Exception as exc:
            logger.error("Image inference failed on model '%s': %s", self.model_name, exc)
            raise ModelInferenceError(f"Model image inference failed: {exc}") from exc

        return self._format_prediction(raw_prob)

    def _format_prediction(self, raw_probability: float) -> Dict[str, Any]:
        """Map the AI-generated score to the configured verdict and response.

        Args:
            raw_probability: Model score for the AI-generated class.

        Returns:
            Standardized prediction result fields.
        """
        prob = max(0.0, min(1.0, raw_probability))
        labels = self._class_labels

        if prob >= Config.CLASSIFICATION_THRESHOLD:
            verdict_code = 1
            verdict_label = labels.get(1, "AI-generated")
            confidence = round(float(prob) * 100.0, 2)
        else:
            verdict_code = 0
            verdict_label = labels.get(0, "Real photo")
            confidence = round(float(1.0 - prob) * 100.0, 2)

        return {
            "raw_probability": prob,
            "verdict_code": verdict_code,
            "verdict_label": verdict_label,
            "confidence": confidence,
            "model_used": self.model_name,
        }
