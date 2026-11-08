# [ISSUE #2] Core System Utilities (Logger, Exceptions, File Validator & Image Utils)

## 📌 Issue Metadata
- **Milestone:** M0 — Architecture & Foundation
- **Phase:** Phase 1 (Foundation)
- **Estimated Effort:** 3–4 hours
- **Labels:** `utils`, `security`, `logging`, `validation`
- **Dependencies:** Issue #1 (`config.py`)
- **Blocks:** Issue #3, Issue #4, Issue #5, Issue #11, Issue #12

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a Senior Backend & Security Engineer.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/SECURITY_GUIDELINES.md`
> 2. `docs/architecture/COMPONENT_ARCHITECTURE.md`
> 3. `docs/testing/UNIT_TESTING.md`
> 4. `AGENTS.md` (Strict rules: No bare `except:`, use custom logger, never log private image bytes, Google-style docstrings).

---

## 🎯 Objective & Context
Implement the core utility layer under `src/utils/` to provide structured logging, custom domain exceptions, defensive file validation with magic-byte header inspection, and image array helpers. Create corresponding unit tests under `tests/test_file_validation.py`.

---

## 📋 Technical Requirements

### 1. Centralized Logger (`src/utils/logger.py`)
- Implement `get_logger(name: str) -> logging.Logger`.
- Format: `%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s`.
- Stream logs to `sys.stdout` with level controlled by `Config.LOG_LEVEL` (default `INFO`).
- Optional file handler outputting to `artifacts/app.log`.

### 2. Domain Exceptions Hierarchy (`src/utils/exceptions.py`)
Define structured custom exceptions inheriting from a base `AppError`:
- `AppError(Exception)`: Base application error.
- `ValidationError(AppError)`: Invalid file extension, missing payload, or spoofed header.
- `PayloadTooLargeError(ValidationError)`: Exceeds 16MB threshold.
- `CorruptImageError(ValidationError)`: Truncated or unidentifiable image stream.
- `ModelInferenceError(AppError)`: Prediction runtime failure.
- `ModelNotLoadedError(ModelInferenceError)`: Requested model not in memory.
- `ReportGenerationError(AppError)`: PDF compilation failure.

### 3. File Validation & Security (`src/utils/file_validator.py`)
- `validate_upload(file_storage: Any) -> Tuple[bool, str]`:
  - Check filename presence and non-empty.
  - Whitelist extension check (`.jpg`, `.jpeg`, `.png`).
  - Read first 32 bytes and verify binary magic bytes:
    - JPEG: `FF D8 FF`
    - PNG: `89 50 4E 47 0D 0A 1A 0A`
    - Rewind stream (`seek(0)`) after inspection.
  - Check content length against `Config.MAX_CONTENT_LENGTH`.
  - Check image dimensions using Pillow with decompression bomb check.
- `save_upload_securely(file_storage: Any, session_id: str) -> Path`:
  - Sanitize filename using `werkzeug.utils.secure_filename`.
  - Prefix with UUID4 hex to avoid collision and path traversal.
  - Save inside `Config.UPLOAD_FOLDER / session_id / <uuid>_<safe_name>`.

### 4. Image Utility Functions (`src/utils/image_utils.py`)
- `ensure_rgb(image: Image.Image) -> Image.Image`: Converts L, RGBA, CMYK safely to 3-channel RGB.
- `bytes_to_pil(image_bytes: bytes) -> Image.Image`: Reads bytes into PIL Image.
- `pil_to_bytes(image: Image.Image, format: str = "PNG") -> bytes`: Exports image into byte buffer.

### 5. Unit Tests (`tests/test_file_validation.py`)
- Create synthetic PIL image fixtures in memory (never depend on CASIA disk files).
- Test valid JPG, valid PNG.
- Test rejection of `.pdf`, `.exe`, empty files, oversized files, and spoofed extensions.

---

## 📂 Target Files
- `src/utils/logger.py`
- `src/utils/exceptions.py`
- `src/utils/file_validator.py`
- `src/utils/image_utils.py`
- `tests/test_file_validation.py`

---

## 🧪 Verification & Testing
```bash
# Run pytest on the new validation tests
pytest tests/test_file_validation.py -v
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] Magic-byte header verification correctly detects genuine vs. spoofed JPEG and PNG files.
- [ ] Filenames are sanitized and saved under unique session paths.
- [ ] All custom exceptions inherit from `AppError` and carry clear diagnostic messages.
- [ ] `pytest tests/test_file_validation.py` passes 100% with no warnings or errors.
