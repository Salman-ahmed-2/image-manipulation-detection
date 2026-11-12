"""Compile preliminary forensic analysis results into an in-memory PDF report."""

from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
from typing import Any, Dict
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
    """Generate downloadable forensic screening reports."""

    @staticmethod
    def generate_pdf_report(
        results_data: Dict[str, Any],
        original_image_path: Path,
        ela_image_path: Path,
    ) -> bytes:
        """Compile an analysis session into an in-memory PDF document.

        Args:
            results_data: Analysis metadata dictionary from DetectionService.
            original_image_path: Filesystem path to the ingested original photo.
            ela_image_path: Filesystem path to the generated ELA visualization map.

        Returns:
            Binary bytes representing the compiled PDF document.

        Raises:
            ReportGenerationError: If report metadata, images, or PDF generation fail.
        """
        try:
            verdict = str(results_data["verdict_label"])
            confidence = float(results_data["confidence"])
            supported_verdicts = (
                Config.AUTHENTIC_LABEL_NAME,
                Config.CLASS_LABELS[Config.MANIPULATED_LABEL],
            )
            if verdict not in supported_verdicts:
                raise ValueError(f"Unsupported report verdict: {verdict}.")
            if not isfinite(confidence) or not 0.0 <= confidence <= 100.0:
                raise ValueError("Report confidence must be a finite percentage from 0 to 100.")

            model_used = str(results_data["model_used"])
            timestamp = str(
                results_data.get("timestamp") or datetime.now(timezone.utc).isoformat()
            )
            original_path = Path(original_image_path)
            ela_path = Path(ela_image_path)
            with Image.open(original_path) as original_image:
                original_size = original_image.size
                original_channels = len(original_image.getbands())
            with Image.open(ela_path) as ela_image:
                ela_size = ela_image.size
                ela_image.verify()

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=10)
            pdf.add_page()
            page_width = pdf.w - 20

            pdf.set_font("Helvetica", "B", 15)
            pdf.cell(
                0,
                8,
                Config.FORENSIC_REPORT_TITLE,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(
                0,
                6,
                Config.FORENSIC_REPORT_SUBTITLE,
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

            is_authentic = verdict == Config.AUTHENTIC_LABEL_NAME
            display_verdict = (
                Config.AUTHENTIC_LABEL_NAME
                if is_authentic
                else Config.CLASS_LABELS[Config.MANIPULATED_LABEL]
            )
            verdict_color = (35, 100, 55) if is_authentic else (150, 35, 35)
            pdf.set_fill_color(242, 245, 248)
            summary_y = pdf.get_y()
            pdf.rect(10, summary_y, page_width, 22, style="F")
            pdf.set_xy(14, summary_y + 3)
            pdf.set_text_color(*verdict_color)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(
                page_width - 8,
                7,
                f"Verdict: {display_verdict}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.set_x(14)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(page_width - 8, 7, f"Confidence: {confidence:.2f}%")
            pdf.set_text_color(0, 0, 0)
            pdf.set_y(summary_y + 26)

            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, "VISUAL EVIDENCE", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            gap = 6
            card_width = (page_width - gap) / 2
            card_y = pdf.get_y()
            card_height = 77
            pdf.set_draw_color(170, 175, 180)
            pdf.rect(10, card_y, card_width, card_height)
            pdf.rect(10 + card_width + gap, card_y, card_width, card_height)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_xy(12, card_y + 2)
            pdf.cell(card_width - 4, 5, "Original Uploaded Image", align="C")
            pdf.set_xy(12 + card_width + gap, card_y + 2)
            pdf.cell(
                card_width - 4,
                5,
                f"Enhanced Error Level Analysis (ELA) - {Config.ELA_ENHANCEMENT_FACTOR:g}x Scale",
                align="C",
            )

            image_top = card_y + 9
            image_bottom = card_y + card_height - 3
            image_box_width = card_width - 8
            image_box_height = image_bottom - image_top
            for image_path, image_size, x in (
                (original_path, original_size, 14),
                (ela_path, ela_size, 14 + card_width + gap),
            ):
                scale = min(
                    image_box_width / image_size[0],
                    image_box_height / image_size[1],
                )
                image_width = image_size[0] * scale
                image_height = image_size[1] * scale
                image_x = x + (image_box_width - image_width) / 2
                image_y = image_top + (image_box_height - image_height) / 2
                pdf.image(
                    str(image_path),
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
                f"Model used: {model_used}",
                f"ELA quality factor: {Config.ELA_QUALITY}",
                f"ELA visualization scale: {Config.ELA_ENHANCEMENT_FACTOR:g}x",
            )
            for item in metadata:
                pdf.cell(0, 5, item, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(3)

            disclaimer_y = pdf.get_y()
            disclaimer_height = 31
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
                "MANDATORY FORENSIC DISCLAIMER",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.set_xy(13, disclaimer_y + 9)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(page_width - 6, 4, Config.FORENSIC_REPORT_DISCLAIMER)
            pdf.set_text_color(0, 0, 0)

            return bytes(pdf.output())
        except (KeyError, OSError, TypeError, ValueError, FPDFException) as error:
            logger.error("Forensic PDF report generation failed: %s", error)
            raise ReportGenerationError(
                f"Unable to generate forensic PDF report: {error}"
            ) from error