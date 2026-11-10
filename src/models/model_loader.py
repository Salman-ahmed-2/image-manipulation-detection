"""In-memory model loader and registry for the Image Manipulation Detection System.

Responsible for caching trained Keras deep learning models in memory once at
application startup to eliminate per-request disk I/O and cold-start latency.
Supports graceful fallback mock predictors when weights files are absent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np

from config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MockFallbackModel:
    """Lightweight fallback model registered when trained weights are missing.

    Ensures the application, unit tests, and UI dashboards remain functional
    even prior to full model training.
    """

    def __init__(self, model_name: str = "fallback") -> None:
        """Initialize mock fallback model.

        Args:
            model_name: Identifier for the model being mocked.
        """
        self.model_name = model_name

    def predict(self, tensor: np.ndarray, verbose: int = 0) -> np.ndarray:
        """Simulate model forward pass returning neutral probability output.

        Args:
            tensor: Input tensor matching expected batch shape (N, 224, 224, 3).
            verbose: Ignored; maintains interface compatibility with Keras.

        Returns:
            np.ndarray: Predicted probabilities of shape (N, 1) with values in [0.0, 1.0].
        """
        batch_size = tensor.shape[0] if getattr(tensor, "ndim", 0) == 4 else 1
        # Default to neutral baseline probability (0.50)
        return np.full((batch_size, 1), 0.50, dtype=np.float32)

    def __call__(self, tensor: Any, training: bool = False) -> Any:
        """Allow model to be invoked as a callable function.

        Args:
            tensor: Input tensor.
            training: Flag indicating training vs. inference mode.

        Returns:
            np.ndarray: Simulated forward pass output.
        """
        return self.predict(tensor)


class ModelLoader:
    """Thread-safe in-memory cache and registry for deep learning models."""

    _registry: Dict[str, Any] = {}

    @classmethod
    def load_all_models(cls) -> None:
        """Check Config.MODEL_DIR and load all configured models into memory.

        Scans for cnn_model.keras and mobilenet_model.keras. If present, loads
        and executes a dummy warmup pass using tf.zeros((1, 224, 224, 3)) to build
        the computation graph. If absent or if TensorFlow is unavailable, logs
        a warning and registers a lightweight mock fallback model.
        """
        models_to_load = {
            "cnn": Config.MODEL_PATH_CNN,
            "mobilenet": Config.MODEL_PATH_MOBILENET,
        }

        # Attempt to import TensorFlow lazily
        tf_module = None
        try:
            import tensorflow as tf  # type: ignore

            tf_module = tf
        except ImportError:
            logger.warning(
                "TensorFlow is not installed in the current environment. "
                "Registering mock fallback predictors for all models."
            )

        for name, path in models_to_load.items():
            path_obj = Path(path)
            if tf_module is not None and path_obj.exists():
                try:
                    logger.info("Loading '%s' weights from %s...", name, path_obj)
                    model = tf_module.keras.models.load_model(str(path_obj))

                    # Execute warmup pass to eliminate first-request inference latency
                    warmup_input = tf_module.zeros((1, 224, 224, 3), dtype=tf_module.float32)
                    _ = model(warmup_input, training=False)

                    cls._registry[name] = model
                    logger.info("Model '%s' successfully loaded and warmed up.", name)
                    continue
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Failed to load model '%s' from %s: %s. Using fallback.",
                        name,
                        path_obj,
                        exc,
                    )

            # Register fallback predictor if file does not exist or failed to load
            logger.warning(
                "Model file for '%s' not found at %s. Registering fallback mock model.",
                name,
                path_obj,
            )
            cls._registry[name] = MockFallbackModel(model_name=name)

    @classmethod
    def get_model(cls, name: str) -> Optional[Any]:
        """Retrieve pre-loaded model instance by key.

        Args:
            name: Logical name of the model ('cnn' or 'mobilenet').

        Returns:
            The loaded Keras model or fallback predictor, or None if not registered.
        """
        return cls._registry.get(name.lower())

    @classmethod
    def register_model(cls, name: str, model: Any) -> None:
        """Manually register a model instance in the in-memory cache.

        Useful for testing, custom mocks, or dynamic fine-tuning experiments.

        Args:
            name: Logical model identifier.
            model: Model object (Keras model, mock, or callable).
        """
        cls._registry[name.lower()] = model
        logger.info("Model '%s' manually registered in ModelLoader cache.", name)

    @classmethod
    def is_fallback(cls, name: str) -> bool:
        """Check whether the loaded model for a key is a fallback mock.

        Args:
            name: Logical model identifier.

        Returns:
            bool: True if model is an instance of MockFallbackModel, False otherwise.
        """
        model = cls.get_model(name)
        return isinstance(model, MockFallbackModel)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached model instances. Primarily used in test teardown."""
        cls._registry.clear()
        logger.debug("ModelLoader in-memory registry cleared.")
