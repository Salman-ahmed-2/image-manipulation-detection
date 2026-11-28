"""Compile CIFAKE classification results into an in-memory PDF report."""

from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.errors import FPDFException
from PIL import Image

from config import Config
from src.utils.exceptions import ReportGenerationError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReportService:
    """Generate downloadable CIFAKE classification summary reports."""

    @staticmethod
    def generate_pdf_report(
        results_data: Dict[str, Any],
        original_image_path: Path,
        ela_image_path: Optional[Path] = None,
    ) -> bytes:
        """Compile an analysis session into an in-memory PDF document.

        Args:
            results_data: Analysis metadata dictionary from DetectionService.
            original_image_path: Filesystem path to the ingested original photo.
            ela_image_path: Unused legacy parameter kept for signature compatibility.

        Returns:
            Binary bytes representing the compiled PDF document.

        Raises:
            ReportGenerationError: If report metadata, image, or PDF generation fail.
        """
        del ela_image_path
        try:
            verdict = str(results_data["verdict_label"])
            raw_probability_value = results_data.get("raw_probability")
            raw_probability = (
                float(raw_probability_value)
                if raw_probability_value is not None
                else None
            )
            supported_verdicts = tuple(Config.CIFAKE_CLASS_LABELS.values())
            if verdict not in supported_verdicts:
                raise ValueError(f"Unsupported report verdict: {verdict}.")
            if raw_probability is not None and (
                not isfinite(raw_probability) or not 0.0 <= raw_probability <= 1.0
            ):
                raise ValueError("Model score must be a finite probability from 0 to 1.")

            model_used = str(results_data.get("model_used") or "verified_c2pa")
            model_display_name = str(
                results_data.get("model_display_name")
                or Config.CIFAKE_MODEL_DISPLAY_NAMES.get(model_used, model_used)
            )
            preprocessing_description = str(
                results_data.get("preprocessing_description")
                or Config.CIFAKE_MODEL_PREPROCESSING.get(
                    model_used, "Model-specific preprocessing"
                )
            )
            score_type = results_data.get("score_type") or Config.CIFAKE_MODEL_SCORE_TYPES.get(
                model_used, "model"
            )
            classification_source = str(results_data.get("classification_source", "model"))
            metadata_assessment = results_data.get("metadata_assessment", {})
            metadata_clues = metadata_assessment.get("metadata_clues", [])
            if not isinstance(metadata_clues, list):
                raise ValueError("Metadata clues must be provided as a list.")
            limitation_notice = str(
                results_data.get("disclaimer", Config.CIFAKE_LIMITATION_NOTICE)
            )
            timestamp = str(
                results_data.get("timestamp") or datetime.now(timezone.utc).isoformat()
            )
            original_path = Path(original_image_path)
            with Image.open(original_path) as original_image:
                original_size = original_image.size
                original_channels = len(original_image.getbands())

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=10)
            pdf.add_page()
            page_width = pdf.w - 20

            pdf.set_font("Helvetica", "B", 15)
            pdf.cell(
                0,
                8,
                Config.CIFAKE_REPORT_TITLE,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(
                0,
                6,
                Config.CIFAKE_REPORT_SUBTITLE,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(
                0, 5, f"Report UUID: {uuid4()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT
            )
            pdf.cell(
                0, 5, f"Generated: {timestamp}", new_x=XPos.LMARGIN, new_y=YPos.NEXT
            )
            pdf.ln(3)

            is_real = verdict == Config.CIFAKE_CLASS_LABELS[0]
            verdict_color = (35, 100, 55) if is_real else (150, 35, 35)
            pdf.set_fill_color(242, 245, 248)
            summary_y = pdf.get_y()
            summary_height = 30 if raw_probability is None else 24
            pdf.rect(10, summary_y, page_width, summary_height, style="F")
            pdf.set_xy(14, summary_y + 3)
            pdf.set_text_color(*verdict_color)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(
                page_width - 8,
                7,
                f"Prediction: {verdict}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.set_x(14)
            pdf.set_font("Helvetica", "B", 10)
            if raw_probability is not None:
                pdf.cell(
                    page_width - 8,
                    7,
                    f"AI-generated score ({score_type}): {raw_probability:.4f}",
                )
            else:
                pdf.cell(
                    page_width - 8,
                    7,
                    "Decision basis: Trusted C2PA AI-origin assertion",
                )
            pdf.set_text_color(0, 0, 0)
            pdf.set_xy(10, summary_y + (34 if raw_probability is None else 28))

            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, "UPLOADED IMAGE", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            card_y = pdf.get_y()
            card_height = 77
            pdf.set_draw_color(170, 175, 180)
            pdf.rect(10, card_y, page_width, card_height)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_xy(12, card_y + 2)
            pdf.cell(page_width - 4, 5, "Original Uploaded Image", align="C")

            image_top = card_y + 9
            image_bottom = card_y + card_height - 3
            image_box_width = page_width - 8
            image_box_height = image_bottom - image_top
            scale = min(
                image_box_width / original_size[0],
                image_box_height / original_size[1],
            )
            image_width = original_size[0] * scale
            image_height = original_size[1] * scale
            image_x = 14 + (image_box_width - image_width) / 2
            image_y = image_top + (image_box_height - image_height) / 2
            pdf.image(
                str(original_path),
                x=image_x,
                y=image_y,
                w=image_width,
                h=image_height,
            )
            pdf.set_y(card_y + card_height + 4)

            input_size_mb = original_path.stat().st_size / (1024 * 1024)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(
                0, 7, "TECHNICAL METADATA", new_x=XPos.LMARGIN, new_y=YPos.NEXT
            )
            pdf.set_font("Helvetica", "", 9)
            metadata = (
                f"Original dimensions: {original_size[0]} x {original_size[1]} px",
                f"Color channels: {original_channels}",
                f"Input size: {input_size_mb:.2f} MB",
                f"Model used: {model_display_name}",
                f"Classification source: {classification_source}",
                f"Preprocessing: {preprocessing_description}",
                *(
                    (
                        f"Score type: {score_type}",
                        f"Decision threshold: {Config.CLASSIFICATION_THRESHOLD}",
                    )
                    if raw_probability is not None
                    else ()
                ),
                "C2PA validation state: "
                f"{metadata_assessment.get('c2pa_validation_state', 'unknown')}",
                "Unverified metadata clues: "
                + ("; ".join(metadata_clues) or "None found"),
            )
            for item in metadata:
                pdf.multi_cell(
                    0, 5, item, new_x=XPos.LMARGIN, new_y=YPos.NEXT
                )
            pdf.ln(3)

            disclaimer_y = pdf.get_y()
            disclaimer_height = 35
            if disclaimer_y + disclaimer_height > pdf.h - 10:
                pdf.add_page()
                disclaimer_y = pdf.get_y()
            pdf.set_fill_color(242, 242, 242)
            pdf.set_draw_color(170, 35, 35)
            pdf.rect(10, disclaimer_y, page_width, disclaimer_height, style="DF")
            pdf.set_xy(13, disclaimer_y + 3)
            pdf.set_text_color(130, 25, 25)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(
                page_width - 6,
                5,
                "LIMITATION NOTICE",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.set_xy(13, disclaimer_y + 9)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(page_width - 6, 4, limitation_notice)
            pdf.set_text_color(0, 0, 0)

            return bytes(pdf.output())
        except (KeyError, OSError, TypeError, ValueError, FPDFException) as error:
            logger.error("Classification PDF report generation failed: %s", error)
            raise ReportGenerationError(
                f"Unable to generate classification PDF report: {error}"
            ) from error