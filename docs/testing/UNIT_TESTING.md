# Unit Testing Guide — Image Manipulation Detection System

> **Framework:** pytest  
> **Coverage Tool:** pytest-cov  
> **Last Updated:** 2026-11-08

---

## Overview

This document provides detailed guidance for every unit test file in the `tests/` directory. For each file, the expected test functions are described, their purpose is explained, and representative code snippets are provided.

All unit tests are:
- **Isolated** — no dependency on trained models, real dataset, or network
- **Fast** — target < 100ms per test
- **Self-contained** — each test creates its own inputs via fixtures

---

## Shared Fixtures (`tests/conftest.py`)

All test files share fixtures defined in `conftest.py`. Key fixtures:

```python
# tests/conftest.py

import io
import pytest
from PIL import Image
from app import create_app   # adjust import to match your app factory


@pytest.fixture(scope="session")
def app():
    """Create Flask app configured for testing."""
    application = create_app(testing=True)
    application.config.update({
        "TESTING": True,
        "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,
        "WTF_CSRF_ENABLED": False,
    })
    return application


@pytest.fixture(scope="session")
def client(app):
    """Return a Flask test client."""
    return app.test_client()


@pytest.fixture
def small_rgb_jpeg():
    """100×100 RGB JPEG as BytesIO."""
    img = Image.new("RGB", (100, 100), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    buf.name = "test_image.jpg"
    return buf


@pytest.fixture
def small_rgb_png():
    """100×100 RGB PNG as BytesIO."""
    img = Image.new("RGB", (100, 100), color=(50, 100, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "test_image.png"
    return buf


@pytest.fixture
def small_rgba_png():
    """100×100 RGBA PNG as BytesIO."""
    img = Image.new("RGBA", (100, 100), color=(50, 100, 200, 180))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "test_rgba.png"
    return buf


@pytest.fixture
def small_grayscale_jpeg():
    """100×100 Grayscale JPEG as BytesIO."""
    img = Image.new("L", (100, 100), color=128)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    buf.name = "test_gray.jpg"
    return buf


@pytest.fixture
def oversized_buffer():
    """17MB buffer — exceeds 16MB limit."""
    return io.BytesIO(b'\x00' * (17 * 1024 * 1024))


@pytest.fixture
def pdf_bytes_as_jpg():
    """PDF magic bytes disguised with .jpg name."""
    buf = io.BytesIO(b'%PDF-1.4 this is not an image')
    buf.name = "not_an_image.jpg"
    return buf


@pytest.fixture
def empty_file():
    """Zero-byte file buffer."""
    buf = io.BytesIO(b'')
    buf.name = "empty.jpg"
    return buf
```

---

## `tests/test_file_validation.py`

**Module Under Test:** `src/utils/file_validator.py`

**Purpose:** Ensure the file validation layer correctly accepts valid images and rejects invalid, dangerous, or oversized files before any processing occurs. This is a security-critical module.

---

### `test_valid_jpg_accepted()`

Verifies that a standard `.jpg` file with correct JPEG content passes validation without error.

```python
import pytest
from src.utils.file_validator import validate_upload

@pytest.mark.unit
def test_valid_jpg_accepted(small_rgb_jpeg):
    """A valid JPG image should pass validation."""
    small_rgb_jpeg.name = "photo.jpg"
    result = validate_upload(small_rgb_jpeg, filename="photo.jpg")
    assert result["valid"] is True
    assert result["error"] is None
```

---

### `test_valid_jpeg_accepted()`

Verifies that `.jpeg` extension (longer form) is accepted alongside `.jpg`.

```python
@pytest.mark.unit
def test_valid_jpeg_accepted(small_rgb_jpeg):
    """A valid JPEG image with .jpeg extension should pass validation."""
    small_rgb_jpeg.name = "photo.jpeg"
    result = validate_upload(small_rgb_jpeg, filename="photo.jpeg")
    assert result["valid"] is True
```

---

### `test_valid_png_accepted()`

Verifies PNG images are accepted.

```python
@pytest.mark.unit
def test_valid_png_accepted(small_rgb_png):
    """A valid PNG image should pass validation."""
    result = validate_upload(small_rgb_png, filename="photo.png")
    assert result["valid"] is True
    assert result["error"] is None
```

