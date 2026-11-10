"""Predictor engine executing forward passes and computing calibrated confidence metrics.

Translates raw neural network Sigmoid probability outputs into human-interpretable
authenticity verdicts and calibrated confidence percentages.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import numpy as np

from config import Config
from src.models.model_loader import ModelLoader
from src.utils.exceptions import ModelInferenceError, ModelNotLoadedError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Predictor:
    """Inference engine executing model predictions and computing confidence metrics."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        model: Optional[Any] = None,
    ) -> None:
        """Initialize the predictor.

        Args:
            model_name: Identifier for the model architecture ('cnn' or 'mobilenet').
                Defaults to Config.ACTIVE_MODEL.
            model: Optional direct model instance for overriding or testing.
        """
        self.model_name = (model_name or Config.ACTIVE_MODEL).lower()
        self._model = model

    @property
    def model(self) -> Any:
        """Retrieve the active model instance, loading if necessary.

        Returns:
            The loaded model instance.

        Raises:
            ModelNotLoadedError: If the model cannot be retrieved or loaded.
        """
        if self._model is not None:
            return self._model

        loaded_model = ModelLoader.get_model(self.model_name)
        if loaded_model is None:
            # Attempt to initialize models in memory
            logger.info(
                "Model '%s' not cached. Invoking ModelLoader.load_all_models().",
                self.model_name,
            )
            ModelLoader.load_all_models()
            loaded_model = ModelLoader.get_model(self.model_name)

        if loaded_model is None:
            raise ModelNotLoadedError(
                f"Model '{self.model_name}' could not be loaded into memory."
            )

        return loaded_model

    def predict(self, preprocessed_tensor: np.ndarray) -> Dict[str, Any]:
        """Execute model prediction and compute calibrated confidence metrics.

        Args:
            preprocessed_tensor: 4D numpy array with shape (1, 224, 224, 3)
                or 3D array (224, 224, 3).

        Returns:
            dict with keys:
                'raw_probability': float (0.0 to 1.0)
                'verdict_code': int (0 for Authentic, 1 for Manipulated)
                'verdict_label': str ("Authentic" or "Potentially Manipulated")
                'confidence': float (percentage 50.0 to 100.0)
                'model_used': str

        Raises:
            ValueError: If input tensor has invalid dimensions or type.
            ModelInferenceError: If forward pass execution fails.
        """
        if not isinstance(preprocessed_tensor, np.ndarray):
            raise ValueError(
                f"Expected numpy.ndarray input, received: {type(preprocessed_tensor).__name__}"
            )

        # Allow 3D tensor by expanding batch dimension
        if preprocessed_tensor.ndim == 3:
            if preprocessed_tensor.shape != Config.INPUT_SHAPE:
                raise ValueError(
                    f"Expected 3D tensor of shape {Config.INPUT_SHAPE}, "
                    f"received shape: {preprocessed_tensor.shape}"
                )
            preprocessed_tensor = np.expand_dims(preprocessed_tensor, axis=0)

        if preprocessed_tensor.ndim != 4:
            raise ValueError(
                f"Expected 4D tensor with shape (N, {Config.INPUT_SHAPE[0]}, "
                f"{Config.INPUT_SHAPE[1]}, {Config.INPUT_SHAPE[2]}), "
                f"received shape: {preprocessed_tensor.shape}"
            )

        if preprocessed_tensor.shape[1:] != Config.INPUT_SHAPE:
            raise ValueError(
                f"Expected spatial dimensions {Config.INPUT_SHAPE}, "
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

        except Exception as exc:
            if isinstance(exc, (ValueError, ModelInferenceError)):
                raise
            logger.error("Inference execution failed on model '%s': %s", self.model_name, exc)
            raise ModelInferenceError(f"Model forward pass failed: {exc}") from exc

        # Clamp raw probability to [0.0, 1.0] boundary
        prob = max(0.0, min(1.0, raw_prob))

        # Confidence Computation Logic:
        # P >= 0.5 -> Manipulated (code 1), confidence = P * 100
        # P < 0.5  -> Authentic (code 0), confidence = (1.0 - P) * 100
        if prob >= Config.CLASSIFICATION_THRESHOLD:
            verdict_code = 1
            verdict_label = Config.CLASS_LABELS.get(1, "Potentially Manipulated")
            confidence = round(float(prob) * 100.0, 2)
        else:
            verdict_code = 0
            verdict_label = Config.CLASS_LABELS.get(0, "Authentic")
            confidence = round(float(1.0 - prob) * 100.0, 2)

        return {
            "raw_probability": prob,
            "verdict_code": verdict_code,
            "verdict_label": verdict_label,
            "confidence": confidence,
            "model_used": self.model_name,
        }
