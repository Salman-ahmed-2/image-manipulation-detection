"""Integration tests for the Flask HTTP interface."""

from __future__ import annotations

import html
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import pytest
from flask import Flask, render_template
from flask.testing import FlaskClient

from config import Config
from src.services import detection_service
from src.utils.image_metadata import MetadataAssessment


def test_home_page_returns_ok(client: FlaskClient) -> None:
    """The home upload page is available."""
    response = client.get("/")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'id="dropZone"' in page
    assert 'name="image"' in page
    assert 'name="model"' in page
    assert f'data-max-file-size="{Config.MAX_CONTENT_LENGTH}"' in page
    assert "CIFAKE Custom CNN" in page
    assert "Hugging Face ViT" in page
    assert Config.CIFAKE_LIMITATION_NOTICE in html.unescape(page)
    assert 'css/style.css' in page
    assert 'js/main.js' in page


def test_navigating_home_cleans_the_active_session_directory(
    client: FlaskClient,
    synthetic_jpeg_bytes: bytes,
) -> None:
    """Returning home removes the current session's temporary image files."""
    analysis_response = client.post(
        "/analyze",
        data={"image": (BytesIO(synthetic_jpeg_bytes), "synthetic.jpg")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )
    session_id = analysis_response.get_json()["session_id"]
    session_directory = Path(Config.UPLOAD_FOLDER) / session_id
    assert session_directory.is_dir()

    response = client.get("/")

    assert response.status_code == 200
    assert not session_directory.exists()


def test_about_page_returns_ok(client: FlaskClient) -> None:
    """The about page is available."""
    response = client.get("/about")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "CIFAKE" in page
    assert "Hugging Face ViT" in page
    assert "95.3%" in page
    assert Config.CIFAKE_LIMITATION_NOTICE in html.unescape(page)
    assert Config.HUGGINGFACE_LIMITATION_NOTICE in html.unescape(page)
    assert "Error Level Analysis" not in page
    assert "Member 4" in page


def test_html_upload_error_renders_structured_error_page(client: FlaskClient) -> None:
    """A missing upload is explained on the user-facing error page."""
    response = client.post("/analyze", headers={"Accept": "text/html"})

    page = response.get_data(as_text=True)
    assert response.status_code == 400
    assert "Bad Request" in page
    assert "Return to Upload" in page


def test_health_returns_healthy_status(client: FlaskClient) -> None:
    """The health endpoint reports the application and CIFAKE model state."""
    response = client.get("/health")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "healthy"
    assert body["models_loaded"][Config.CIFAKE_MODEL_NAME] is True
    assert body["models_loaded"][Config.HUGGINGFACE_MODEL_NAME] is True
    assert body["active_model"] == Config.CIFAKE_MODEL_NAME


def test_analyze_without_file_returns_bad_request(client: FlaskClient) -> None:
    """An analysis request without an image is rejected."""
    response = client.post("/analyze", headers={"Accept": "application/json"})

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


def test_analyze_non_image_returns_bad_request(client: FlaskClient) -> None:
    """An upload with an unsupported file extension is rejected."""
    response = client.post(
        "/analyze",
        data={"image": (BytesIO(b"not an image"), "notes.txt")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 400
    assert response.get_json()["error_code"] == "INVALID_FILE_TYPE"


def test_analyze_valid_synthetic_image_returns_json(
    client: FlaskClient,
    synthetic_jpeg_bytes: bytes,
    mock_predictor: Mock,
) -> None:
    """A synthetic JPEG is classified and returned without ELA artifacts."""
    response = client.post(
        "/analyze",
        data={"image": (BytesIO(synthetic_jpeg_bytes), "synthetic.jpg")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )

    body = response.get_json()
    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["prediction"]["label"] == "AI-generated"
    assert body["prediction"]["model_score"] == 0.934
    assert body["prediction"]["raw_probability"] == 0.934
    assert body["prediction"]["model_used"] == Config.CIFAKE_MODEL_NAME
    assert body["artifacts"]["original_image_url"].startswith("/static/temp/")
    assert "ela_image_url" not in body["artifacts"]
    assert "stage1_result" in body
    assert body["stage1_result"]["status"] == "no_signal"
    assert body["limitation_notice"] == Config.CIFAKE_LIMITATION_NOTICE
    original_response = client.get(body["artifacts"]["original_image_url"])
    assert original_response.status_code == 200
    assert original_response.mimetype == "image/jpeg"
    mock_predictor.assert_called_once()


def test_trusted_c2pa_result_has_no_model_score(
    client: FlaskClient,
    synthetic_jpeg_bytes: bytes,
    mock_predictor: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return provenance evidence without inventing a model confidence score."""
    monkeypatch.setattr(
        detection_service,
        "inspect_image_metadata",
        lambda image_path: MetadataAssessment("Trusted", True, ()),
    )

    response = client.post(
        "/analyze",
        data={"image": (BytesIO(synthetic_jpeg_bytes), "synthetic.jpg")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )

    body = response.get_json()
    assert response.status_code == 200
    assert body["prediction"]["label"] == "AI-generated"
    assert body["prediction"]["classification_source"] == "verified_c2pa"
    assert body["prediction"]["raw_probability"] is None
    assert body["metadata_assessment"]["has_trusted_ai_claim"] is True
    assert body["limitation_notice"] == Config.C2PA_PROVENANCE_NOTICE
    mock_predictor.assert_not_called()


def test_trusted_c2pa_html_does_not_render_a_model_score(
    client: FlaskClient,
    synthetic_jpeg_bytes: bytes,
    mock_predictor: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Render a provenance-specific result without presenting a fake confidence."""
    monkeypatch.setattr(
        detection_service,
        "inspect_image_metadata",
        lambda image_path: MetadataAssessment("Trusted", True, ()),
    )

    response = client.post(
        "/analyze",
        data={"image": (BytesIO(synthetic_jpeg_bytes), "synthetic.jpg")},
        content_type="multipart/form-data",
        headers={"Accept": "text/html"},
    )

    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Verified provenance result" in page
    assert "C2PA Validation" in page
    assert "0.0000" not in page
    mock_predictor.assert_not_called()


def test_analyze_with_huggingface_model_returns_real_vs_ai_result(
    client: FlaskClient,
    synthetic_jpeg_bytes: bytes,
) -> None:
    """The second model returns a correctly labeled result and its own limitation."""
    response = client.post(
        "/analyze",
        data={
            "image": (BytesIO(synthetic_jpeg_bytes), "synthetic.jpg"),
            "model": Config.HUGGINGFACE_MODEL_NAME,
        },
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )

    body = response.get_json()
    assert response.status_code == 200
    assert body["prediction"]["label"] == "AI-generated"
    assert body["prediction"]["raw_probability"] == pytest.approx(0.75)
    assert body["prediction"]["model_used"] == Config.HUGGINGFACE_MODEL_NAME
    assert (
        body["prediction"]["model_display_name"]
        == Config.CIFAKE_MODEL_DISPLAY_NAMES[Config.HUGGINGFACE_MODEL_NAME]
    )
    assert body["limitation_notice"] == Config.HUGGINGFACE_LIMITATION_NOTICE


def test_stage1_metadata_shortcircuit_via_api(
    client: FlaskClient,
    mock_predictor: Mock,
) -> None:
    """Uploading a PNG with Stable Diffusion metadata short-circuits Stage 2."""
    from PIL import Image, PngImagePlugin

    buf = BytesIO()
    info = PngImagePlugin.PngInfo()
    info.add_text("parameters", "Steps: 25, Sampler: Euler a, CFG scale: 7")
    Image.new("RGB", (32, 32), color=(10, 20, 30)).save(buf, format="PNG", pnginfo=info)
    buf.seek(0)

    response = client.post(
        "/analyze",
        data={"image": (buf, "sd_gen.png")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )

    body = response.get_json()
    assert response.status_code == 200
    assert body["prediction"]["label"] == "AI-generated"
    assert body["prediction"]["classification_source"] == "metadata"
    assert body["prediction"]["raw_probability"] is None
    assert body["stage1_result"]["status"] == "ai_detected"
    assert body["stage1_result"]["route_to_stage2"] is False
    assert body["limitation_notice"] == Config.STAGE1_METADATA_NOTICE
    mock_predictor.assert_not_called()


def test_analyze_valid_synthetic_image_renders_html(
    client: FlaskClient,
    synthetic_jpeg_bytes: bytes,
    mock_predictor: Mock,
) -> None:
    """A browser upload receives the rendered CIFAKE results page."""
    response = client.post(
        "/analyze",
        data={"image": (BytesIO(synthetic_jpeg_bytes), "synthetic.jpg")},
        content_type="multipart/form-data",
        headers={"Accept": "text/html"},
    )

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "AI-generated" in page
    assert "100 × 100 px" in page
    assert "RGB" in page
    assert "CIFAKE Custom CNN" in page
    assert "Model Architecture" in page
    assert "Analysis Latency" in page
    assert "ms" in page
    assert Config.CIFAKE_LIMITATION_NOTICE in html.unescape(page)
    assert "Download PDF Report" in page
    assert "0.9340" in page
    assert "Why we think this" in page
    assert "Error Level Analysis" not in page
    mock_predictor.assert_called_once()


def test_analyze_missing_model_returns_explicit_error(
    client: FlaskClient,
    synthetic_jpeg_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing CIFAKE model surfaces an explicit 503 error with no fallback prediction."""
    from src.models.model_loader import ModelLoader

    ModelLoader.clear_cache()
    monkeypatch.setitem(
        ModelLoader._load_errors,
        Config.CIFAKE_MODEL_NAME,
        "CIFAKE Custom CNN model file not found at '/nonexistent/cifake_custom_cnn.keras'.",
    )

    response = client.post(
        "/analyze",
        data={"image": (BytesIO(synthetic_jpeg_bytes), "synthetic.jpg")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )

    body = response.get_json()
    assert response.status_code == 503
    assert body["status"] == "error"
    assert body["error_code"] == "MODEL_NOT_LOADED"
    assert "cifake_custom_cnn.keras" in body["message"]


def test_analyze_inference_error_returns_explicit_error(
    client: FlaskClient,
    synthetic_jpeg_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inference failure returns an explicit 500 error without fallback."""
    from src.models.predictor import Predictor
    from src.utils.exceptions import ModelInferenceError

    monkeypatch.setattr(
        Predictor,
        "predict",
        Mock(side_effect=ModelInferenceError("Simulated forward pass failure")),
    )

    response = client.post(
        "/analyze",
        data={"image": (BytesIO(synthetic_jpeg_bytes), "synthetic.jpg")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )

    body = response.get_json()
    assert response.status_code == 500
    assert body["status"] == "error"
    assert body["error_code"] == "MODEL_INFERENCE_ERROR"
    assert "Simulated forward pass failure" in body["message"]


def test_executable_payload_disguised_as_jpeg_is_rejected(
    client: FlaskClient,
    synthetic_corrupt_bytes: bytes,
) -> None:
    """A non-image payload using a JPEG extension is rejected as a bad request."""
    response = client.post(
        "/analyze",
        data={"image": (BytesIO(synthetic_corrupt_bytes), "test.jpg")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


def test_oversized_upload_returns_payload_too_large(
    client: FlaskClient,
    synthetic_oversized_bytes: bytes,
) -> None:
    """A request exceeding the configured upload size is rejected with HTTP 413."""
    response = client.post(
        "/analyze",
        data={"image": (BytesIO(synthetic_oversized_bytes), "oversized.jpg")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 413


@pytest.mark.parametrize(
    ("verdict_code", "verdict_label", "badge_class"),
    [
        (1, "AI-generated", "text-bg-danger"),
        (0, "Real photo", "text-bg-success"),
    ],
)
def test_result_template_accepts_nested_mock_results(
    app: Flask,
    verdict_code: int,
    verdict_label: str,
    badge_class: str,
) -> None:
    """Render both CIFAKE verdict states with the nested result shape."""
    with app.test_request_context():
        page = render_template(
            "result.html",
            results={
                "session_id": "test-session",
                "verdict_label": verdict_label,
                "verdict_code": verdict_code,
                "raw_probability": 0.934,
                "model_used": Config.CIFAKE_MODEL_NAME,
                "original_image_path": "/static/temp/test/orig.jpg",
                "disclaimer": Config.CIFAKE_LIMITATION_NOTICE,
            },
        )

    assert verdict_label in page
    assert "0.9340" in page
    assert badge_class in page
    assert "/report/test-session" in page
    assert "/static/temp/test/orig.jpg" in page
    assert Config.CIFAKE_LIMITATION_NOTICE in html.unescape(page)
    assert "Error Level Analysis" not in page
    assert "Analyze Another Image" in page


def test_report_download_returns_pdf_for_completed_session(
    client: FlaskClient,
    synthetic_jpeg_bytes: bytes,
    mock_predictor: Mock,
) -> None:
    """A completed synthetic-image analysis can be downloaded as a PDF report."""
    analysis_response = client.post(
        "/analyze",
        data={"image": (BytesIO(synthetic_jpeg_bytes), "synthetic.jpg")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )
    session_id = analysis_response.get_json()["session_id"]

    response = client.get(f"/report/{session_id}")

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
    assert len(response.data) > 1000
    assert response.headers["Content-Disposition"] == (
        f"attachment; filename=classification_report_{session_id}.pdf"
    )
    assert not (Path(Config.UPLOAD_FOLDER) / session_id).exists()


def test_report_download_returns_not_found_for_unknown_session(client: FlaskClient) -> None:
    """A session without a completed analysis cannot retrieve a report."""
    response = client.get("/report/unknown-session")

    assert response.status_code == 404