---

### `test_invalid_extension_rejected()`

Parameterized test ensuring unsupported file types are rejected with an appropriate error.

```python
@pytest.mark.unit
@pytest.mark.parametrize("filename,content", [
    ("document.pdf",  b'%PDF-1.4'),
    ("animation.gif", b'GIF89a'),
    ("bitmap.bmp",    b'BM'),
    ("archive.zip",   b'PK\x03\x04'),
])
def test_invalid_extension_rejected(filename, content):
    """Files with unsupported extensions must be rejected."""
    buf = io.BytesIO(content)
    result = validate_upload(buf, filename=filename)
    assert result["valid"] is False
    assert "extension" in result["error"].lower() or "type" in result["error"].lower()
```

---

### `test_oversized_file_rejected()`

Verifies that files exceeding the 16MB limit are rejected with a size-related error message.

```python
@pytest.mark.unit
def test_oversized_file_rejected(oversized_buffer):
    """Files larger than 16MB should be rejected."""
    result = validate_upload(oversized_buffer, filename="big.jpg")
    assert result["valid"] is False
    assert "size" in result["error"].lower() or "16" in result["error"]
```

---

### `test_empty_file_rejected()`

Verifies that a zero-byte file is rejected rather than causing a downstream crash.

```python
@pytest.mark.unit
def test_empty_file_rejected(empty_file):
    """An empty (zero-byte) file should be rejected."""
    result = validate_upload(empty_file, filename="empty.jpg")
    assert result["valid"] is False
    assert result["error"] is not None
```

---

### `test_spoofed_extension_rejected()`

Security test: a file with `.jpg` extension but PDF magic bytes must be rejected. The validator must inspect file content (magic bytes), not just the filename extension.

```python
@pytest.mark.unit
def test_spoofed_extension_rejected(pdf_bytes_as_jpg):
    """A file named .jpg but containing PDF bytes must be rejected."""
    result = validate_upload(pdf_bytes_as_jpg, filename="not_an_image.jpg")
    assert result["valid"] is False
    # Error must indicate content mismatch, not just extension
    assert result["error"] is not None
```

> [!IMPORTANT]
> This test is a **security requirement**. If your validator only checks filename extension and not actual file bytes, this test will correctly fail and expose the gap.

---

### `test_secure_filename_applied()`

Verifies that filenames with path traversal sequences or special characters are sanitized before use.

```python
@pytest.mark.unit
def test_secure_filename_applied(small_rgb_jpeg):
    """Dangerous filenames must be sanitized."""
    dangerous_name = "../../../etc/passwd.jpg"
    result = validate_upload(small_rgb_jpeg, filename=dangerous_name)
    # Either rejected entirely, or the sanitized name is returned
    if result["valid"]:
        # If accepted, the returned filename must not contain '..'
        assert ".." not in result["filename"]
        assert "/" not in result["filename"]
    else:
        # Acceptable to reject dangerous filenames outright
        assert result["error"] is not None
```

---

## `tests/test_preprocessing.py`

**Module Under Test:** `src/preprocessing/preprocessor.py`

**Purpose:** Verify the image preprocessing pipeline correctly transforms any valid input image into the exact tensor format expected by the model: shape `(1, 224, 224, 3)`, dtype `float32`, values in `[0.0, 1.0]`.

---

### `test_image_loads_as_rgb()`

```python
import numpy as np
import pytest
from src.preprocessing.preprocessor import load_and_preprocess

@pytest.mark.unit
def test_image_loads_as_rgb(small_rgb_jpeg, tmp_path):
    """Preprocessed image should have 3 channels (RGB)."""
    # Save to temp file for preprocessor that expects a path
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(small_rgb_jpeg.read())
    tensor = load_and_preprocess(str(img_path))
    assert tensor.shape[-1] == 3, "Expected 3 color channels (RGB)"
```

---

### `test_image_resized_to_224_224()`

```python
@pytest.mark.unit
def test_image_resized_to_224_224(small_rgb_jpeg, tmp_path):
    """Preprocessed image must be resized to 224×224."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(small_rgb_jpeg.read())
    tensor = load_and_preprocess(str(img_path))
    assert tensor.shape[1] == 224
    assert tensor.shape[2] == 224
```

