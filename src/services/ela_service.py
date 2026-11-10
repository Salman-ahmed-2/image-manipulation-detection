"""Service wrapper for generating and persisting ELA visualizations."""

from __future__ import annotations

from pathlib import Path

from werkzeug.utils import secure_filename

from config import Config
from src.preprocessing.ela_generator import ELAGenerator
from src.utils.exceptions import ValidationError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ELAService:
    """Generate ELA visualizations and manage their session-scoped output path."""

    def generate_and_save(
        self,
        image_path: Path,
        session_id: str,
        quality: int = Config.ELA_QUALITY,
    ) -> Path:
        """Generate an ELA visualization and save it under the upload session.

        Args:
            image_path: Path to the source image.
            session_id: Safe session identifier used for the output directory.
            quality: JPEG recompression quality. Defaults to ``Config.ELA_QUALITY``.

        Returns:
            The path to the saved ELA PNG.

        Raises:
            ValidationError: If the session identifier is not safe.
            OSError: If the source image cannot be read or output cannot be saved.
            ValueError: If the ELA quality is invalid.
        """
        safe_session_id = secure_filename(session_id)
        if not safe_session_id or safe_session_id != session_id:
            raise ValidationError("Invalid ELA session identifier.")

        output_directory = Path(Config.UPLOAD_FOLDER) / safe_session_id
        output_path = output_directory / "ela_result.png"
        output_directory.mkdir(parents=True, exist_ok=True)

        try:
            ELAGenerator.generate(
                image_path,
                output_path=output_path,
                quality=quality,
            )
        except (OSError, TypeError, ValueError) as error:
            logger.error("ELA generation failed for session %s: %s", session_id, error)
            raise

        logger.info("Saved ELA visualization for session %s.", session_id)
        return output_path
