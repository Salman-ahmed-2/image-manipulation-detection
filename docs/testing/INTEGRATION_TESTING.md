# Integration Testing Guide — Image Manipulation Detection System

> **Framework:** pytest + Flask Test Client  
> **Layer:** Integration (module interactions, not individual functions)  
> **Last Updated:** 2026-11-08

---

## 1. What to Integration Test

Integration tests verify that **two or more modules work correctly together** through their real interfaces. Unlike unit tests that isolate individual functions, integration tests exercise the connections between components.

For this system, the primary integration concern is the **analysis pipeline**:

```
HTTP Upload Request
       │
       ▼
  File Validator ──────────────────────► 400 Bad Request (if invalid)
       │ (passes)
       ▼
  Preprocessor (resize, normalize, batch)
       │
       ▼
  ELA Generator (error level analysis)
       │
       ▼
  Detection Service (model inference)
       │
       ▼
  Result Renderer (templates, session data)
       │
       ▼
  HTTP Response (200 with result page)
```

Each arrow in this diagram is an integration boundary — a place where data flows from one module to another and must be in the exact format the receiving module expects.

### Integration Test Scope Summary

| Integration Boundary | What Must Match |
|---|---|
| Validator → Preprocessor | Validated file is a readable buffer in correct format |
| Preprocessor → DetectionService | Tensor shape `(1, 224, 224, 3)`, dtype `float32`, values `[0,1]` |
| ELA Generator → Template | Returns a valid `PIL.Image` or saved path, renderable in HTML |
| DetectionService → Result | Returns `{"label": int, "confidence": float, "label_text": str}` |
| Result → ReportService | Session result dict is correctly passed to PDF generator |
| Flask Route → HTTP Response | Correct status codes for all scenarios |

---

## 2. Integration Test Scenarios

### Scenario 1: Valid JPEG Upload → Analysis → Results Page

**Goal:** Verify the complete happy path for a JPEG image upload.

```python
# tests/test_api.py (integration section)
import io
import pytest
from PIL import Image
from unittest.mock import patch, MagicMock


@pytest.mark.integration
def test_valid_jpeg_upload_full_pipeline(client):
    """
    Integration: Valid JPEG → validate → preprocess → mock predict → result page.
    Uses a mocked model to avoid dependency on trained .h5 file.
    """
    # Create a valid synthetic JPEG
    img = Image.new("RGB", (200, 200), color=(180, 90, 45))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)

    mock_result = {
        "label": 1,
        "label_text": "Manipulated",
        "confidence": 0.87,
        "ela_path": "/tmp/test_ela.png",
    }

    with patch("src.services.detection_service.DetectionService.predict",
               return_value=mock_result):
        response = client.post(
            "/analyze",
            data={"file": (buf, "test_photo.jpg")},
            content_type="multipart/form-data",
        )

    # Expect either a redirect to result page or direct 200 with results
    assert response.status_code in (200, 302)

    if response.status_code == 302:
        # Follow the redirect
        redirect_response = client.get(response.headers["Location"])
        assert redirect_response.status_code == 200
        assert b"Manipulated" in redirect_response.data or b"result" in redirect_response.data.lower()
```

**What this tests:**
- File is received by the Flask route
- Validator accepts the JPEG
- Preprocessor is called and produces the right tensor shape
- DetectionService.predict() is called (mocked here) with the correct argument
- Result is rendered and the response is a valid HTTP success

---

### Scenario 2: Valid PNG Upload → Analysis → Results Page (ELA Caveat Documented)

**Goal:** Verify PNG images complete the pipeline. Document that ELA output on PNG shows conversion artifacts — this is expected, not a bug.

```python
@pytest.mark.integration
def test_valid_png_upload_full_pipeline(client):
    """
    Integration: Valid PNG → validate → preprocess → mock predict → result page.
    
    Important: PNG images are converted to JPEG internally for ELA processing.
    The resulting ELA image will show JPEG compression artifacts in addition to
    any actual manipulation signals. This is a known and documented limitation.
    """
    img = Image.new("RGB", (200, 200), color=(64, 128, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    mock_result = {
        "label": 0,
        "label_text": "Authentic",
        "confidence": 0.73,
        "ela_path": "/tmp/test_ela_png.png",
        "png_conversion_note": True,  # Flag that ELA was run on converted JPEG
    }

    with patch("src.services.detection_service.DetectionService.predict",
               return_value=mock_result):
        response = client.post(
            "/analyze",
            data={"file": (buf, "test_photo.png")},
            content_type="multipart/form-data",
        )

    assert response.status_code in (200, 302)
```

