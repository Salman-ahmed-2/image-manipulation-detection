# AGENTS.md — AI Coding Agent Instructions

> This file is authoritative configuration for all AI coding agents working on this repository —
> GitHub Copilot, Gemini, Claude, ChatGPT, Cursor, and any other assistant.
> **Read this file before writing a single line of code.**

---

## 1. Project Summary

This is a **4-person student team project** (4–6 weeks) that builds an image manipulation detection system using deep learning. The system accepts a user-uploaded JPEG or PNG image, generates an Error Level Analysis (ELA) visualization using JPEG recompression, and feeds both the original and ELA image into one of two trained classification models — a **Custom CNN** or a **MobileNetV2 transfer learning model** — to predict whether the image has been digitally manipulated. Training data is sourced from the **CASIA v1.0** (1,721 images) and **CASIA v2.0** (12,614 images) benchmark datasets. The user-facing interface is a **Flask + Bootstrap 5** web application. No database is used; image data is processed in memory and stored only temporarily in a session-scoped temp folder.

---

## 2. BEFORE YOU CODE — Required Reading

Do **not** generate new code until you have read (or been shown the contents of) the following documents:

| Priority | File | Why It Matters |
|----------|------|----------------|
| 🔴 CRITICAL | `docs/PROJECT_OVERVIEW.md` | Project goals, scope, and constraints |
| 🔴 CRITICAL | `docs/architecture/SYSTEM_ARCHITECTURE.md` | End-to-end system design |
| 🔴 CRITICAL | `docs/architecture/COMPONENT_ARCHITECTURE.md` | Module responsibilities and boundaries |
| 🟠 HIGH | `docs/dataset/DATASET_OVERVIEW.md` | CASIA dataset structure and label convention |
| 🟠 HIGH | `docs/machine_learning/ML_OVERVIEW.md` | Model selection rationale and training approach |
| 🟠 HIGH | `docs/image_forensics/ELA_OVERVIEW.md` | ELA theory, limitations, and implementation notes |
| 🟡 MEDIUM | `docs/application/BACKEND_DOCUMENTATION.md` | Flask route design and service layer |
| 🟡 MEDIUM | `docs/application/FRONTEND_DOCUMENTATION.md` | Template variables and UI conventions |
| 🟡 MEDIUM | `docs/testing/UNIT_TESTING.md` | Test patterns and fixture conventions |

---

## 3. Project Structure Map

```
image-manipulation-detection/
│
├── app.py                  # Flask application factory
├── config.py               # ALL constants live here — paths, hyperparams, limits
├── run.py                  # Development entry point
├── requirements.txt        # Pinned dependencies
│
├── data/                   # Dataset storage (see data/README.md)
│   ├── raw/                # READ-ONLY: original CASIA v1.0 and v2.0 images
│   ├── annotations/        # Ground-truth manipulation masks
│   ├── processed/          # Resized/normalized images ready for training
│   ├── splits/             # train / validation / test splits
│   └── metadata/           # CSV inventory and label files
│
├── src/                    # All Python source code (see src/README.md)
│   ├── data/               # Dataset loading, splitting, validation, augmentation
│   ├── evaluation/         # Metrics, confusion matrix, training curve plots
│   ├── explainability/     # Grad-CAM (optional — implement AFTER core pipeline)
│   ├── models/             # Model architectures + loader + predictor
│   ├── preprocessing/      # ELA generator, image loading, resizing, normalization
│   ├── services/           # Business logic: detection_service, ela_service, report_service
│   ├── training/           # Training loop, callbacks, checkpointing
│   └── utils/              # file_validator, image_utils, logger, exceptions
│
├── web/                    # Flask web layer (see web/README.md)
│   ├── routes/             # Route handlers — NO business logic here
│   ├── templates/          # Jinja2 HTML templates
│   └── static/             # CSS and JS assets
│
├── scripts/                # Standalone CLI scripts (not imported by src/)
│   ├── prepare_dataset.py  # Scan raw data, generate metadata CSVs, split dataset
│   ├── train.py            # Kick off model training
│   ├── evaluate.py         # Evaluate trained model on test split
│   └── cleanup.py          # Remove temp files and old artifacts
│
├── tests/                  # pytest tests (see tests/README.md)
│   ├── conftest.py         # Shared fixtures: app, client, synthetic test images
│   └── test_*.py           # One file per module under test
│
├── notebooks/              # Jupyter notebooks for exploration (not production code)
│
├── artifacts/              # Generated outputs (not committed to git)
│   ├── models/             # Saved .keras / .h5 model files
│   ├── plots/              # Training history and evaluation plots
│   └── reports/            # PDF/HTML detection reports
│
├── docs/                   # All project documentation
│
├── AGENTS.md               # ← YOU ARE HERE
├── AI_DEVELOPMENT_GUIDELINES.md
├── PROMPT_TEMPLATES.md
└── .github/copilot-instructions.md
```

