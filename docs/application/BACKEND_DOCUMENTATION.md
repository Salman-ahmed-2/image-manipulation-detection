# Backend Documentation

## Image Manipulation Detection System — Flask Backend

---

## Table of Contents

1. [Flask Application Structure](#1-flask-application-structure)
2. [App Factory Pattern](#2-app-factory-pattern-apppy)
3. [Configuration](#3-configuration-configpy)
4. [Blueprint Descriptions](#4-blueprint-descriptions)
5. [Route Specifications](#5-route-specifications)
6. [Request/Response Formats for `/analyze`](#6-requestresponse-formats-for-analyze)
7. [Error Handling Strategy](#7-error-handling-strategy)
8. [Session Management](#8-session-management)
9. [Temp File Management](#9-temp-file-management)
10. [Security Measures](#10-security-measures)

---

## 1. Flask Application Structure

The backend follows Flask's **Application Factory** pattern combined with **Blueprints** for modular route organization. This prevents circular imports, enables proper testing (each test can spin up a fresh app instance), and cleanly separates concerns.

```
image-manipulation-detection/
├── app.py                          # App factory: create_app()
├── config.py                       # Configuration class hierarchy
├── run.py                          # Entry point: calls create_app(), app.run()
├── web/
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       ├── main_routes.py          # Blueprint: home, about
│       └── detection_routes.py     # Blueprint: /analyze, /report, /health
└── src/
    ├── preprocessing/
    │   ├── image_preprocessor.py   # Image loading and normalization
    │   └── ela_generator.py        # Error Level Analysis
    ├── models/
    │   ├── cnn_model.py            # Custom CNN architecture and loader
    │   └── mobilenet_model.py      # MobileNetV2 transfer learning loader
    ├── prediction/
    │   └── predictor.py            # Unified prediction interface
    ├── reporting/
    │   └── report_generator.py     # PDF generation with fpdf2
    └── utils/
        ├── file_validator.py       # File validation logic
        └── logger.py               # Centralized logging setup
```

---

## 2. App Factory Pattern (`app.py`)

The application is instantiated via the `create_app()` factory function. This pattern is the Flask-recommended approach for non-trivial applications.

```python
# app.py
from flask import Flask
from config import Config, DevelopmentConfig, ProductionConfig
from web.routes.main_routes import main_bp
from web.routes.detection_routes import detection_bp
import os

def create_app(config_object=None):
    """Create and configure the Flask application.

    Args:
        config_object: Configuration class or object to use. If None,
                       selects based on FLASK_ENV environment variable.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__, template_folder='web/templates',
                static_folder='web/static')

    # --- Config Loading ---
    if config_object is None:
        env = os.getenv('FLASK_ENV', 'development')
        config_object = DevelopmentConfig if env == 'development' else ProductionConfig
    app.config.from_object(config_object)

    # --- Ensure temp upload directory exists ---
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- Blueprint Registration ---
    app.register_blueprint(main_bp)
    app.register_blueprint(detection_bp)

    # --- Error Handlers ---
    register_error_handlers(app)

    return app


def register_error_handlers(app):
    """Register HTTP error handlers on the application."""
    from flask import render_template

    @app.errorhandler(400)
    def bad_request(e):
        return render_template('error.html',
                               error_code=400,
                               error_title='Bad Request',
                               error_message=str(e)), 400

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html',
                               error_code=404,
                               error_title='Page Not Found',
                               error_message='The page you requested does not exist.'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('error.html',
                               error_code=413,
                               error_title='File Too Large',
                               error_message='The uploaded file exceeds the 16 MB limit. '
                                             'Please upload a smaller image.'), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html',
                               error_code=500,
                               error_title='Internal Server Error',
                               error_message='An unexpected error occurred. '
                                             'Please try again.'), 500
```

### `run.py` — Application Entry Point

```python
# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

> [!IMPORTANT]
> Never run with `debug=True` in production. Set `FLASK_ENV=production` and use a WSGI server (Gunicorn) instead.

---

## 3. Configuration (`config.py`)

All application configuration is centralized in `config.py`. Environment-specific subclasses inherit from a shared `Config` base.

```python
# config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base configuration shared by all environments."""

    # Flask core
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')
    SESSION_TYPE = 'filesystem'

    # File upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024          # 16 MB
    UPLOAD_FOLDER = str(BASE_DIR / 'temp' / 'uploads')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

    # ML model paths
    MODEL_PATH_CNN = str(BASE_DIR / 'artifacts' / 'models' / 'cnn_model.h5')
    MODEL_PATH_MOBILENET = str(BASE_DIR / 'artifacts' / 'models' / 'mobilenet_model.h5')
    ACTIVE_MODEL = 'mobilenet'                      # Default model selection

    # ELA parameters
    ELA_QUALITY = 90                                # JPEG re-compression quality for ELA
    ELA_SCALE = 10                                  # Amplification factor for ELA diff

    # Reporting
    REPORT_FOLDER = str(BASE_DIR / 'temp' / 'reports')


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False
    # In production, SECRET_KEY MUST be set via environment variable
    SECRET_KEY = os.environ['SECRET_KEY']


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = True
    UPLOAD_FOLDER = '/tmp/test_uploads'
    WTF_CSRF_ENABLED = False
```

### Configuration Reference Table

| Config Key | Type | Default Value | Description |
|---|---|---|---|
| `SECRET_KEY` | `str` | `[from env]` | Flask session signing key. Must be a strong random value in production. |
| `MAX_CONTENT_LENGTH` | `int` | `16777216` (16 MB) | Maximum allowed size for the entire request body. Flask returns 413 automatically if exceeded. |
| `UPLOAD_FOLDER` | `str` | `temp/uploads` | Absolute path to the temporary upload directory. Created automatically on startup. |
| `ALLOWED_EXTENSIONS` | `set` | `{'jpg', 'jpeg', 'png'}` | Whitelist of permitted file extensions. Compared against the uploaded file's extension. |
| `MODEL_PATH_CNN` | `str` | `artifacts/models/cnn_model.h5` | Absolute path to the trained custom CNN model weights file. |
| `MODEL_PATH_MOBILENET` | `str` | `artifacts/models/mobilenet_model.h5` | Absolute path to the trained MobileNetV2 model weights file. |
| `ACTIVE_MODEL` | `str` | `'mobilenet'` | Default model used when the user does not specify one in the request. |
| `ELA_QUALITY` | `int` | `90` | JPEG re-save quality used during ELA computation. Lower values increase ELA sensitivity. |
| `ELA_SCALE` | `int` | `10` | Pixel difference amplification factor for ELA visualization (multiplied before display). |
| `REPORT_FOLDER` | `str` | `temp/reports` | Temporary storage for generated PDF reports before streaming. |
| `SESSION_TYPE` | `str` | `'filesystem'` | Flask session backend type. |

> [!WARNING]
> `SECRET_KEY` defaults to a hardcoded string in `DevelopmentConfig`. **This default must never be used in production.** `ProductionConfig` raises a `KeyError` if `SECRET_KEY` is not set in the environment, preventing accidental insecure deployment.

---

## 4. Blueprint Descriptions

### `main_bp` — General Pages Blueprint

**Module:** `web/routes/main_routes.py`
**URL prefix:** *(none — routes are at root)*

Handles navigation pages that do not involve ML processing.

| Route | Method | Handler Function |
|---|---|---|
| `/` | `GET` | `index()` |
| `/about` | `GET` | `about()` |

```python
# web/routes/main_routes.py
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')
```

---

### `detection_bp` — Detection and Reporting Blueprint

**Module:** `web/routes/detection_routes.py`
**URL prefix:** *(none)*

Handles all ML analysis, report generation, and system health routes. This is where the core business logic orchestration happens.

| Route | Method | Handler Function |
|---|---|---|
| `/analyze` | `POST` | `analyze()` |
| `/report/<session_id>` | `GET` | `download_report()` |
| `/health` | `GET` | `health_check()` |

---

## 5. Route Specifications

### `GET /` — Home Page

| Property | Value |
|---|---|
| **Blueprint** | `main_bp` |
| **Handler** | `main_routes.index()` |
| **Auth required** | No |
| **Response** | 200 OK — renders `index.html` |

### `GET /about` — About Page

| Property | Value |
|---|---|
| **Blueprint** | `main_bp` |
| **Handler** | `main_routes.about()` |
| **Auth required** | No |
| **Response** | 200 OK — renders `about.html` |

### `POST /analyze` — Image Analysis

| Property | Value |
|---|---|
| **Blueprint** | `detection_bp` |
| **Handler** | `detection_routes.analyze()` |
| **Content-Type** | `multipart/form-data` |
| **Auth required** | No |

**Processing pipeline executed by this route:**
1. Extract file from `request.files['image']`
2. Validate file (via `FileValidator`)
3. Apply `secure_filename()` and save to temp folder
4. Inspect C2PA credentials and EXIF/XMP metadata
5. If C2PA is `Trusted` and asserts an AI-origin action, return that provenance finding
   without running the classifier; otherwise continue with the selected model
6. Store results and file paths in Flask session
7. Render `result.html` with results data

`C2PA_TRUST_ANCHORS_PATH` may point to a PEM trust list. If it is unset, missing, or
cannot be used, a C2PA claim is not treated as trusted and classifier inference runs.
EXIF/XMP generator strings and generator names found in the active C2PA manifest are
shown as clues only and never bypass inference. Parsed nested XMP fields are scanned.

**On success:** Renders `result.html` (200 OK)
**On validation failure:** Flash error message, redirect to `/` (302)
**On server error:** Render `error.html` (500)

### `GET /report/<session_id>` — PDF Report Download

| Property | Value |
|---|---|
| **Blueprint** | `detection_bp` |
| **Handler** | `detection_routes.download_report()` |
| **URL Parameter** | `session_id` — UUID string |
| **Auth required** | No (session-based access control) |

**Behavior:**
1. Verify `session_id` matches the current Flask session's stored ID
2. Retrieve stored analysis results from session
3. Call `ReportGenerator.generate()` to produce PDF bytes
4. Stream PDF with `Content-Disposition: attachment; filename="report_{session_id}.pdf"`
5. Schedule temp file cleanup

**On success:** 200 OK — binary PDF stream
**On session expired/mismatch:** 404 — renders `error.html`

### `GET /health` — Health Check

| Property | Value |
|---|---|
| **Blueprint** | `detection_bp` |
| **Handler** | `detection_routes.health_check()` |
| **Auth required** | No |

Returns system status as JSON. Useful for monitoring and deployment verification.

**Response:**
```json
{
  "status": "ok",
  "model_loaded": true,
  "active_model": "mobilenet",
  "version": "1.0.0"
}
```

---

## 6. Request/Response Formats for `/analyze`

### Request

```
POST /analyze HTTP/1.1
Content-Type: multipart/form-data; boundary=----FormBoundary

------FormBoundary
Content-Disposition: form-data; name="image"; filename="photo.jpg"
Content-Type: image/jpeg

[binary image data]
------FormBoundary
Content-Disposition: form-data; name="model"

mobilenet
------FormBoundary--
```

| Field | Type | Required | Values | Default |
|---|---|---|---|---|
| `image` | File (binary) | **Yes** | JPG, JPEG, PNG | — |
| `model` | String | No | `'cnn'` or `'mobilenet'` | `'mobilenet'` |

### Response (Success)

On success, the route renders and returns `result.html` (HTTP 200). The result data is passed as template context — it is not returned as JSON in the standard browser flow.

If the client sends `Accept: application/json` (for API/AJAX use), the route returns JSON:

```json
{
  "status": "success",
  "prediction": {
    "label": "AI-generated",
    "raw_probability": null,
    "classification_source": "verified_c2pa"
  },
  "metadata_assessment": {
    "c2pa_validation_state": "Trusted",
    "has_trusted_ai_claim": true,
    "metadata_clues": []
  },
  "session_id": "abc123-uuid-here"
}
```

For model-based results, `raw_probability` contains the model score and
`classification_source` is `"model"`. For verified C2PA results, model score fields
are `null`; the route does not fabricate a confidence score.

### Response (Error)

```json
{
  "status": "error",
  "message": "Invalid file type. Only JPG, JPEG, and PNG are accepted.",
  "code": 400
}
```

| Error Code | Trigger Condition |
|---|---|
| `400` | No file in request, empty filename, invalid file type, failed magic bytes check |
| `413` | File size exceeds `MAX_CONTENT_LENGTH` (16 MB) |
| `500` | Preprocessing failure, model inference error, ELA generation failure |

---

## 7. Error Handling Strategy

The application uses a layered error handling approach:

### Layer 1: Flask HTTP Error Handlers

Registered in `app.py` via `register_error_handlers()`. These handle standard HTTP errors (400, 404, 413, 500) and render user-friendly `error.html` pages.

### Layer 2: Route-Level Try/Except

Each route handler in `detection_routes.py` wraps its processing pipeline in `try/except` blocks:

```python
try:
    result = predictor.predict(preprocessed_image)
except ModelNotLoadedError as e:
    logger.error(f"Model not loaded: {e}")
    return render_template('error.html',
                           error_code=500,
                           error_title='Model Error',
                           error_message='The ML model is not available.'), 500
except Exception as e:
    logger.error(f"Unexpected prediction error: {e}", exc_info=True)
    abort(500)
```

### Layer 3: Custom Exception Classes

Defined in `src/utils/exceptions.py`:

| Exception Class | Raised When |
|---|---|
| `InvalidFileTypeError` | File extension or magic bytes check fails |
| `FileTooLargeError` | File size exceeds limit (redundant with Flask 413, used for explicit checks) |
| `ModelNotLoadedError` | ML model file not found or failed to load |
| `PreprocessingError` | Image cannot be decoded or resized |
| `ELAGenerationError` | ELA computation fails (e.g., corrupt JPEG data) |
| `ReportGenerationError` | PDF creation fails |

### Layer 4: Validation Module

`src/utils/file_validator.py` raises `InvalidFileTypeError` or `FileTooLargeError` before the file is ever passed to the ML pipeline. This prevents unnecessary computation on invalid inputs.

---

## 8. Session Management

Flask's built-in cookie-based session is used to:
1. Store the `session_id` (UUID) generated per analysis
2. Track temp file paths associated with the session
3. Gate report download to the session that performed the analysis

```python
import uuid
from flask import session

# In the /analyze route, after successful analysis:
session_id = str(uuid.uuid4())
session['session_id'] = session_id
session['temp_files'] = {
    'upload': upload_path,
    'ela': ela_image_path
}
session['analysis_result'] = {
    'prediction': prediction,
    'confidence': float(confidence),
    'model_used': model_name,
    'timestamp': datetime.utcnow().isoformat()
}
```

> [!NOTE]
> Flask's default cookie-based session stores data client-side (signed, not encrypted). The temp file paths stored in the session are not sensitive — they are UUIDs on disk. The `SECRET_KEY` ensures session integrity (tamper detection).

**Session lifetime:** Flask's default session expires when the browser is closed (session cookie). Temp files are cleaned up either on report download or by a background cleanup task that removes files older than 1 hour.

---

## 9. Temp File Management

Since the system must not permanently store uploaded images, all file I/O is strictly temporary.

### Directory Structure

```
temp/
├── uploads/
│   └── {session_id}/
│       └── {secure_filename}       # The uploaded image
└── reports/
    └── report_{session_id}.pdf     # Generated PDF (brief existence)
```

### Lifecycle

```
1. POST /analyze received
   → Create: temp/uploads/{session_id}/{filename}
   → Store path in Flask session

2. ELA generator reads upload
   → Generates ELA image in memory or temp/uploads/{session_id}/ela_{filename}

3. result.html rendered (image URLs served from temp folder)

4. GET /report/{session_id} received
   → PDF generated and streamed (may write to temp/reports/ briefly)
   → After streaming: cleanup() called

5. Cleanup: os.remove() on all tracked temp files
            os.rmdir() on session temp directory (if empty)
```

### Cleanup Function

```python
def cleanup_session_files(session_id: str, file_paths: list):
    """Remove temporary files associated with a session.

    Args:
        session_id (str): The session UUID for logging.
        file_paths (list): List of absolute file paths to delete.
    """
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Cleaned up temp file: {path} (session: {session_id})")
        except OSError as e:
            logger.warning(f"Failed to clean up {path}: {e}")
```

> [!CAUTION]
> Never serve files from the temp upload directory using `send_from_directory` with user-supplied paths. Always validate that the path matches the session-stored path before serving.

---

## 10. Security Measures

The backend implements multiple overlapping security controls for file upload handling:

### 10.1 `secure_filename()` from Werkzeug

All uploaded filenames are sanitized before use:

```python
from werkzeug.utils import secure_filename

safe_name = secure_filename(file.filename)
# "../../etc/passwd" → "etc_passwd" or empty string
# "photo (1).jpg" → "photo_1_.jpg"
```

If `secure_filename()` returns an empty string (e.g., the filename was entirely composed of unsafe characters), the upload is rejected.

### 10.2 File Magic Bytes Verification

Checking the file extension alone is insufficient — a user could rename a PHP script to `photo.jpg`. The backend reads the first few bytes of the uploaded file and verifies against known image signatures:

```python
MAGIC_BYTES = {
    'jpg':  [b'\xff\xd8\xff'],
    'jpeg': [b'\xff\xd8\xff'],
    'png':  [b'\x89PNG\r\n\x1a\n'],
}

def verify_magic_bytes(file_stream, extension: str) -> bool:
    header = file_stream.read(16)
    file_stream.seek(0)  # Reset stream after reading
    for magic in MAGIC_BYTES.get(extension, []):
        if header.startswith(magic):
            return True
    return False
```

### 10.3 Extension Whitelist

Only extensions in `ALLOWED_EXTENSIONS` (`{'jpg', 'jpeg', 'png'}`) pass validation. The check is case-insensitive and operates on the last extension component only.

```python
def allowed_file(filename: str, allowed_extensions: set) -> bool:
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in allowed_extensions)
```

### 10.4 `MAX_CONTENT_LENGTH` Enforcement

Flask enforces the size limit at the WSGI level before the request body is fully read. When `MAX_CONTENT_LENGTH = 16 * 1024 * 1024`, Flask automatically returns HTTP 413 for requests exceeding this size. This prevents memory exhaustion from large file uploads.

### 10.5 Session-Based Report Access Control

The `GET /report/<session_id>` endpoint verifies that the requested `session_id` matches the `session_id` stored in the current user's Flask session. This prevents one user from downloading another user's report by guessing UUIDs.

```python
@detection_bp.route('/report/<session_id>')
def download_report(session_id):
    if session.get('session_id') != session_id:
        abort(404)
    # ... proceed to generate and stream PDF
```

### 10.6 No Directory Traversal

Upload paths are constructed using `os.path.join()` with a fixed base (`UPLOAD_FOLDER / session_id / secure_filename`). The `secure_filename()` sanitization prevents directory traversal sequences (`../`) from appearing in the final path.

### Summary Table

| Security Control | Threat Mitigated |
|---|---|
| `secure_filename()` | Path traversal via filename |
| Magic bytes check | Disguised file types (e.g., script renamed to `.jpg`) |
| Extension whitelist | Unexpected file types reaching the ML pipeline |
| `MAX_CONTENT_LENGTH` | Memory exhaustion / DoS via large uploads |
| Session-scoped report access | Cross-session report enumeration |
| Temp file cleanup | Data retention / privacy |
| No permanent storage | GDPR/privacy — uploaded images are not kept |
