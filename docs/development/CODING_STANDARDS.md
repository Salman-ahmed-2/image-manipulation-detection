# Coding Standards & Quality Governance

## 1. Style & Syntax Rules
- **Python Version:** Strictly Python 3.11+.
- **PEP 8 Compliance:** All code formatted to PEP 8 standards. Maximum line length is **100 characters**.
- **Indentation:** 4 spaces (never tabs).
- **Imports Sorting:** Standard library $\rightarrow$ Third-party $\rightarrow$ Local `src/` modules.
- **Type Annotations:** All functions and methods must have complete parameter and return type hints:
  ```python
  from __future__ import annotations
  from typing import Optional, Tuple
  from pathlib import Path
  from PIL import Image
  ```

---

## 2. Docstring Specification (Google Style)
Every public module, class, method, and function must include Google-style docstrings:

```python
def preprocess_image(
    image_path: Union[str, Path],
    target_size: Tuple[int, int] = (224, 224),
    normalize_mode: str = "tf"
) -> np.ndarray:
    """Ingest a photographic file, convert to RGB, and resize to target dimensions.

    Args:
        image_path: Absolute or relative filesystem path to the image file.
        target_size: Desired (width, height) pixel tuple. Defaults to (224, 224).
        normalize_mode: Normalization scale ('tf' for [-1,1] or 'standard' for [0,1]).

    Returns:
        A 4D float32 NumPy tensor with shape (1, height, width, 3).

    Raises:
        FileNotFoundError: If image_path does not exist on disk.
        ValueError: If target_size contains non-positive dimensions or mode is invalid.
        IOError: If Pillow cannot decode the image binary stream.
    """
```

---

## 3. Defensive Programming Rules
1. **Never use bare `except:` clauses:** Always catch specific exceptions (`FileNotFoundError`, `ValueError`, `PIL.UnidentifiedImageError`).
2. **No Magic Numbers:** All hyperparameters, image dimensions, quality factors, and byte thresholds must be defined in `config.py`.
3. **Structured Logging:** Use `src/utils/logger.py` exclusively (`logger.info`, `logger.warning`, `logger.error`). `print()` statements are forbidden in production code.