---

## 4. Coding Rules

These rules are **strict**. Apply them without exception.

### 4.1 Read Before Writing
- **Always inspect existing code** in the target module before writing new code.
- **Never overwrite a working module** without first reading its full content.
- Run `grep -r "function_name" src/` before creating a new function — duplicates are forbidden.

### 4.2 Architecture Compliance
- Follow the documented architecture in `docs/architecture/` exactly.
- **Route handlers** (`web/routes/`) contain only: input parsing, service calls, response formatting.
- **Business logic** lives exclusively in `src/services/`.
- **ML code** (model loading, inference) lives exclusively in `src/models/`.
- **Preprocessing** (image operations, ELA) lives exclusively in `src/preprocessing/`.

### 4.3 Docstrings
Every public function and class **must** have a Google-style docstring:

```python
def generate_ela(image_path: str, quality: int = 90) -> Image.Image:
    """Generate an Error Level Analysis visualization for an image.

    Args:
        image_path: Absolute path to the source JPEG or PNG image.
        quality: JPEG recompression quality (1–95). Defaults to 90.

    Returns:
        A PIL Image object containing the ELA visualization.

    Raises:
        FileNotFoundError: If image_path does not exist.
        ValueError: If quality is outside the valid range 1–95.
        IOError: If the image cannot be opened or decoded.
    """
```

### 4.4 Type Hints
- **All** function parameters and return values must have type annotations.
- Use `from __future__ import annotations` at the top of each file for forward compatibility.
- Use `Optional[T]` (or `T | None`) for nullable parameters.

### 4.5 PEP 8 and Style
- Maximum line length: **100 characters**.
- Use **4 spaces** for indentation (never tabs).
- Imports order: standard library → third-party → local (`src/`).
- One blank line between methods; two blank lines between top-level definitions.

### 4.6 Constants — No Magic Values
- **All constants** (paths, limits, hyperparameters, thresholds) live in `config.py`.
- Reference them as `from config import Config` or `Config.MAX_FILE_SIZE`.
- **Never hardcode** `224`, `0.5`, `16 * 1024 * 1024`, file paths, or model names inline.

### 4.7 Exception Handling
- **Never use a bare `except:`** — always catch a specific exception class.
- Always include a meaningful error message in the exception or log entry.
- Re-raise or return structured error responses; never silently swallow exceptions.

```python
# ❌ WRONG
try:
    result = predict(image)
except:
    pass

# ✅ CORRECT
try:
    result = predict(image)
except FileNotFoundError as e:
    logger.error("Model file missing: %s", e)
    raise
except RuntimeError as e:
    logger.error("Prediction failed: %s", e)
    raise PredictionError(f"Inference error: {e}") from e
```

### 4.8 Logging
- Import and use the project logger: `from src.utils.logger import get_logger`
- Call `logger = get_logger(__name__)` at module level.
- Use `logger.info`, `logger.warning`, `logger.error`, `logger.debug` — **never** `print()` in production code.
- Never log sensitive data (file contents, user-identifiable information).

### 4.9 File Paths
- **Never hardcode** absolute or relative file paths.
- Always use `Config.UPLOAD_FOLDER`, `Config.MODEL_DIR`, `Config.DATA_DIR`, etc. from `config.py`.
- Build paths with `pathlib.Path` or `os.path.join()`.

### 4.10 Modular Structure
- Respect the module boundaries defined in `src/README.md`.
- Do not import from `web/` inside `src/`.
- Do not import from `src/models/` inside `web/routes/` — go through `src/services/`.

---

## 5. STRICT PROHIBITIONS

The following actions are **absolutely forbidden**:

| Prohibition | Reason |
|-------------|--------|
| ❌ Invent model performance metrics or benchmark results | Academic dishonesty; misleads evaluators |
| ❌ Fabricate dataset file lists, image counts, or contents | The dataset structure must be discovered, not assumed |
| ❌ Claim that ELA *proves* image manipulation | ELA is investigative evidence, not proof — this is a legal/ethical requirement |
| ❌ Add unnecessary third-party dependencies | Increases attack surface and maintenance burden |
| ❌ Implement optional features before core features work | Follow the Module Development Order in `AI_DEVELOPMENT_GUIDELINES.md` |
| ❌ Store user images permanently | Privacy and storage policy — only temporary session storage |
| ❌ Add authentication, payment, or cloud infrastructure | Out of scope for a 4–6 week student project |
| ❌ Create duplicate functions or classes | Search the codebase first with `grep` or IDE search |
| ❌ Use bare `except:` clauses | Masks errors and makes debugging impossible |
| ❌ Hardcode file paths or configuration values | All constants live in `config.py` |
| ❌ Load models inside Flask route handlers | Models are loaded once at app startup via `model_loader.py` |
| ❌ Write to `data/raw/` | Raw dataset is read-only source of truth |

