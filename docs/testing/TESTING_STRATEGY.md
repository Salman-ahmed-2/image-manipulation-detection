# Testing Strategy — Image Manipulation Detection System

> **Project:** Image Manipulation Detection Using Deep Learning  
> **Team Size:** 4 members  
> **Framework:** pytest + pytest-cov  
> **Last Updated:** 2026-11-08

---

## 1. Testing Philosophy

This project follows a **test early, test often** approach. Testing is not an afterthought applied at the end of the sprint — it is woven into every development phase:

- **Test Early:** Unit tests are written alongside (or just after) each module, not at the end of the project.
- **Test Often:** Every meaningful code change triggers a local test run before committing to the shared repository.
- **CI-Friendly:** All tests are designed to run without a GPU, without the real CASIA dataset, and without network access — enabling automated validation in any environment.
- **Honest About Limitations:** ML tests do not assert exact accuracy values; they assert structural properties (shape, type, range) and behavior (error handling, boundary conditions).

> [!IMPORTANT]
> Tests that require the real trained model (`.h5` or `.keras` files in `artifacts/models/`) are marked with `@pytest.mark.skipif` guards so the test suite still passes during early development when models are not yet trained.

---

## 2. Testing Pyramid

The project follows the classic testing pyramid structure, investing most effort at the unit level where tests are fast, cheap, and highly isolated.

```
              ┌──────────────────┐
              │  Acceptance /    │  ← Fewest, slowest, manual or semi-automated
              │  System Tests    │     (user story walkthroughs, browser tests)
              ├──────────────────┤
              │  Integration     │  ← Moderate number, test module interactions
              │  Tests           │     (upload → validate → predict → result)
              ├──────────────────┤
              │  Unit Tests      │  ← Most numerous, fastest, fully automated
              │  (most)          │     (individual functions, classes, edge cases)
              └──────────────────┘
```

### 2.1 Unit Tests (Primary Focus)

- **Scope:** Individual functions and classes in isolation.
- **Speed:** Each test should complete in milliseconds.
- **Dependencies:** External dependencies (model inference, file I/O, Flask) are mocked or replaced with fixtures.
- **Coverage Target:** >80% line coverage on all modules under `src/`.

### 2.2 Integration Tests

- **Scope:** Two or more modules working together through their real interfaces.
- **Speed:** A few seconds per test; acceptable to run on every commit.
- **Dependencies:** Flask test client used instead of a real browser. Models may be stubbed.
- **Key Scenario:** Full pipeline from file upload through validation, preprocessing, prediction, ELA generation, and result rendering.

### 2.3 System / Acceptance Tests

- **Scope:** End-to-end behavior from the user's perspective.
- **Speed:** Can take 10–30 seconds per scenario; run before major milestones.
- **Dependencies:** Requires a fully loaded model. Some tests are manual walkthroughs.
- **Coverage:** Mapped directly to user stories and acceptance criteria.

---

## 3. Test Coverage Goals

| Module | Coverage Target | Rationale |
|---|---|---|
| `src/utils/file_validator.py` | ≥ 90% | Security-critical; all branches must be tested |
| `src/preprocessing/preprocessor.py` | ≥ 85% | Core data pipeline; failures break entire system |
| `src/preprocessing/ela_generator.py` | ≥ 80% | Forensic feature; needs edge case coverage |
| `src/models/cnn_model.py` | ≥ 70% | Architecture definition; structural tests |
| `src/models/mobilenet_model.py` | ≥ 70% | Architecture definition; structural tests |
| `src/services/detection_service.py` | ≥ 80% | Critical service; prediction + error paths |
| `src/services/report_service.py` | ≥ 75% | PDF generation; happy path + error path |
| `app.py` / routes | ≥ 80% | All HTTP endpoints and status codes |
| **Overall `src/` target** | **≥ 80%** | Project-wide minimum |

> [!NOTE]
> Coverage percentage is a floor, not a ceiling. 100% coverage does not mean the tests are good — focus on testing meaningful behavior, not just executing lines.

---

## 4. Test Framework

### 4.1 Core Tools

| Tool | Version | Purpose |
|---|---|---|
| `pytest` | ≥ 7.0 | Test runner, fixture system, parametrize |
| `pytest-cov` | ≥ 4.0 | Coverage measurement and HTML reporting |
| `Pillow` | (project version) | Synthetic image creation in fixtures |
| `Flask` test client | (Flask built-in) | Simulates HTTP requests without a live server |
| `unittest.mock` | (stdlib) | Mocking model predictions and file I/O |

### 4.2 Installation

```bash
# From project root, with virtual environment active
pip install pytest pytest-cov

# Verify installation
pytest --version
```

### 4.3 Configuration (`pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (module interactions)
    acceptance: Acceptance tests (end-to-end)
    requires_model: Tests that need a trained model file
    slow: Tests that take longer than 5 seconds
