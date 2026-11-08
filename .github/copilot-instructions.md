# GitHub Copilot Instructions

> These instructions configure GitHub Copilot's behaviour for the **Image Manipulation Detection System** repository.
> Copilot should read this file and apply its guidance to every suggestion it makes.

---

## 1. Project Context

This is a **deep-learning image forensics application** built by a 4-person student team over 4–6 weeks.

- Users upload a JPEG or PNG image via a web form.
- The system generates an **Error Level Analysis (ELA)** visualization using JPEG recompression.
- A trained **Custom CNN** or **MobileNetV2** classification model predicts whether the image has been digitally manipulated.
- Results are displayed on a Bootstrap 5 dashboard with the ELA image, a confidence score, and a mandatory disclaimer.
- **No database** is used. No user images are stored permanently.

Training data: **CASIA v1.0** (1,721 images) + **CASIA v2.0** (12,614 images).  
Label convention: filename prefix `Au_` → authentic (0), `Tp_` → manipulated (1).

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Web Framework | Flask (latest stable) |
| ML Framework | TensorFlow 2.x / Keras |
| Image Processing | Pillow (PIL), NumPy |
| Data Processing | Pandas, scikit-learn |
| Frontend | Bootstrap 5, Jinja2 templates |
| Testing | pytest |
| Utilities | Werkzeug, python-dotenv |

> [!IMPORTANT]
> Do **not** suggest OpenCV for ELA generation — PIL/Pillow only for `ela_generator.py`.
> Do **not** suggest PyTorch — this project uses TensorFlow/Keras exclusively.
> Do **not** suggest SQLAlchemy or any ORM — there is no database.

---

## 3. Code Style Preferences

### 3.1 Docstrings — Google Style (always)
```python
def build_cnn_model(input_shape: tuple[int, int, int] = (224, 224, 3)) -> tf.keras.Model:
    """Build and compile the custom CNN model for binary image classification.

    Args:
        input_shape: Height, width, and channel count of the input tensor.
            Defaults to (224, 224, 3).

    Returns:
        A compiled tf.keras.Model with binary crossentropy loss and Adam optimizer.

    Raises:
        ValueError: If input_shape dimensions are invalid (non-positive integers).
    """
```

### 3.2 Type Hints — Always
```python
# ✅ Correct
def validate_file(filename: str, file_bytes: bytes) -> tuple[bool, str]:

# ❌ Wrong — missing type hints
def validate_file(filename, file_bytes):
```

Use `from __future__ import annotations` at the top of each file.  
Use `Optional[T]` or `T | None` for nullable types.  
Use `list[T]`, `dict[K, V]`, `tuple[T, ...]` (lowercase, PEP 585) in Python 3.11.

### 3.3 PEP 8
- **Max line length: 100 characters**
- 4 spaces indentation, never tabs
- Two blank lines between top-level definitions; one blank line between methods
- Imports order: stdlib → third-party → local (`src/`)

### 3.4 Exception Handling — Always Explicit
```python
# ✅ Correct
try:
    img = Image.open(image_path)
except FileNotFoundError as e:
    logger.error("Image not found: %s — %s", image_path, e)
    raise
except OSError as e:
    logger.error("Cannot open image %s: %s", image_path, e)
    raise ValueError(f"Corrupt or unreadable image file: {image_path}") from e

# ❌ Forbidden — bare except
try:
    img = Image.open(image_path)
except:
    pass
```

### 3.5 Logging — Use Project Logger
```python
from src.utils.logger import get_logger
logger = get_logger(__name__)

# Use structured log messages
logger.info("Processing image: %s (size=%d bytes)", filename, file_size)
logger.warning("PNG input to ELA generator — result reliability is reduced")
logger.error("Model prediction failed: %s", error_message)
```

**Never use `print()` in production modules** (src/, web/).

---

## 4. Architecture Context

> [!IMPORTANT]
> Copilot must respect module boundaries. Do not suggest code that crosses these boundaries.

### 4.1 Module Responsibilities

```
src/models/
  cnn_model.py        → def build_cnn_model(input_shape) -> Model
  mobilenet_model.py  → def build_mobilenet_model(input_shape, trainable_layers) -> Model
  model_loader.py     → ModelLoader class — loads models from artifacts/models/ at startup
  predictor.py        → ModelPredictor class — runs inference, returns PredictionResult

src/preprocessing/
  ela_generator.py    → ELAGenerator class — JPEG recompression ELA, PIL only
  image_loader.py     → ImageLoader class — open + validate PIL images
  image_resizer.py    → ImageResizer class — resize to target dimensions
  image_normalizer.py → ImageNormalizer class — normalize pixel values to [0,1]

src/services/
  detection_service.py → DetectionService — orchestrates preprocessing + prediction
  ela_service.py       → ELAService — wraps ELAGenerator, manages temp file lifecycle
  report_service.py    → ReportService — builds downloadable HTML/PDF report

src/utils/
  file_validator.py   → FileValidator class — extension + MIME type + size checks
  image_utils.py      → utility functions for image format detection
  logger.py           → get_logger(name) factory function
  exceptions.py       → project-specific exception classes

web/routes/
  main_routes.py      → GET /, GET /about, GET /health
  detection_routes.py → POST /analyze, GET /report/<session_id>
```