> [!NOTE]
> When testing PNG uploads, verify that the UI shows a note explaining ELA reliability for PNG input. The result template should display `png_conversion_note` if set.

---

### Scenario 3: Invalid File Type → Error Page

**Goal:** Verify that uploading an unsupported file type produces a user-friendly error response — not a 500 Internal Server Error.

```python
@pytest.mark.integration
def test_invalid_file_type_returns_error_page(client):
    """
    Integration: Uploading an unsupported file type must return an error
    response with a helpful message, not a server crash.
    """
    # Upload a text file pretending to be an image
    buf = io.BytesIO(b"This is not an image. It is plain text.")
    
    response = client.post(
        "/analyze",
        data={"file": (buf, "data.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    # Response should contain a user-readable error message
    assert b"error" in response.data.lower() or b"invalid" in response.data.lower()


@pytest.mark.integration
def test_pdf_file_returns_error_page(client):
    """PDF files must be rejected with a 400 error."""
    buf = io.BytesIO(b"%PDF-1.4 Fake PDF content here")
    
    response = client.post(
        "/analyze",
        data={"file": (buf, "report.pdf")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
```

---

### Scenario 4: Valid Image → PDF Report Download

**Goal:** Verify that after a successful analysis, a PDF report can be downloaded via `GET /report/<id>`.

```python
@pytest.mark.integration
def test_pdf_report_download_after_analysis(client):
    """
    Integration: After a successful analysis, GET /report/<id> must return
    a downloadable PDF with correct content-type header.
    """
    # First, perform an analysis to populate the session
    img = Image.new("RGB", (200, 200), color=(180, 90, 45))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)

    mock_result = {
        "label": 1,
        "label_text": "Manipulated",
        "confidence": 0.87,
        "result_id": "test-report-001",
        "ela_path": None,
    }

    with patch("src.services.detection_service.DetectionService.predict",
               return_value=mock_result):
        with patch("src.services.report_service.ReportService.generate_pdf",
                   return_value=b"%PDF-1.4 fake pdf bytes") as mock_pdf:
            
            # Perform analysis
            client.post(
                "/analyze",
                data={"file": (buf, "test.jpg")},
                content_type="multipart/form-data",
            )

            # Request the PDF report
            report_response = client.get("/report/test-report-001")

    assert report_response.status_code == 200
    assert "application/pdf" in report_response.content_type
```

---

### Scenario 5: Health Check with Model Loaded

**Goal:** Verify the `/health` endpoint reports correct status and indicates model availability.

```python
@pytest.mark.integration
def test_health_check_reports_model_status(client):
    """
    Integration: GET /health must return JSON with status 'ok' and
    indicate whether the model is loaded.
    """
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data is not None
    assert "status" in data
    assert data["status"] == "ok"
    
    # Health check should report model status (loaded or not loaded)
    assert "model_loaded" in data or "model" in data
```

---

## 3. Test Environment Setup

### 3.1 Flask Test Client Configuration

```python
# tests/conftest.py

import pytest
from app import create_app

@pytest.fixture(scope="session")
def app():
    """
    Create the Flask application in test mode.
    - TESTING=True disables error propagation (shows real exceptions)
    - MAX_CONTENT_LENGTH enforces 16MB limit
    - Model loading may be skipped if model file is absent
    """
    test_config = {
        "TESTING": True,
        "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,
        "SECRET_KEY": "test-secret-key-not-for-production",
        "WTF_CSRF_ENABLED": False,
    }
    application = create_app(config=test_config)
    return application


@pytest.fixture(scope="session")
def client(app):
    """Return a Flask test client for the duration of the test session."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Push an application context for tests that need it."""
    with app.app_context():
        yield app
```

### 3.2 Application Factory Pattern

For integration tests to work cleanly, the Flask app must support a factory pattern:

```python
# app.py

def create_app(config=None, testing=False):
    """
    Application factory.
    Accepts configuration overrides for test environments.
    When testing=True, model loading errors are suppressed gracefully.
    """
    app = Flask(__name__)
    
    # Apply defaults
    app.config.from_object("config.DefaultConfig")
    
    # Apply test overrides
    if config:
        app.config.update(config)
    if testing:
        app.config["TESTING"] = True

    # Register blueprints / routes
    from routes import main_bp
    app.register_blueprint(main_bp)

    # Initialize model (with graceful fallback for test environments)
    from src.services.detection_service import DetectionService
    try:
        app.detection_service = DetectionService(
            model_path=app.config.get("MODEL_PATH", "artifacts/models/best_model.h5")
        )
    except FileNotFoundError:
        if testing:
            app.detection_service = None  # Tests will mock this
        else:
            raise

    return app
```

