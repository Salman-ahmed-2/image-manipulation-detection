# [ISSUE #4] Image Ingestion, Resizing, and Normalization Pipeline

## 📌 Issue Metadata
- **Milestone:** M1 — Data Pipeline & Forensics
- **Phase:** Phase 2 (Forensics & Preprocessing)
- **Estimated Effort:** 3–4 hours
- **Labels:** `preprocessing`, `vision`, `numpy`, `tensorflow`
- **Dependencies:** Issue #1 (`config.py`), Issue #2 (`src/utils/`)
- **Blocks:** Issue #7 (Custom CNN), Issue #8 (MobileNetV2), Issue #11 (Detection Service)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a Computer Vision & Deep Learning Engineer.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/architecture/COMPONENT_ARCHITECTURE.md`
> 2. `docs/architecture/DATA_FLOW.md`
> 3. `docs/machine_learning/ML_OVERVIEW.md`
> 4. `AGENTS.md` (Strict rules: Input shape must be `(224, 224, 3)`, no hardcoded shapes, Google-style docstrings).

---

## 🎯 Objective & Context
Build the deterministic image preprocessing pipeline under `src/preprocessing/` responsible for loading images from disk or memory, safely converting colorspaces to RGB, resizing to standardized model dimensions `(224, 224)` via bicubic interpolation, and scaling tensor values for either standard `[0.0, 1.0]` (Custom CNN) or `[-1.0, 1.0]` (MobileNetV2). Author unit tests in `tests/test_preprocessing.py`.

---

## 📋 Technical Requirements

### 1. Image Loader (`src/preprocessing/image_loader.py`)
- `load_image(image_input: Union[str, Path, bytes, Image.Image]) -> Image.Image`:
  - Ingest from path, raw byte stream, or existing PIL Image.
  - Automatically convert grayscale (`L`) or CMYK to standard 3-channel `RGB`.
  - Handle RGBA transparency by compositing over a solid white canvas (`Image.alpha_composite`).
  - Catch `PIL.UnidentifiedImageError` and raise `CorruptImageError`.

### 2. Image Resizer (`src/preprocessing/image_resizer.py`)
- `resize_image(image: Image.Image, target_size: Tuple[int, int] = (224, 224), keep_aspect_ratio: bool = False) -> Image.Image`:
  - Default: Resize directly to `target_size` using `Image.Resampling.BICUBIC`.
  - If `keep_aspect_ratio=True`: Pad with black or white borders to preserve original aspect ratio while filling target dimensions.
  - Reject non-positive dimensions with `ValueError`.

### 3. Image Normalizer (`src/preprocessing/image_normalizer.py`)
- `normalize_image(image_array: np.ndarray, mode: str = "standard") -> np.ndarray`:
  - Cast input array to `float32`.
  - If `mode == "standard"`: Scale pixel values to `[0.0, 1.0]` by dividing by `255.0`.
  - If `mode == "tf"` or `mode == "mobilenet"`: Scale to `[-1.0, 1.0]` via $(x / 127.5) - 1.0$ (matching `tf.keras.applications.mobilenet_v2.preprocess_input`).
  - Validate output values are strictly within target bounds.
- `prepare_tensor(image: Image.Image, target_size: Tuple[int, int] = (224, 224), mode: str = "standard") -> np.ndarray`:
  - Chains `resize_image` $\rightarrow$ `normalize_image` $\rightarrow$ `np.expand_dims(..., axis=0)` to yield shape `(1, 224, 224, 3)`.

### 4. Unit Tests (`tests/test_preprocessing.py`)
- Test grayscale image converts to 3-channel RGB.
- Test RGBA image with transparency composites cleanly on white background.
- Test output shape is strictly `(1, 224, 224, 3)`.
- Test `mode="standard"` outputs values in `[0.0, 1.0]`.
- Test `mode="mobilenet"` outputs values in `[-1.0, 1.0]`.
- Test invalid paths or corrupted byte arrays raise `CorruptImageError`.

---

## 📂 Target Files
- `src/preprocessing/image_loader.py`
- `src/preprocessing/image_resizer.py`
- `src/preprocessing/image_normalizer.py`
- `tests/test_preprocessing.py`

---

## 🧪 Verification & Testing
```bash
pytest tests/test_preprocessing.py -v
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] Pipeline produces batch-ready float32 tensors with shape `(1, 224, 224, 3)`.
- [ ] Both `standard` and `mobilenet` normalization modes are supported and numerically verified.
- [ ] Alpha transparency is handled without losing channel alignment.
- [ ] `pytest tests/test_preprocessing.py` passes 100%.