---

## 6. Dataset Rules

### 6.1 Directory Layout
```
data/raw/
├── casia_v1/     # 1,721 images — download separately per DATASET_DOWNLOAD_GUIDE.md
└── casia_v2/     # 12,614 images — download separately
```

### 6.2 Label Convention
Labels are **derived from the filename prefix only**:

| Prefix | Label (int) | Label Name |
|--------|-------------|------------|
| `Au_`  | `0` | Authentic |
| `Tp_`  | `1` | Manipulated (Tampered) |

- Do **not** invent or assume labels from any other source.
- Do **not** rely on subfolder names for labels — use the filename prefix.
- If a file does not match either prefix, log a warning and skip it.

### 6.3 Access Policy
- `data/raw/` → **READ-ONLY**. No script writes here.
- `data/processed/` → preprocessed images written by `scripts/prepare_dataset.py`.
- `data/metadata/` → CSV files written by `scripts/prepare_dataset.py`.
- Never commit files in `data/raw/` or `data/processed/` to git.

---

## 7. Model Rules

### 7.1 Saving
- Trained model files are saved to `artifacts/models/` using paths from `Config.MODEL_DIR`.
- Use the `.keras` format (TF 2.x native) unless a specific `.h5` format is required.
- Include a timestamp or version suffix: `cnn_model_v1.keras`, `mobilenet_model_v1.keras`.

### 7.2 Loading
- **Model loading** is handled **exclusively** by `src/models/model_loader.py`.
- The model loader is called **once** during Flask app startup (`app.py`), not on every request.
- Route handlers and services receive a pre-loaded model object — they do not load from disk.

### 7.3 Architecture
- **Never hardcode** model architecture inside routes, services, or scripts.
- Architecture definitions live in `src/models/cnn_model.py` and `src/models/mobilenet_model.py`.
- Both model builders accept `input_shape` as a parameter (default `(224, 224, 3)`).

---

## 8. ELA Rules

### 8.1 Implementation Location
- ELA code lives **only** in `src/preprocessing/ela_generator.py`.
- No other module re-implements ELA logic. Import `ELAGenerator` from there.

### 8.2 Input Handling
- **JPEG input**: apply JPEG recompression at the configured quality level, compute absolute pixel difference, apply enhancement.
- **PNG input**: PNG files must first be converted to JPEG for ELA to work. **Log a warning** that the ELA result for PNG-sourced images may be less reliable than for original JPEGs. Do not silently convert without logging.

### 8.3 Disclaimer
Every code path that returns an ELA result — in the service layer AND in the template — must accompany the result with the following disclaimer text:

> *"ELA visualization is an investigative aid. Bright regions in the ELA image indicate potential compression inconsistencies and do not constitute definitive proof of digital manipulation."*

This disclaimer text is defined as a constant in `config.py` as `Config.ELA_DISCLAIMER`.

---

## 9. Testing Rules

### 9.1 File Location
- All test files go in `tests/`.
- One test file per module: `tests/test_ela.py` → tests `src/preprocessing/ela_generator.py`.
- Shared fixtures go in `tests/conftest.py`.

### 9.2 Pre-commit Requirement
- Run `pytest tests/` before every commit.
- All tests must pass. Do not commit with failing tests.

### 9.3 Synthetic Images Only
- Tests **must not** depend on actual CASIA dataset images.
- Use `PIL.Image.new()` or `PIL.Image.fromarray()` with synthetic data in `conftest.py`.
- Tests must pass in a fresh clone without the CASIA dataset present.

### 9.4 Test Quality
- Each public function must have at least one happy-path test and one failure-path test.
- Use `pytest.monkeypatch` or `unittest.mock` to mock model inference so tests do not require trained model files.
- Assert on specific return types and value ranges, not just "no exception raised".

---

## 10. Git Rules

### 10.1 Branch Naming
```
feature/<short-description>   # New features
fix/<short-description>        # Bug fixes
docs/<short-description>       # Documentation updates
refactor/<short-description>   # Code refactoring
test/<short-description>       # Test additions
```

### 10.2 Commit Message Format
Follow Conventional Commits:
```
type(scope): short description

[optional body]
[optional footer]
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`  
**Scopes**: `ela`, `models`, `preprocessing`, `routes`, `training`, `dataset`, `config`, `tests`, `docs`

**Examples**:
```
feat(ela): implement ELAGenerator class with JPEG recompression
fix(preprocessing): handle grayscale images in image_normalizer
docs(agents): add prohibition against bare except clauses
test(ela): add synthetic image fixture for ELA unit tests
```

### 10.3 Branch Protection
- **Never commit directly to `main`**.
- All changes to `main` go through a pull request reviewed by at least one teammate.
- Delete feature branches after merging.
