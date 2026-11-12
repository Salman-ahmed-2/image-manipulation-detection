"""Blueprint for image analysis, report, and temporary-image routes."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    render_template,
    request,
    Response,
    send_from_directory,
    session,
    url_for,
)

from config import Config
from src.services.detection_service import DetectionService
from src.services.report_service import ReportService
from src.utils.exceptions import (
    PayloadTooLargeError,
    ReportGenerationError,
    ValidationError,
)
from src.utils.file_validator import cleanup_session_directory
from src.utils.logger import get_logger

logger = get_logger(__name__)
detection_bp = Blueprint("detection", __name__)


def _accepts_json() -> bool:
    """Determine whether JSON is the client's preferred response format.

    Returns:
        True when JSON is the best matching response type.
    """
    return request.accept_mimetypes.best == "application/json"


def _error_response(message: str, status_code: int, error_code: str) -> Any:
    """Return an analysis error in the format requested by the client.

    Args:
        message: Human-readable error detail.
        status_code: HTTP status for the response.
        error_code: Machine-readable error identifier.

    Returns:
        A JSON error response or a rendered HTTP error page.
    """
    if _accepts_json():
        return (
            jsonify(
                {
                    "status": "error",
                    "error_code": error_code,
                    "message": message,
                    "code": status_code,
                }
            ),
            status_code,
        )
    abort(status_code)


@detection_bp.post("/analyze")
def analyze() -> Any:
    """Analyze the uploaded image and return HTML or JSON results.

    Returns:
        A rendered results page, JSON analysis response, or error response.
    """
    uploaded_file = request.files.get("image")
    if uploaded_file is None or not uploaded_file.filename:
        return _error_response("No file selected.", 400, "INVALID_FILE")

    session_id = session.get("session_id") or str(uuid4())
    model_choice = request.form.get("model") or Config.ACTIVE_MODEL

    try:
        result = DetectionService().analyze_image(
            uploaded_file,
            session_id,
            model_choice,
        )
    except PayloadTooLargeError as error:
        logger.warning("Upload rejected because it exceeds the configured limit.")
        return _error_response(str(error), 413, "PAYLOAD_TOO_LARGE")
    except ValidationError as error:
        logger.warning("Invalid image upload: %s", error)
        return _error_response(str(error), 400, "INVALID_FILE_TYPE")

    session["session_id"] = session_id
    session["analysis_result"] = result

    original_image_url = url_for(
        "detection.serve_session_image",
        session_id=session_id,
        filename=Path(result["original_image_path"]).name,
    )
    ela_image_url = url_for(
        "detection.serve_session_image",
        session_id=session_id,
        filename=Path(result["ela_image_path"]).name,
    )
    response_data = {
        "status": "success",
        "session_id": session_id,
        "prediction": {
            "label": result["verdict_label"],
            "verdict_code": result["verdict_code"],
            "confidence": result["confidence"],
            "raw_probability": result["raw_probability"],
            "model_used": result["model_used"],
        },
        "artifacts": {
            "original_image_url": original_image_url,
            "ela_image_url": ela_image_url,
        },
        "disclaimer": result["disclaimer"],
    }
    if _accepts_json():
        return jsonify(response_data)

    template_context = {
        **result,
        "prediction": result["verdict_label"],
        "confidence_pct": int(result["confidence"]),
        "model_used": result["model_used"],
        "original_image_url": original_image_url,
        "ela_image_url": ela_image_url,
        "session_id": session_id,
    }
    return render_template("result.html", **template_context)


@detection_bp.get("/report/<session_id>")
def download_report(session_id: str) -> Any:
    """Generate and return the PDF report for the current browser session.

    Args:
        session_id: Identifier for the completed analysis.

    Returns:
        A downloadable PDF response, or a not-found/internal error response.
    """
    analysis_result = session.get("analysis_result")
    if (
        session.get("session_id") != session_id
        or not isinstance(analysis_result, dict)
        or not analysis_result
    ):
        abort(404)

    try:
        pdf_bytes = ReportService.generate_pdf_report(
            analysis_result,
            Path(analysis_result["original_image_path"]),
            Path(analysis_result["ela_image_path"]),
        )
    except (KeyError, ReportGenerationError) as error:
        logger.error("Unable to create report for session %s: %s", session_id, error)
        abort(500)

    cleanup_session_directory(session_id)
    session.pop("session_id", None)
    session.pop("analysis_result", None)

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=forensic_report_{session_id}.pdf"
        },
    )


@detection_bp.get("/static/temp/<session_id>/<filename>")
def serve_session_image(session_id: str, filename: str) -> Any:
    """Serve an image generated for the current browser session.

    Args:
        session_id: Session-scoped directory identifier.
        filename: Image artifact basename.

    Returns:
        The requested image file.
    """
    analysis_result = session.get("analysis_result", {})
    if session.get("session_id") != session_id or not isinstance(analysis_result, dict):
        abort(404)

    allowed_filenames = {
        Path(analysis_result[key]).name
        for key in ("original_image_path", "ela_image_path")
        if isinstance(analysis_result.get(key), str)
    }
    if filename not in allowed_filenames:
        abort(404)

    directory = Path(current_app.config.get("UPLOAD_FOLDER", Config.UPLOAD_FOLDER))
    return send_from_directory(directory / session_id, filename)
