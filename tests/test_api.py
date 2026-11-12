"""Integration tests for the Flask HTTP interface."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Iterator

import pytest
from flask import Flask, render_template
from flask.testing import FlaskClient
from PIL import Image

from app import create_app
from config import Config
from src.models.model_loader import MockFallbackModel, ModelLoader


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Flask]:
    """Create a test application with isolated temporary uploads.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Per-test temporary filesystem path.

    Yields:
        A configured Flask application instance.
    """
    upload_folder = tmp_path / "uploads"
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", upload_folder)

    def register_test_models() -> None:
        """Populate the model registry without loading model weights."""
        for model_name in ("cnn", "mobilenet"):
            ModelLoader.register_model(model_name, MockFallbackModel(model_name))

    monkeypatch.setattr(ModelLoader, "load_all_models", register_test_models)
    ModelLoader.clear_cache()
    test_app = create_app(Config)
    test_app.config.update(TESTING=True)
    yield test_app
    ModelLoader.clear_cache()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Return a Flask test client.

    Args:
        app: Test application fixture.

    Returns:
        A Flask test client for the application.
    """
    return app.test_client()


def _synthetic_jpeg() -> bytes:
    """Encode a small synthetic RGB image as JPEG bytes.

    Returns:
        Encoded JPEG image content.
    """
    image = Image.new("RGB", (64, 64), color=(80, 120, 160))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_home_page_returns_ok(client: FlaskClient) -> None:
    """The home upload page is available."""
    response = client.get("/")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'id="dropZone"' in page
    assert 'name="image"' in page
    assert 'name="model"' in page
    assert f'data-max-file-size="{Config.MAX_CONTENT_LENGTH}"' in page
    assert "MobileNetV2 (Recommended)" in page
    assert "Custom CNN" in page
    assert 'css/style.css' in page
    assert 'js/main.js' in page


def test_navigating_home_cleans_the_active_session_directory(client: FlaskClient) -> None:
    """Returning home removes the current session's temporary image files."""
    analysis_response = client.post(
        "/analyze",
        data={"image": (BytesIO(_synthetic_jpeg()), "synthetic.jpg")},
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
    assert "Copy-move" in page
    assert "Splicing" in page
    assert "False positives" in page
    assert "False negatives" in page
    assert Config.ELA_DISCLAIMER in page
    assert "Member 4" in page


def test_html_upload_error_renders_structured_error_page(client: FlaskClient) -> None:
    """A missing upload is explained on the user-facing error page."""
    response = client.post("/analyze", headers={"Accept": "text/html"})

    page = response.get_data(as_text=True)
    assert response.status_code == 400
    assert "Bad Request" in page
    assert "Return to Upload" in page


def test_health_returns_healthy_status(client: FlaskClient) -> None:
    """The health endpoint reports the application and model state."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"
    assert response.get_json()["models_loaded"]["cnn"] is True
    assert response.get_json()["models_loaded"]["mobilenet"] is True


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


def test_analyze_valid_synthetic_image_returns_json(client: FlaskClient) -> None:
    """A synthetic JPEG is analyzed and returned with artifact URLs."""
    response = client.post(
        "/analyze",
        data={"image": (BytesIO(_synthetic_jpeg()), "synthetic.jpg")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )

    body = response.get_json()
    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["prediction"]["model_used"] == "mobilenet"
    assert body["artifacts"]["original_image_url"].startswith("/static/temp/")
    assert body["artifacts"]["ela_image_url"].startswith("/static/temp/")
    original_response = client.get(body["artifacts"]["original_image_url"])
    assert original_response.status_code == 200
    assert original_response.mimetype == "image/jpeg"


def test_analyze_valid_synthetic_image_renders_html(client: FlaskClient) -> None:
    """A browser upload receives the rendered results page."""
    response = client.post(
        "/analyze",
        data={"image": (BytesIO(_synthetic_jpeg()), "synthetic.jpg")},
        content_type="multipart/form-data",
        headers={"Accept": "text/html"},
    )

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Potentially Manipulated" in page
    assert "64 × 64 px" in page
    assert "RGB" in page
    assert "MobileNetV2" in page
    assert "Model Architecture" in page
    assert "Analysis Latency" in page
    assert "ms" in page
    assert Config.ELA_DISCLAIMER in page
    assert "Download PDF Report" in page


@pytest.mark.parametrize(
    ("verdict_code", "verdict_label", "badge_class"),
    [
        (1, "Potentially Manipulated", "text-bg-danger"),
        (0, "Authentic Image", "text-bg-success"),
    ],
)
def test_result_template_accepts_nested_mock_results(
    app: Flask,
    verdict_code: int,
    verdict_label: str,
    badge_class: str,
) -> None:
    """Render both verdict states with the documented nested result shape."""
    with app.test_request_context():
        page = render_template(
            "result.html",
            results={
                "session_id": "test-session",
                "verdict_label": verdict_label,
                "verdict_code": verdict_code,
                "confidence": 93.4,
                "model_used": "mobilenet_v2",
                "original_image_path": "/static/temp/test/orig.jpg",
                "ela_image_path": "/static/temp/test/ela.png",
                "disclaimer": "ELA is an investigative aid.",
            },
        )

    assert verdict_label in page
    assert "93.4%" in page
    assert badge_class in page
    assert "/report/test-session" in page
    assert "/static/temp/test/orig.jpg" in page
    assert "/static/temp/test/ela.png" in page
    assert Config.ELA_DISCLAIMER in page
    assert 'id="imageInspectToggle"' in page
    assert 'class="col-lg-6"' in page
    assert "Analyze Another Image" in page


def test_report_download_returns_pdf_for_completed_session(client: FlaskClient) -> None:
    """A completed synthetic-image analysis can be downloaded as a PDF report."""
    analysis_response = client.post(
        "/analyze",
        data={"image": (BytesIO(_synthetic_jpeg()), "synthetic.jpg")},
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
        f"attachment; filename=forensic_report_{session_id}.pdf"
    )
    assert not (Path(Config.UPLOAD_FOLDER) / session_id).exists()


def test_report_download_returns_not_found_for_unknown_session(client: FlaskClient) -> None:
    """A session without a completed analysis cannot retrieve a report."""
    response = client.get("/report/unknown-session")

    assert response.status_code == 404
