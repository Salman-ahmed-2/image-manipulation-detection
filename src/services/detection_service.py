"""Orchestrate upload validation, image inference, and ELA generation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Optional

from config import Config
from src.models.predictor import Predictor
from src.preprocessing.image_loader import load_image
from src.preprocessing.image_normalizer import prepare_tensor
from src.services.ela_service import ELAService
from src.utils.exceptions import CorruptImageError, ModelInferenceError, ValidationError
from src.utils.file_validator import save_upload_securely
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DetectionService:
    """Coordinate secure image ingestion, prediction, and ELA analysis."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        """Initialize the service with a predictor and ELA service.

        Args:
            model_name: Model identifier to use by default. Defaults to
                ``Config.ACTIVE_MODEL``.
        """
        self.model_name = (model_name or Config.ACTIVE_MODEL).lower()
        self.predictor = Predictor(model_name=self.model_name)
        self.ela_service = ELAService()

    def analyze_image(
        self,
        file_storage: Any,
        session_id: str,
        model_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze an uploaded image and return presentation-ready results.

        Args:
            file_storage: Uploaded image payload, such as Werkzeug ``FileStorage``.
            session_id: Session identifier used to isolate temporary artifacts.
            model_choice: Optional inference model override.

        Returns:
            A dictionary containing verdict, confidence, paths, metadata, and the
            mandatory ELA disclaimer.

        Raises:
            ValidationError: If the upload or selected model is invalid.
            ModelInferenceError: If model inference fails.
            OSError: If an image artifact cannot be saved.
        """
        started_at = perf_counter()
        selected_model = (model_choice or self.model_name).lower()
        supported_models = {
            choice for choice in Config.EVALUATION_MODEL_CHOICES if choice != "both"
        }
        if selected_model not in supported_models:
            raise ValidationError(f"Unsupported model choice: {selected_model}.")

        original_filename = getattr(file_storage, "filename", None)
        try:
            saved_path = save_upload_securely(file_storage, session_id)
            original_path = self._rename_original(saved_path)
            image = load_image(original_path)
            tensor = (
                prepare_tensor(
                    image,
                    target_size=Config.TARGET_SIZE,
                    mode=Config.MOBILENET_NORMALIZATION_MODE,
                )
                if selected_model == "mobilenet"
                else prepare_tensor(image, target_size=Config.TARGET_SIZE)
            )

            predictor = (
                self.predictor
                if selected_model == self.model_name
                else Predictor(model_name=selected_model)
            )
            prediction = predictor.predict(tensor)
            ela_path = self.ela_service.generate_and_save(
                original_path,
                session_id,
                quality=Config.ELA_QUALITY,
            )
        except (CorruptImageError, ModelInferenceError, ValidationError) as error:
            logger.error("Image analysis failed for session %s: %s", session_id, error)
            raise
        except OSError as error:
            logger.error("Image analysis I/O failed for session %s: %s", session_id, error)
            raise

        return {
            "session_id": session_id,
            "verdict_label": prediction["verdict_label"],
            "verdict_code": prediction["verdict_code"],
            "confidence": prediction["confidence"],
            "raw_probability": prediction["raw_probability"],
            "model_used": prediction["model_used"],
            "image_dimensions": image.size,
            "input_colorspace": image.mode,
            "latency_ms": (perf_counter() - started_at) * 1000,
            "original_image_path": str(original_path),
            "ela_image_path": str(ela_path),
            "original_filename": original_filename,
            "disclaimer": Config.ELA_DISCLAIMER,
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