### 4.2 Dependency Flow (no circular imports)

```
web/routes → src/services → src/models + src/preprocessing + src/utils
                          ↑
                     src/data (dataset loading)
```

- Routes **never** import from `src/models/` directly — always through `src/services/`.
- Services **never** import from `web/`.
- `src/utils/` is imported by all other `src/` subpackages but imports nothing from them.

### 4.3 Request Lifecycle

1. `detection_routes.py` receives multipart POST
2. `FileValidator.validate()` checks extension, MIME, size
3. File saved to `temp/{session_id}/{secure_filename}`
4. `DetectionService.analyze()` called with temp path
5. Inside service: `ELAGenerator.generate()` → `ModelPredictor.predict()`
6. Result dict returned to route → `render_template('result.html', **result)`
7. Temp file scheduled for deletion after session timeout

---

## 5. Auto-complete Guidance

### When writing a new function:
1. Write the function signature with full type hints **first**
2. Write the Google-style docstring **second**
3. Then implement the body

### When writing a new class:
1. Check `src/` for a similar class: `grep -r "class.*:" src/`
2. If similar exists, extend or reuse it — do not duplicate
3. Add `__repr__` and use dataclasses where state is simple

### For ML/model code:
1. Check `src/training/` for existing training utilities
2. Use `Config.*` for all hyperparameters (learning rate, dropout, batch size)
3. Use TensorFlow 2.x functional API or Sequential — never TF 1.x `compat.v1`
4. Input shape is always `(224, 224, 3)` — from `Config.IMAGE_SIZE`

### For route handlers:
1. Never inline validation — always call `FileValidator`
2. Never inline ML code — always call `DetectionService`
3. Always call `secure_filename()` on uploaded filenames
4. Return `render_template(...)` on success; return JSON `{status, message, code}` on error

---

## 6. What Copilot Should NOT Suggest

| ❌ Anti-pattern | ✅ Correct Alternative |
|----------------|----------------------|
| `except:` or `except Exception:` with no handling | Catch specific exceptions with logging |
| `"/absolute/path/to/model.h5"` hardcoded paths | `Config.MODEL_DIR / "cnn_model_v1.keras"` |
| `model = tf.keras.models.load_model(...)` inside a route | Model loaded at startup by `ModelLoader` |
| `from flask_sqlalchemy import SQLAlchemy` | No database — remove entirely |
| `from flask_login import login_required` | No authentication in this project |
| `import cv2` in `ela_generator.py` | Use `PIL.Image` and `PIL.ImageChops` |
| `torch.nn.Module` or any PyTorch | TensorFlow/Keras only |
| `model.predict(image_array)` returning a label string | `ModelPredictor` returns a `PredictionResult` dataclass |
| Commented-out code blocks | Clean code only |
| `# TODO: implement later` on a function that is being written | Implement it now or raise `NotImplementedError` |

---

## 7. File / Module Responsibilities Quick Reference

| File | Exports / Purpose |
|------|-------------------|
| `config.py` | `Config` class with all constants — image size, paths, limits, thresholds |
| `app.py` | Flask application factory `create_app()` — registers blueprints, loads models |
| `src/utils/exceptions.py` | `ValidationError`, `PredictionError`, `ELAError`, `ModelLoadError` |
| `src/utils/logger.py` | `get_logger(name: str) -> logging.Logger` |
| `src/utils/file_validator.py` | `FileValidator.validate(filename, stream) -> tuple[bool, str]` |
| `src/preprocessing/ela_generator.py` | `ELAGenerator.generate(path, quality, factor) -> PIL.Image.Image` |
| `src/preprocessing/image_loader.py` | `ImageLoader.load(path) -> PIL.Image.Image` |
| `src/preprocessing/image_resizer.py` | `ImageResizer.resize(image, target_size) -> PIL.Image.Image` |
| `src/preprocessing/image_normalizer.py` | `ImageNormalizer.normalize(image) -> np.ndarray` |
| `src/models/model_loader.py` | `ModelLoader.load(model_name) -> tf.keras.Model` |
| `src/models/predictor.py` | `ModelPredictor.predict(image_array) -> PredictionResult` |
| `src/services/detection_service.py` | `DetectionService.analyze(image_path, model_name) -> DetectionResult` |
| `web/routes/detection_routes.py` | `POST /analyze`, `GET /report/<session_id>` |
| `web/routes/main_routes.py` | `GET /`, `GET /about`, `GET /health` |
| `tests/conftest.py` | `app`, `client`, `synthetic_jpeg`, `synthetic_png` fixtures |
