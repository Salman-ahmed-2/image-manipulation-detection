# [ISSUE #10] Thread-Safe In-Memory Model Loader & Predictor Engine

## 📌 Issue Metadata
- **Milestone:** M3 — Transfer Learning & Comparison
- **Phase:** Phase 5 (Model Serving & Backend)
- **Estimated Effort:** 3–4 hours
- **Labels:** `serving`, `inference`, `model-loader`, `concurrency`
- **Dependencies:** Issue #1 (`config.py`), Issue #2 (`logger.py`), Issue #7 or Issue #8
- **Blocks:** Issue #11 (Detection Service)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as an ML Infrastructure & Systems Engineer.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/machine_learning/MODEL_DEPLOYMENT.md`
> 2. `docs/architecture/COMPONENT_ARCHITECTURE.md`
> 3. `AGENTS.md` (Strict rules: Models loaded ONCE at app startup, never inside route handlers, mock fallback required if model files are absent).

---

## 🎯 Objective & Context
Implement `src/models/model_loader.py` and `src/models/predictor.py`. In-memory model caching is critical for performance; reloading models on each request causes unacceptable multi-second delays. The model loader must safely cache models at startup, execute a warmup pass, support graceful fallback when weights are missing, and provide a clean `Predictor` interface that outputs categorical verdicts and calibrated confidence scores.

---

## 📋 Technical Requirements

### 1. In-Memory Registry (`src/models/model_loader.py`)
- Implement `class ModelLoader`:
  - `_registry: Dict[str, tf.keras.Model] = {}`
  - `@classmethod load_all_models() -> None`:
    - Checks `Config.MODEL_DIR` for `cnn_model.keras` and `mobilenet_model.keras`.
    - If present: Load model via `tf.keras.models.load_model()`.
    - Execute a dummy warmup forward pass using `tf.zeros((1, 224, 224, 3))`.
    - Store references in `_registry['cnn']` and `_registry['mobilenet']`.
    - If a model file is missing: Log a descriptive warning and register a lightweight mock/fallback predictor so tests and UI can run before heavy training completes.
  - `@classmethod get_model(name: str) -> Optional[tf.keras.Model]`:
    - Return model instance by key.

### 2. Predictor Engine (`src/models/predictor.py`)
- Implement `class Predictor`:
  ```python
  class Predictor:
      def __init__(self, model_name: str = "mobilenet"):
          ...
          
      def predict(self, preprocessed_tensor: np.ndarray) -> Dict[str, Any]:
          """Execute model prediction and compute calibrated confidence metrics.
          
          Args:
              preprocessed_tensor: 4D numpy array with shape (1, 224, 224, 3).
              
          Returns:
              dict with keys:
                  'raw_probability': float (0.0 to 1.0)
                  'verdict_code': int (0 for Authentic, 1 for Manipulated)
                  'verdict_label': str ("Authentic" or "Potentially Manipulated")
                  'confidence': float (percentage 50.0 to 100.0)
                  'model_used': str
          """
  ```
- **Confidence Computation Logic:**
  - Let raw Sigmoid output be $P \in [0.0, 1.0]$.
  - If $P \ge 0.5$:
    - `verdict_code = 1`, `verdict_label = "Potentially Manipulated"`
    - `confidence = round(float(P) * 100.0, 2)`
  - Else:
    - `verdict_code = 0`, `verdict_label = "Authentic"`
    - `confidence = round(float(1.0 - P) * 100.0, 2)`

### 3. Unit Tests (`tests/test_prediction.py`)
- Test prediction returns required dictionary keys and types.
- Test confidence percentage is always between `50.0%` and `100.0%`.
- Test model loader gracefully handles missing model files with descriptive warning.

---

## 📂 Target Files
- `src/models/model_loader.py`
- `src/models/predictor.py`
- `tests/test_prediction.py`

---

## 🧪 Verification & Testing
```bash
pytest tests/test_prediction.py -v
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] Models load into memory once at server initialization without per-request disk reads.
- [ ] Dummy warmup forward pass eliminates cold-start latency for the first user request.
- [ ] Predictor outputs consistent verdicts, probabilities, and confidence percentages.
- [ ] `pytest tests/test_prediction.py` passes 100%.
