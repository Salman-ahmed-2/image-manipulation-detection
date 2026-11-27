"""Orchestrate upload validation, CIFAKE preprocessing, and model inference."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Optional

from PIL import Image

from config import Config
from src.models.predictor import Predictor
from src.preprocessing.image_loader import load_image
from src.preprocessing.image_normalizer import prepare_tensor
from src.utils.exceptions import CorruptImageError, ModelInferenceError, ValidationError
from src.utils.file_validator import save_upload_securely
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DetectionService:
    """Coordinate secure image ingestion and CIFAKE real-vs-AI classification."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        """Initialize the service with the configured CIFAKE predictor.

        Args:
            model_name: Model identifier to use by default. Defaults to
                ``Config.ACTIVE_MODEL``.
        """
        self.model_name = (model_name or Config.ACTIVE_MODEL).lower()
        self.predictor = Predictor(model_name=self.model_name)

    def analyze_image(
        self,
        file_storage: Any,
        session_id: str,
        model_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Classify an uploaded image as Real photo or AI-generated.

        Args:
            file_storage: Uploaded image payload, such as Werkzeug ``FileStorage``.
            session_id: Session identifier used to isolate temporary artifacts.
            model_choice: Optional inference model override (must be supported).

        Returns:
            A dictionary containing verdict, raw sigmoid score, paths, metadata,
            and the CIFAKE limitation notice.

        Raises:
            ValidationError: If the upload or selected model is invalid.
            ModelInferenceError: If the model is missing or inference fails.
            OSError: If an image artifact cannot be saved.
        """
        started_at = perf_counter()
        selected_model = (model_choice or self.model_name).lower()
        if selected_model not in Config.CIFAKE_SUPPORTED_MODELS:
            raise ValidationError(f"Unsupported model choice: {selected_model}.")

        original_filename = getattr(file_storage, "filename", None)
        try:
            saved_path = save_upload_securely(file_storage, session_id)
            original_path = self._rename_original(saved_path)
            image = load_image(original_path)
            predictor = (
                self.predictor
                if selected_model == self.model_name
                else Predictor(model_name=selected_model)
            )
            if selected_model == Config.HUGGINGFACE_MODEL_NAME:
                prediction = predictor.predict_image(image)
            else:
                tensor = prepare_tensor(
                    image,
                    target_size=Config.CIFAKE_TARGET_SIZE,
                    mode=Config.CIFAKE_NORMALIZATION_MODE,
                    resample=Image.Resampling.BILINEAR,
                )
                prediction = predictor.predict(tensor)
        except (CorruptImageError, ModelInferenceError, ValidationError) as error:
            logger.error("Image analysis failed for session %s: %s", session_id, error)
            raise
        except OSError as error:
            logger.error("Image analysis I/O failed for session %s: %s", session_id, error)
            raise

        disclaimer = (
            Config.HUGGINGFACE_LIMITATION_NOTICE
            if selected_model == Config.HUGGINGFACE_MODEL_NAME
            else Config.CIFAKE_LIMITATION_NOTICE
        )
        return {
            "session_id": session_id,
            "verdict_label": prediction["verdict_label"],
            "verdict_code": prediction["verdict_code"],
            "confidence": prediction["confidence"],
            "raw_probability": prediction["raw_probability"],
            "model_used": prediction["model_used"],
            "model_display_name": Config.CIFAKE_MODEL_DISPLAY_NAMES[selected_model],
            "preprocessing_description": Config.CIFAKE_MODEL_PREPROCESSING[selected_model],
            "score_type": Config.CIFAKE_MODEL_SCORE_TYPES[selected_model],
            "image_dimensions": image.size,
            "input_colorspace": image.mode,
            "latency_ms": (perf_counter() - started_at) * 1000,
            "original_image_path": str(original_path),
            "original_filename": original_filename,
            "disclaimer": disclaimer,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _rename_original(saved_path: Path) -> Path:
        """Rename a securely saved upload to the session artifact naming format.

        Args:
            saved_path: Path returned by ``save_upload_securely``.

        Returns:
            The original image path ending in ``_orig`` and its validated extension.
        """
        unique_id = saved_path.name.partition("_")[0]
        original_path = saved_path.with_name(
            f"{unique_id}_orig{saved_path.suffix.lower()}"
        )
        saved_path.rename(original_path)
        return original_path