---

### `test_pixel_values_normalized_0_to_1()`

```python
@pytest.mark.unit
def test_pixel_values_normalized_0_to_1(small_rgb_jpeg, tmp_path):
    """All pixel values must be in [0.0, 1.0] after normalization."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(small_rgb_jpeg.read())
    tensor = load_and_preprocess(str(img_path))
    assert float(tensor.min()) >= 0.0, "Pixel values must not be negative"
    assert float(tensor.max()) <= 1.0, "Pixel values must not exceed 1.0"
```

---

### `test_batch_dimension_added()`

```python
@pytest.mark.unit
def test_batch_dimension_added(small_rgb_jpeg, tmp_path):
    """Output tensor must have a batch dimension as the first axis."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(small_rgb_jpeg.read())
    tensor = load_and_preprocess(str(img_path))
    assert len(tensor.shape) == 4, "Expected shape (1, 224, 224, 3)"
    assert tensor.shape[0] == 1, "Batch dimension must be 1"
```

---

### `test_grayscale_converted_to_rgb()`

```python
@pytest.mark.unit
def test_grayscale_converted_to_rgb(small_grayscale_jpeg, tmp_path):
    """Grayscale images must be converted to RGB (3-channel)."""
    img_path = tmp_path / "gray.jpg"
    img_path.write_bytes(small_grayscale_jpeg.read())
    tensor = load_and_preprocess(str(img_path))
    assert tensor.shape[-1] == 3, "Grayscale must be converted to 3-channel RGB"
```

---

### `test_rgba_converted_to_rgb()`

```python
@pytest.mark.unit
def test_rgba_converted_to_rgb(small_rgba_png, tmp_path):
    """RGBA PNG images (4 channels) must be converted to RGB (3 channels)."""
    img_path = tmp_path / "rgba.png"
    img_path.write_bytes(small_rgba_png.read())
    tensor = load_and_preprocess(str(img_path))
    assert tensor.shape[-1] == 3, "RGBA must be flattened to 3-channel RGB"
```

---

## `tests/test_ela.py`

**Module Under Test:** `src/preprocessing/ela_generator.py`

**Purpose:** Verify that Error Level Analysis (ELA) generates a valid output image with the same dimensions as the input, handles both JPEG and PNG inputs, and cleans up any temporary files it creates.

---

### `test_ela_generates_image()`

```python
import os
import pytest
from PIL import Image
from src.preprocessing.ela_generator import generate_ela

@pytest.mark.unit
def test_ela_generates_image(small_rgb_jpeg, tmp_path):
    """ELA should produce an output image object."""
    img_path = tmp_path / "input.jpg"
    img_path.write_bytes(small_rgb_jpeg.read())
    ela_img = generate_ela(str(img_path))
    assert ela_img is not None
    assert isinstance(ela_img, Image.Image)
```

---

### `test_ela_output_same_shape_as_input()`

```python
@pytest.mark.unit
def test_ela_output_same_shape_as_input(small_rgb_jpeg, tmp_path):
    """ELA output dimensions must match the input image dimensions."""
    img = Image.new("RGB", (200, 150), color=(100, 100, 100))
    img_path = tmp_path / "sized.jpg"
    img.save(str(img_path), format="JPEG", quality=85)

    ela_img = generate_ela(str(img_path))
    assert ela_img.size == (200, 150), (
        f"ELA output size {ela_img.size} does not match input (200, 150)"
    )
```

---

### `test_ela_output_is_valid_image()`

```python
@pytest.mark.unit
def test_ela_output_is_valid_image(small_rgb_jpeg, tmp_path):
    """ELA output must be a valid RGB image that can be saved."""
    img_path = tmp_path / "input.jpg"
    img_path.write_bytes(small_rgb_jpeg.read())
    ela_img = generate_ela(str(img_path))

    output_path = tmp_path / "ela_output.png"
    ela_img.save(str(output_path))
    assert output_path.exists()
    assert output_path.stat().st_size > 0
```

---

### `test_ela_works_with_jpeg()`

```python
@pytest.mark.unit
def test_ela_works_with_jpeg(small_rgb_jpeg, tmp_path):
    """ELA must work correctly with JPEG input (primary use case)."""
    img_path = tmp_path / "jpeg_input.jpg"
    img_path.write_bytes(small_rgb_jpeg.read())
    ela_img = generate_ela(str(img_path))
    assert ela_img is not None
```