```

---

## 5. Test File Organization

```
tests/
├── conftest.py                  # Shared fixtures (Flask app, synthetic images)
├── test_file_validation.py      # File upload validation tests
├── test_preprocessing.py        # Image preprocessing pipeline tests
├── test_ela.py                  # ELA generation tests
├── test_models.py               # Model architecture and load tests
├── test_prediction.py           # Inference and output tests
├── test_api.py                  # Flask endpoint integration tests
└── test_dataset.py              # Dataset utility and label mapping tests
```

### Role of Each File

| Test File | What It Tests | Layer |
|---|---|---|
| `test_file_validation.py` | Extension checking, size limits, MIME sniffing, filename sanitization | Unit |
| `test_preprocessing.py` | RGB conversion, resize to 224×224, normalization, batch dimension | Unit |
| `test_ela.py` | ELA image generation, output shape, temp file cleanup | Unit |
| `test_models.py` | Model instantiation, input/output shapes, weight loading | Unit + Integration |
| `test_prediction.py` | Prediction output format, label type, confidence range | Unit + Integration |
| `test_api.py` | HTTP status codes, JSON responses, file upload endpoint behavior | Integration |
| `test_dataset.py` | Label mapping from filenames, train/val/test split ratios | Unit |

---

## 6. Running Tests

### 6.1 Run All Tests (Verbose)

```bash
pytest tests/ -v
```

### 6.2 Run with Coverage Report (HTML)

```bash
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser to inspect coverage
```

### 6.3 Run with Coverage Report (Terminal Summary)

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### 6.4 Run a Specific Test File

```bash
pytest tests/test_file_validation.py -v
```

### 6.5 Run a Specific Test Function

```bash
pytest tests/test_file_validation.py::test_valid_jpg_accepted -v
```

### 6.6 Run Tests by Marker

```bash
# Only unit tests
pytest tests/ -m unit -v

# Only integration tests
pytest tests/ -m integration -v

# Skip tests requiring trained model
pytest tests/ -m "not requires_model" -v
```

### 6.7 Run with Fail-Fast (Stop on First Failure)

```bash
pytest tests/ -v -x
```

### 6.8 Generate Full Coverage Report

```bash
pytest tests/ \
  --cov=src \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=80
```

---

## 7. Test Data Strategy

> [!IMPORTANT]
> **Never use real CASIA dataset images in test fixtures.** Tests must be self-contained, reproducible, and runnable without downloading the dataset.

### 7.1 Synthetic Image Creation

All tests that need image input create small, synthetic images using `Pillow` within fixtures:

```python
# tests/conftest.py
import io
import pytest
from PIL import Image

@pytest.fixture
def synthetic_rgb_jpeg():
    """Returns a BytesIO buffer containing a valid small JPEG image."""
    img = Image.new("RGB", (100, 100), color=(128, 64, 32))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    return buf

@pytest.fixture
def synthetic_rgb_png():
    """Returns a BytesIO buffer containing a valid small PNG image."""
    img = Image.new("RGB", (100, 100), color=(64, 128, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

@pytest.fixture
def synthetic_rgba_png():
    """Returns a BytesIO buffer containing a valid RGBA PNG image."""
    img = Image.new("RGBA", (100, 100), color=(64, 128, 200, 180))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

@pytest.fixture
def synthetic_grayscale_jpeg():
    """Returns a BytesIO buffer containing a grayscale JPEG image."""
    img = Image.new("L", (100, 100), color=128)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf
```

### 7.2 Oversized File Simulation

```python
@pytest.fixture
def oversized_file():
    """Returns a BytesIO buffer that exceeds the 16MB upload limit."""
    # 17MB of zero bytes — not a real image, used to test size limit only
    buf = io.BytesIO(b'\x00' * (17 * 1024 * 1024))
    buf.name = "big_file.jpg"
    return buf
```

### 7.3 Spoofed File Simulation

```python
@pytest.fixture
def pdf_as_jpg():
    """Returns a BytesIO buffer with PDF magic bytes but .jpg extension."""
    # PDF magic bytes: %PDF-
    buf = io.BytesIO(b'%PDF-1.4 fake pdf content')
    buf.name = "sneaky.jpg"
    return buf
```

### 7.4 Why Not Real Dataset Images

| Reason | Explanation |
|---|---|
| **Dataset availability** | CASIA dataset may not be present on every developer's machine |
| **Reproducibility** | Synthetic images are always identical; real images vary by download |
| **Speed** | Small 100×100 test images process in milliseconds |
| **Legal** | Distributing dataset images through the test suite may violate dataset license |
| **CI compatibility** | CI environments cannot download large datasets |

---

## 8. CI Considerations

Although this is a university project without a mandatory CI pipeline, the test suite is designed to be CI-compatible:

### 8.1 GitHub Actions Example (`ci.yml`)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests (excluding model-dependent tests)
        run: |
          pytest tests/ -m "not requires_model" \
            --cov=src \
            --cov-report=term-missing \
            --cov-fail-under=80
```

### 8.2 CI Constraints

| Constraint | How Tests Handle It |
|---|---|
| No GPU | All tests use CPU; model tests are skipped (`@pytest.mark.skipif`) |
| No dataset | Synthetic images used; no CASIA access required |
| No trained model | Model-dependent tests guarded with `requires_model` marker |
| Memory limits | Test images are small (100×100); no large tensors allocated |
| No network | Tests do not make external HTTP calls |

### 8.3 Pre-Commit Check

Teams should run the following before every commit:

```bash
# Minimal fast check (unit tests only, no coverage overhead)
pytest tests/ -m "unit" -v -x

# Full check before pushing
pytest tests/ -m "not requires_model" --cov=src --cov-report=term-missing
```

---

## 9. Test Maintenance Guidelines

1. **Keep tests deterministic** — no random seeds without being fixed, no time-dependent assertions.
2. **One assertion per concern** — a test should fail for one clear reason.
3. **Name tests descriptively** — `test_oversized_file_rejected` is better than `test_case_7`.
4. **Clean up temp files** — any test that creates files on disk must clean them up (`tmp_path` fixture handles this automatically).
5. **Do not test implementation details** — test behavior and contracts, not internal variable names.
6. **Update tests when requirements change** — a failing test suite is better than an outdated one.