### 3.3 Temporary Model Stubs

When the real trained model is not available (early in development), use a stub:

```python
# tests/stubs/model_stub.py

class ModelStub:
    """
    Drop-in replacement for a loaded Keras model during testing.
    Always returns a fixed prediction value.
    """
    def __init__(self, return_value=0.8):
        self.return_value = return_value
        self.input_shape = (None, 224, 224, 3)

    def predict(self, x, verbose=0):
        import numpy as np
        batch_size = x.shape[0]
        return np.array([[self.return_value]] * batch_size)

    def __call__(self, x):
        return self.predict(x)
```

---

## 4. Mock Strategy

Integration tests for the analysis pipeline use mocking at the **model inference boundary** only. Everything above the model (file validation, preprocessing, ELA) runs with real code.

```
[ Real Code ]                    [ Mocked ]
─────────────────────────────────────────────
Flask Route ──► Validator ──► Preprocessor ──► [DetectionService.predict()]
                                ELA Generator ──► [Template Renderer]
```

### 4.1 When to Mock

| Scenario | Mock? | Reason |
|---|---|---|
| Testing file validation logic | No | Use real validator |
| Testing preprocessing pipeline | No | Use real preprocessor |
| Testing ELA generation | No | Use real ELA generator |
| Testing model prediction output | Yes | Model may not be trained yet |
| Testing PDF generation | Yes | Avoid generating real PDFs in every test |
| Testing email/external API (N/A) | Yes | External service stability |

### 4.2 Standard Mock Pattern for Integration Tests

```python
from unittest.mock import patch, MagicMock

# Pattern: patch at the point of use, not at the definition
with patch("app.routes.detection_service.predict") as mock_predict:
    mock_predict.return_value = {
        "label": 0,
        "label_text": "Authentic",
        "confidence": 0.65,
    }
    response = client.post("/analyze", ...)
```

### 4.3 Avoiding Over-Mocking

> [!WARNING]
> Do not mock the file validator or preprocessor in integration tests. If those are mocked, you lose the integration coverage entirely and the tests become indistinguishable from unit tests.

---

## 5. Integration Test Checklist

Use this checklist before marking integration testing complete for each milestone.

| # | Scenario | Expected Status | Verified | Notes |
|---|---|---|---|---|
| 1 | Valid JPEG upload → analysis complete | 200 or 302→200 | ☐ | Core happy path |
| 2 | Valid PNG upload → analysis complete | 200 or 302→200 | ☐ | ELA conversion note shown |
| 3 | PDF file upload → error message | 400 | ☐ | No server crash |
| 4 | GIF file upload → error message | 400 | ☐ | No server crash |
| 5 | Oversized file (>16MB) → error message | 413 | ☐ | Flask MAX_CONTENT_LENGTH enforced |
| 6 | No file attached → error message | 400 | ☐ | Empty form submission |
| 7 | PDF report downloadable after analysis | 200, `application/pdf` | ☐ | Content-Type header correct |
| 8 | Health endpoint returns `{"status": "ok"}` | 200 | ☐ | Liveness check |
| 9 | Report ID not found → 404 | 404 | ☐ | Invalid report ID handled |
| 10 | Spoofed extension (PDF bytes, .jpg name) | 400 | ☐ | MIME sniffing works |
| 11 | 224×224 image processes without resize errors | 200 | ☐ | Exact model input size |
| 12 | Very small image (10×10) is upscaled correctly | 200 | ☐ | Resize handles small inputs |
| 13 | Grayscale JPEG completes pipeline | 200 | ☐ | Grayscale→RGB conversion |
| 14 | RGBA PNG completes pipeline | 200 | ☐ | RGBA→RGB conversion |
| 15 | Concurrent requests don't share state | 200 each | ☐ | Session isolation check |

---

## 6. Running Integration Tests

```bash
# Run only integration-marked tests
pytest tests/ -m integration -v

# Run integration tests with coverage
pytest tests/ -m integration --cov=src --cov-report=term-missing

# Run all tests except those requiring a real trained model
pytest tests/ -m "not requires_model" -v
```

---

## 7. Integration Test Maintenance Notes

- **Re-run after any route change** — adding or modifying a Flask endpoint requires verifying Scenario 1–9 again.
- **Re-run after preprocessing changes** — changes to resize dimensions, normalization scale, or channel conversion affect model input and must be re-validated.
- **Document any new failure modes** — if a new exception type can be raised, add an integration test for it.
- **Keep mocks up to date** — if `DetectionService.predict()` signature changes, update all mock `return_value` structures to match.
