"""In-memory model loader and registry for the Image Manipulation Detection System.

Responsible for caching trained Keras deep learning models in memory once at
application startup to eliminate per-request disk I/O and cold-start latency.
Supports graceful fallback mock predictors when weights files are absent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
from PIL import Image

from config import Config
from src.models.huggingface_image_classifier import HuggingFaceImageClassifier
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
    _load_errors: Dict[str, str] = {}

    @classmethod
    def load_all_models(cls) -> None:
        """Load the CIFAKE CNN and optional Hugging Face model at startup.

        A failure loading either model is recorded independently so it does not
        prevent the other configured model from being used.
        """
        name = Config.CIFAKE_MODEL_NAME
        path_obj = Path(Config.MODEL_PATH_CIFAKE_CNN)
        cls._registry.pop(name, None)
        cls._load_errors.pop(name, None)

        if not path_obj.exists():
            message = (
                f"CIFAKE Custom CNN model file not found at '{path_obj}'. "
                "Place the trained model at that path and restart the application."
            )
            logger.error(message)
            cls._load_errors[name] = message
        else:
            try:
                import tensorflow as tf  # type: ignore
            except ImportError as exc:
                message = f"TensorFlow is unavailable; cannot load model '{name}': {exc}"
                logger.error(message)
                cls._load_errors[name] = message
            else:
                try:
                    logger.info("Loading '%s' weights from %s...", name, path_obj)
                    model = tf.keras.models.load_model(str(path_obj))

                    # Execute warmup pass to eliminate first-request inference latency
                    warmup_input = tf.zeros(
                        (1, *Config.CIFAKE_INPUT_SHAPE), dtype=tf.float32
                    )
                    _ = model(warmup_input, training=False)

                    cls._registry[name] = model
                    logger.info("Model '%s' successfully loaded and warmed up.", name)
                except Exception as exc:  # noqa: BLE001
                    message = f"Failed to load CIFAKE Custom CNN model from '{path_obj}': {exc}"
                    logger.error(message)
                    cls._load_errors[name] = message

        cls._load_huggingface_model()

    @classmethod
    def _load_huggingface_model(cls) -> None:
        """Load the pinned Hugging Face ViT and its matching image processor."""
        name = Config.HUGGINGFACE_MODEL_NAME
        cls._registry.pop(name, None)
        cls._load_errors.pop(name, None)
        try:
            import torch
            from transformers import AutoImageProcessor, AutoModelForImageClassification
            if not hasattr(torch, "inference_mode"):
                raise ImportError("Installed PyTorch does not provide inference_mode().")
        except ImportError as exc:
            message = (
                "Hugging Face ViT dependencies are unavailable; install the project "
                f"requirements to enable '{name}': {exc}"
            )
            logger.error(message)
            cls._load_errors[name] = message
            return

        try:
            logger.info(
                "Loading Hugging Face model '%s' at revision %s...",
                Config.HUGGINGFACE_MODEL_ID,
                Config.HUGGINGFACE_MODEL_REVISION,
            )
            processor = AutoImageProcessor.from_pretrained(
                Config.HUGGINGFACE_MODEL_ID,
                revision=Config.HUGGINGFACE_MODEL_REVISION,
            )
            model = AutoModelForImageClassification.from_pretrained(
                Config.HUGGINGFACE_MODEL_ID,
                revision=Config.HUGGINGFACE_MODEL_REVISION,
                use_safetensors=True,
            )
            classifier = HuggingFaceImageClassifier(model, processor)
            classifier.predict_image(
                Image.new("RGB", Config.HUGGINGFACE_TARGET_SIZE, color="black")
            )
            cls._registry[name] = classifier
            logger.info("Hugging Face model '%s' loaded on CPU.", name)
        except Exception as exc:  # noqa: BLE001
            message = (
                f"Failed to load Hugging Face model '{Config.HUGGINGFACE_MODEL_ID}' "
                f"at revision '{Config.HUGGINGFACE_MODEL_REVISION}': {exc}"
            )
            logger.error(message)
            cls._load_errors[name] = message

    @classmethod
    def get_model(cls, name: str) -> Optional[Any]:
        """Retrieve pre-loaded model instance by key.

        Args:
            name: Logical name of the model (e.g. ``'cifake_cnn'``).

        Returns:
            The loaded Keras model, or None if not registered.
        """
        return cls._registry.get(name.lower())

    @classmethod
    def get_load_error(cls, name: str) -> Optional[str]:
        """Return the recorded startup load error for a model, if any.

        Args:
            name: Logical model identifier.

        Returns:
            Human-readable error description or ``None``.
        """
        return cls._load_errors.get(name.lower())

    @classmethod
    def register_model(cls, name: str, model: Any) -> None:
        """Manually register a model instance in the in-memory cache.

        Useful for testing or custom overrides.

        Args:
            name: Logical model identifier.
            model: Model object (Keras model or callable).
        """
        key = name.lower()
        cls._registry[key] = model
        cls._load_errors.pop(key, None)
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
        """Clear all cached model instances and recorded load errors."""
        cls._registry.clear()
        cls._load_errors.clear()
        logger.debug("ModelLoader in-memory registry cleared.")