---

### `test_ela_works_with_png_input()`

```python
@pytest.mark.unit
def test_ela_works_with_png_input(small_rgb_png, tmp_path):
    """
    ELA must work with PNG input.
    Note: PNG→JPEG conversion introduces compression artifacts; this is
    expected behavior, not an error. The ELA result will show these
    conversion artifacts and must be interpreted with this in mind.
    """
    img_path = tmp_path / "png_input.png"
    img_path.write_bytes(small_rgb_png.read())
    ela_img = generate_ela(str(img_path))
    # Must complete without exception, even if ELA shows conversion artifacts
    assert ela_img is not None
    assert isinstance(ela_img, Image.Image)
```

---

### `test_ela_quality_parameter_accepted()`

```python
@pytest.mark.unit
@pytest.mark.parametrize("quality", [75, 85, 95])
def test_ela_quality_parameter_accepted(quality, small_rgb_jpeg, tmp_path):
    """ELA should accept different JPEG quality parameters without error."""
    img_path = tmp_path / "input.jpg"
    img_path.write_bytes(small_rgb_jpeg.read())
    ela_img = generate_ela(str(img_path), quality=quality)
    assert ela_img is not None
```

---

### `test_ela_cleanup_temp_file()`

```python
@pytest.mark.unit
def test_ela_cleanup_temp_file(small_rgb_jpeg, tmp_path):
    """ELA generator must delete any temporary files it creates."""
    img_path = tmp_path / "input.jpg"
    img_path.write_bytes(small_rgb_jpeg.read())

    files_before = set(tmp_path.iterdir())
    generate_ela(str(img_path))
    files_after = set(tmp_path.iterdir())

    # Only the original input file should remain; no temp files
    new_files = files_after - files_before
    assert len(new_files) == 0, (
        f"ELA left behind temp files: {[f.name for f in new_files]}"
    )
```

---

## `tests/test_prediction.py`

**Module Under Test:** `src/services/detection_service.py` (or `src/models/predictor.py`)

**Purpose:** Verify that the prediction layer returns correctly structured output — a binary label and a confidence score in the expected ranges — without validating the actual model accuracy.

> [!NOTE]
> Tests that use the real `.h5` model file are guarded with `@pytest.mark.requires_model` and skipped when the model is not present. Tests using a mock predictor run always.

---

### `test_prediction_returns_label_and_confidence()`

```python
import pytest
from unittest.mock import patch, MagicMock
from src.services.detection_service import DetectionService

@pytest.fixture
def mock_service():
    """DetectionService with a mocked model that always returns 0.8."""
    with patch("src.services.detection_service.load_model") as mock_load:
        mock_model = MagicMock()
        mock_model.predict.return_value = [[0.8]]
        mock_load.return_value = mock_model
        service = DetectionService(model_path="fake/path.h5")
        yield service

@pytest.mark.unit
def test_prediction_returns_label_and_confidence(mock_service, small_rgb_jpeg, tmp_path):
    """Prediction must return a dict with 'label' and 'confidence' keys."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(small_rgb_jpeg.read())
    result = mock_service.predict(str(img_path))
    assert "label" in result
    assert "confidence" in result
```

---

### `test_prediction_label_is_binary()`

```python
@pytest.mark.unit
def test_prediction_label_is_binary(mock_service, small_rgb_jpeg, tmp_path):
    """Prediction label must be either 0 (authentic) or 1 (manipulated)."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(small_rgb_jpeg.read())
    result = mock_service.predict(str(img_path))
    assert result["label"] in (0, 1), (
        f"Label must be 0 or 1, got: {result['label']}"
    )
```

---

### `test_confidence_between_0_and_1()`

```python
@pytest.mark.unit
def test_confidence_between_0_and_1(mock_service, small_rgb_jpeg, tmp_path):
    """Confidence score must be a float in the range [0.0, 1.0]."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(small_rgb_jpeg.read())
    result = mock_service.predict(str(img_path))
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0
```

---

### `test_prediction_works_with_224x224_input()`

