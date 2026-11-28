"""Orchestrate upload validation, Stage 1 metadata filter, and model inference."""

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
from src.utils.image_metadata import (
    Stage1Result,
    analyze_metadata,
    inspect_image_metadata,
)
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

        Flow:
        1. Validate and save the upload securely.
        2. Run Stage 1 (metadata / provenance filter, < 100 ms).
        3. If Stage 1 short-circuits (``route_to_stage2 = False``), return
           immediately with the metadata verdict.
        4. Otherwise run Stage 2 (ML classifier) and merge Stage 1 evidence.

        Args:
            file_storage: Uploaded image payload, such as Werkzeug ``FileStorage``.
            session_id: Session identifier used to isolate temporary artifacts.
            model_choice: Optional inference model override (must be supported).

        Returns:
            A dictionary containing the verdict, optional model score, paths,
            metadata assessment, Stage 1 evidence, and limitation notice.

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

            # --- Stage 1: Metadata & Provenance Filter -----------------------
            stage1 = analyze_metadata(original_path)
            metadata = inspect_image_metadata(original_path)

            # Short-circuit: trusted C2PA AI-origin or strong metadata signal
            if metadata.has_trusted_ai_claim:
                # Verified C2PA provenance — skip ML entirely
                prediction = {
                    "raw_probability": None,
                    "verdict_code": 1,
                    "verdict_label": Config.CIFAKE_CLASS_LABELS[1],
                    "confidence": None,
                    "model_used": None,
                }
                classification_source = "verified_c2pa"
            elif not stage1.route_to_stage2 and stage1.status == "ai_detected":
                # Strong metadata signal (e.g. generation chunks), no ML needed
                prediction = {
                    "raw_probability": None,
                    "verdict_code": 1,
                    "verdict_label": Config.CIFAKE_CLASS_LABELS[1],
                    "confidence": None,
                    "model_used": None,
                }
                classification_source = "metadata"
            else:
                # --- Stage 2: ML Classifier ----------------------------------
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
                classification_source = "model"

        except (CorruptImageError, ModelInferenceError, ValidationError) as error:
            logger.error("Image analysis failed for session %s: %s", session_id, error)
            raise
        except OSError as error:
            logger.error("Image analysis I/O failed for session %s: %s", session_id, error)
            raise

        provenance_verified = metadata.has_trusted_ai_claim
        metadata_shortcircuit = classification_source == "metadata"

        if provenance_verified:
            disclaimer = Config.C2PA_PROVENANCE_NOTICE
        elif metadata_shortcircuit:
            disclaimer = Config.STAGE1_METADATA_NOTICE
        elif selected_model == Config.HUGGINGFACE_MODEL_NAME:
            disclaimer = Config.HUGGINGFACE_LIMITATION_NOTICE
        else:
            disclaimer = Config.CIFAKE_LIMITATION_NOTICE

        if provenance_verified:
            display_name = "Trusted C2PA Content Credentials"
            preprocessing_desc = (
                "Classification based on a trusted C2PA AI-origin assertion; "
                "ML inference skipped"
            )
        elif metadata_shortcircuit:
            display_name = f"Stage 1 Metadata ({stage1.generator or 'detected'})"
            preprocessing_desc = (
                "AI signature found in file metadata; ML inference skipped"
            )
        else:
            display_name = Config.CIFAKE_MODEL_DISPLAY_NAMES[selected_model]
            preprocessing_desc = Config.CIFAKE_MODEL_PREPROCESSING[selected_model]

        return {
            "session_id": session_id,
            "verdict_label": prediction["verdict_label"],
            "verdict_code": prediction["verdict_code"],
            "confidence": prediction["confidence"],
            "raw_probability": prediction["raw_probability"],
            "model_used": prediction["model_used"],
            "model_display_name": display_name,
            "preprocessing_description": preprocessing_desc,
            "score_type": (
                None
                if provenance_verified or metadata_shortcircuit
                else Config.CIFAKE_MODEL_SCORE_TYPES[selected_model]
            ),
            "classification_source": classification_source,
            "metadata_assessment": {
                "c2pa_validation_state": metadata.c2pa_validation_state,
                "has_trusted_ai_claim": metadata.has_trusted_ai_claim,
                "metadata_clues": list(metadata.metadata_clues),
            },
            "stage1_result": stage1.to_dict(),
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
