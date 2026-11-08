# Automated Test Suite (`tests/`)

This directory contains the automated test suite executed via `pytest`.

## Test Organization

```
tests/
├── conftest.py                # Pytest fixtures, Flask test client, synthetic image generators
├── test_api.py                # REST API and route integration tests
├── test_dataset.py            # Dataset inventory and splitting logic tests
├── test_ela.py                # ELA recompression and contrast scaling tests
├── test_file_validation.py    # Magic bytes, extension, and payload boundary tests
├── test_models.py             # CNN and MobileNetV2 architecture tests
├── test_prediction.py         # Prediction probability scoring tests
└── test_preprocessing.py      # Resizing, colorspace, and normalization tests
```

## Running Tests

```bash
# Execute full test suite
pytest tests/ -v

# Run with code coverage report
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Run specific test module
pytest tests/test_ela.py -v
```

## Testing Ground Rules
- **Synthetic Data Only:** Tests must never depend on the physical presence of the CASIA datasets. All test images must be generated programmatically in-memory using `PIL.Image.new()`.
- **Pre-Commit Enforcement:** All tests must pass before pushing commits to Git.