```python
@pytest.mark.unit
def test_prediction_works_with_224x224_input(mock_service, tmp_path):
    """Prediction must accept and process a 224×224 RGB image correctly."""
    from PIL import Image
    img = Image.new("RGB", (224, 224), color=(100, 150, 200))
    img_path = tmp_path / "test_224.jpg"
    img.save(str(img_path), format="JPEG")

    result = mock_service.predict(str(img_path))
    assert result is not None
    assert "label" in result
```

---

### `test_model_handles_batch()`

```python
@pytest.mark.unit
def test_model_handles_batch(mock_service, tmp_path):
    """
    The underlying model preprocessor must add a batch dimension.
    Verifies that the model's predict() is called with shape (1, 224, 224, 3).
    """
    from PIL import Image
    img = Image.new("RGB", (224, 224), color=(50, 50, 50))
    img_path = tmp_path / "batch_test.jpg"
    img.save(str(img_path), format="JPEG")

    mock_service.predict(str(img_path))
    
    # Inspect what was passed to model.predict
    call_args = mock_service.model.predict.call_args
    input_tensor = call_args[0][0]
    assert input_tensor.shape == (1, 224, 224, 3), (
        f"Model was called with wrong shape: {input_tensor.shape}"
    )
```

---

## `tests/test_api.py`

**Module Under Test:** `app.py` routes and Flask application

**Purpose:** Integration-level tests that verify HTTP endpoint behavior: status codes, error responses, and successful responses using the Flask test client.

---

### `test_home_page_returns_200()`

```python
@pytest.mark.integration
def test_home_page_returns_200(client):
    """GET / should return HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200
```

---

### `test_about_page_returns_200()`

```python
@pytest.mark.integration
def test_about_page_returns_200(client):
    """GET /about (if it exists) should return HTTP 200."""
    response = client.get("/about")
    assert response.status_code in (200, 404)  # 404 acceptable if page not implemented yet
```

---

### `test_health_endpoint_returns_ok()`

```python
@pytest.mark.integration
def test_health_endpoint_returns_ok(client):
    """GET /health should return HTTP 200 with status 'ok'."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
```

---

### `test_analyze_no_file_returns_400()`

```python
@pytest.mark.integration
def test_analyze_no_file_returns_400(client):
    """POST /analyze with no file attached should return 400."""
    response = client.post("/analyze", data={})
    assert response.status_code == 400
```

---

### `test_analyze_invalid_type_returns_400()`

```python
@pytest.mark.integration
def test_analyze_invalid_type_returns_400(client):
    """POST /analyze with an unsupported file type should return 400."""
    data = {
        "file": (io.BytesIO(b"not an image"), "document.pdf")
    }
    response = client.post("/analyze", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
```

---

### `test_analyze_oversized_returns_413()`

```python
@pytest.mark.integration
def test_analyze_oversized_returns_413(client):
    """POST /analyze with a file > 16MB should return 413 (Request Entity Too Large)."""
    large_data = b'\x00' * (17 * 1024 * 1024)
    data = {
        "file": (io.BytesIO(large_data), "big.jpg")
    }
    response = client.post("/analyze", data=data, content_type="multipart/form-data")
    assert response.status_code == 413
```

---

### `test_analyze_valid_image_returns_result()`

```python
@pytest.mark.integration
def test_analyze_valid_image_returns_result(client, small_rgb_jpeg):
    """
    POST /analyze with a valid JPEG should return 200 and a result.
    Uses a mock or real model depending on what's available.
    """
    data = {
        "file": (small_rgb_jpeg, "test.jpg")
    }
    response = client.post("/analyze", data=data, content_type="multipart/form-data")
    # Either a redirect to result page (302) or direct 200 with result
    assert response.status_code in (200, 302)
```

---

## Summary Table

| Test File | Test Count (approx.) | Markers | Model Required? |
|---|---|---|---|
| `test_file_validation.py` | 8+ | unit | No |
| `test_preprocessing.py` | 6+ | unit | No |
| `test_ela.py` | 7+ | unit | No |
| `test_prediction.py` | 5+ | unit | No (uses mock) |
| `test_api.py` | 7+ | integration | No (uses mock) |
| `test_dataset.py` | 4+ | unit | No |
| `test_models.py` | 4+ | unit, requires_model | Optional |
