# [ISSUE #1] Project Dependencies, Environment Setup & Centralized Configuration

## 📌 Issue Metadata
- **Milestone:** M0 — Architecture & Foundation
- **Phase:** Phase 1 (Foundation)
- **Estimated Effort:** 2–3 hours
- **Labels:** `setup`, `config`, `dependencies`, `foundation`
- **Dependencies:** None (Initial Task)
- **Blocks:** Issue #2, Issue #3, Issue #4, Issue #5

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a Senior Software Architect and Backend Engineer on the **Image Manipulation Detection System Using Deep Learning**.
> Before generating or editing code, you **MUST read the following authoritative documentation**:
> 1. `docs/PROJECT_OVERVIEW.md`
> 2. `docs/development/INSTALLATION_GUIDE.md`
> 3. `docs/development/ENVIRONMENT_SETUP.md`
> 4. `docs/decisions/ADR-001-TECHNOLOGY-STACK.md`
> 5. `AGENTS.md` (Strict rules: No hardcoded constants, follow PEP 8, add docstrings, use Python 3.11).

---

## 🎯 Objective & Context
Establish the runtime dependencies, environment variables template, and authoritative configuration class (`Config`) that centralizes all file paths, operational limits, hyperparameters, and forensic constants. No other module should ever hardcode constants or magic values.

---

## 📋 Technical Requirements

### 1. Define Dependencies in `requirements.txt`
Pin compatible versions for Python 3.11:
- `flask>=3.0.0`
- `werkzeug>=3.0.0`
- `tensorflow>=2.15.0`
- `pillow>=10.2.0`
- `opencv-python-headless>=4.9.0`
- `numpy>=1.24.3`
- `pandas>=2.1.0`
- `scikit-learn>=1.3.0`
- `matplotlib>=3.8.0`
- `seaborn>=0.13.0`
- `fpdf2>=2.7.7`
- `python-dotenv>=1.0.0`
- `pytest>=7.4.0`
- `pytest-cov>=4.1.0`
- `gunicorn>=21.2.0`

### 2. Create Environment Template `.env.example`
Provide clear defaults for:
- `FLASK_APP=app.py`
- `FLASK_ENV=development`
- `FLASK_DEBUG=1`
- `SECRET_KEY=replace-with-a-secure-random-32-char-key-in-production`
- `PORT=5000`
- `HOST=127.0.0.1`

### 3. Implement Centralized Configuration (`config.py`)
Create a robust `Config` class loading from environment variables with safe defaults:
- **Project Roots & Storage:**
  - `BASE_DIR = Path(__file__).resolve().parent`
  - `DATA_DIR = BASE_DIR / "data"`
  - `RAW_DATA_DIR = DATA_DIR / "raw"`
  - `PROCESSED_DATA_DIR = DATA_DIR / "processed"`
  - `METADATA_DIR = DATA_DIR / "metadata"`
  - `SPLITS_DIR = DATA_DIR / "splits"`
  - `ARTIFACTS_DIR = BASE_DIR / "artifacts"`
  - `MODEL_DIR = ARTIFACTS_DIR / "models"`
  - `PLOTS_DIR = ARTIFACTS_DIR / "plots"`
  - `REPORTS_DIR = ARTIFACTS_DIR / "reports"`
  - `TEMP_DIR = BASE_DIR / "temp"`
  - `UPLOAD_FOLDER = TEMP_DIR / "uploads"`
- **Upload Constraints:**
  - `MAX_CONTENT_LENGTH = 16 * 1024 * 1024` (16 MB)
  - `ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}`
  - `MAX_IMAGE_PIXELS = 50_000_000` (Decompression bomb protection)
  - `TEMP_FILE_EXPIRY = 1800` (30 minutes)
- **Model Parameters:**
  - `INPUT_SHAPE = (224, 224, 3)`
  - `BATCH_SIZE = 32`
  - `DEFAULT_EPOCHS = 50`
  - `ACTIVE_MODEL = "mobilenet"` (or `"cnn"`)
- **Forensic ELA Settings:**
  - `ELA_QUALITY = 90`
  - `ELA_ENHANCEMENT_FACTOR = 10.0`
  - `ELA_DISCLAIMER = "ELA visualization is an investigative aid. Bright regions indicate potential compression inconsistencies and do not constitute definitive proof of digital manipulation."`
- **Method `init_app(app)`:** Automatically creates necessary directories (`temp/uploads`, `artifacts/models`, etc.) if missing.

---

## 📂 Target Files
- `requirements.txt`
- `.env.example`
- `config.py`

---

## 🧪 Verification & Testing
```bash
# Verify config can be imported without errors
python3 -c "from config import Config; print('Config loaded successfully. Upload folder:', Config.UPLOAD_FOLDER)"

# Verify directory creation
python3 -c "from config import Config; Config.init_app(); print('Artifact directories initialized.')"
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] `requirements.txt` contains clean, pinned, modern dependencies without conflicts.
- [ ] `.env.example` documents all required environment variables.
- [ ] `config.py` uses `pathlib.Path` for all paths and exports all required parameters.
- [ ] `Config.ELA_DISCLAIMER` is defined exactly as specified in `AGENTS.md`.
- [ ] No hardcoded paths or values remain in module code.
