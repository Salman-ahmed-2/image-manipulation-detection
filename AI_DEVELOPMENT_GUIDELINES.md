# AI-Assisted Development Guidelines

**Project**: Image Manipulation Detection System  
**Team Size**: 4 students  
**Timeline**: 4–6 weeks  
**AI Tools Permitted**: GitHub Copilot, Gemini, Claude, ChatGPT (any coding assistant)

---

## 1. Philosophy

> AI coding assistants are **pair programmers**, not autonomous developers.

Every AI-generated suggestion must be reviewed by a human team member before it is committed to the repository. The AI does not understand your project's full context, your team's decisions, or the academic integrity requirements of this assignment. **You are responsible for every line of code in this repository**, regardless of whether an AI wrote it.

### Core Principles

1. **AI suggestions are drafts, not solutions.** Treat them as a first draft that requires review, testing, and often refactoring.
2. **Architecture is non-negotiable.** If the AI deviates from the documented architecture in `docs/architecture/`, correct it — do not accept the deviation.
3. **Verify all API calls.** AI assistants frequently hallucinate function signatures, class names, and module paths. Always cross-check against official documentation or the existing codebase.
4. **Never accept fabricated numbers.** If an AI generates a comment like `"achieves 94.7% accuracy"`, delete it immediately. Performance metrics come only from actual training runs.
5. **Test everything.** An untested AI-generated function is a liability. Write or verify unit tests before marking a task complete.

---

## 2. How to Use AI Effectively for This Project

### 2.1 Use PROMPT_TEMPLATES.md
The file `PROMPT_TEMPLATES.md` contains pre-written, context-rich prompt templates for every major development task (ELA, CNN, MobileNetV2, Flask routes, testing, etc.). **Use these templates** rather than improvised prompts — they include the required documentation context and constraints that prevent common AI mistakes.

### 2.2 Provide Context Before Asking
Before asking an AI to write or modify code, paste in:
- The relevant section from `docs/` (architecture doc, ML overview, etc.)
- The existing code of the module being modified
- The specific function signature and docstring you expect

```
# Example: Good prompt structure
"I am working on the Image Manipulation Detection project.
Here is the architecture documentation: [paste relevant section]
Here is the existing code: [paste file contents]
Task: Implement the generate() method of ELAGenerator following these requirements: [paste requirements]"
```

### 2.3 Correct Architectural Deviations Immediately
If the AI places ML code inside a route handler, generates a database model, adds `flask-login` imports, or loads models on every request — **stop, correct the prompt, and regenerate**. Do not patch around architectural violations.

### 2.4 Verify Module Names and Signatures
After receiving AI-generated code, verify every import and function call:
```bash
# Check that an imported module actually exists
find src/ -name "*.py" | xargs grep -l "class ELAGenerator"

# Check that a referenced function has the correct signature
grep -n "def validate" src/utils/file_validator.py
```

### 2.5 Cross-Reference Config Constants
AI assistants frequently hardcode values. After receiving any generated code, search for:
- Magic numbers (`224`, `0.5`, `16777216`, `90`, `0.4`)
- Hardcoded paths (`"artifacts/models/"`, `"temp/"`, `"data/raw/"`)
- Hardcoded strings (`"Au_"`, `"Tp_"`, `".jpg"`)

Replace every occurrence with the corresponding `Config.*` constant.

---

## 3. Module Development Order

Build modules in this order. **Do not skip ahead.** Later modules depend on earlier ones, and jumping ahead leads to integration failures that are hard to debug.

```
Phase 1: Foundation
─────────────────────────────────────────
  1  src/utils/exceptions.py          Custom exception classes
  2  src/utils/logger.py              Logger factory
  3  src/utils/file_validator.py      Upload validation
  4  src/utils/image_utils.py         Image format utilities
  5  config.py                        All constants (review existing)

Phase 2: Preprocessing Pipeline
─────────────────────────────────────────
  6  src/preprocessing/image_loader.py
  7  src/preprocessing/image_resizer.py
  8  src/preprocessing/image_normalizer.py
  9  src/preprocessing/ela_generator.py   ← Critical; test thoroughly

Phase 3: Dataset Preparation
─────────────────────────────────────────
  10  src/data/dataset_loader.py
  11  src/data/dataset_validator.py
  12  src/data/dataset_splitter.py
  13  src/data/augmentation.py
  14  scripts/prepare_dataset.py

Phase 4: Model Architecture
─────────────────────────────────────────
  15  src/models/cnn_model.py
  16  src/models/mobilenet_model.py

Phase 5: Training Infrastructure
─────────────────────────────────────────
  17  src/training/trainer.py
  18  src/training/callbacks.py
  19  scripts/train.py
  20  scripts/evaluate.py

Phase 6: Inference Pipeline
─────────────────────────────────────────
  21  src/models/model_loader.py
  22  src/models/predictor.py

Phase 7: Business Logic Services
─────────────────────────────────────────
  23  src/services/ela_service.py
  24  src/services/detection_service.py
  25  src/services/report_service.py

Phase 8: Web Application
─────────────────────────────────────────
  26  web/routes/main_routes.py
  27  web/routes/detection_routes.py
  28  web/templates/base.html
  29  web/templates/index.html
  30  web/templates/result.html
  31  web/templates/about.html
  32  web/templates/error.html
  33  web/static/css/style.css
  34  web/static/js/main.js
  35  app.py (wire everything together)

Phase 9: Testing and Evaluation
─────────────────────────────────────────
  36  tests/conftest.py
  37  tests/test_file_validation.py
  38  tests/test_preprocessing.py
  39  tests/test_ela.py
  40  tests/test_models.py
  41  tests/test_prediction.py
  42  tests/test_api.py
  43  tests/test_dataset.py

Phase 10: Optional Enhancements (time permitting)
─────────────────────────────────────────
  44  src/explainability/gradcam.py
  45  src/evaluation/confusion_matrix.py
  46  src/evaluation/visualization.py
```

---

## 4. Verification Checklist After Each AI-Generated Module

Run through this checklist **before committing** any AI-generated code:

### Architecture Check
- [ ] Does the module's location (`src/`, `web/`, `scripts/`) match what `docs/architecture/COMPONENT_ARCHITECTURE.md` specifies?
- [ ] Does the module's import graph respect the dependency order in `src/README.md`?
- [ ] Are there any imports from the wrong layer (e.g., web imports in src/)?

### Code Quality Check
- [ ] Do all public functions have Google-style docstrings?
- [ ] Do all function parameters and return values have type hints?
- [ ] Is the line length ≤ 100 characters throughout?
- [ ] Are there any bare `except:` clauses?
- [ ] Are there any hardcoded file paths?
- [ ] Are there any hardcoded numeric constants (magic numbers)?
- [ ] Does the module use `Config.*` for all constants?
- [ ] Does the module use `get_logger(__name__)` for all logging?
- [ ] Is there any `print()` statement in production code?

### ML-Specific Check (for src/models/, src/training/)
- [ ] Does the model use TensorFlow 2.x APIs only (no `tf.compat.v1`)?
- [ ] Is the input shape `(224, 224, 3)` sourced from `Config.IMAGE_SIZE`?
- [ ] Are batch size and epochs kept out of the model definition?
- [ ] Is model loading isolated to `model_loader.py`?

### Flask-Specific Check (for web/routes/)
- [ ] Is `secure_filename()` applied to every uploaded filename?
- [ ] Is all validation delegated to `FileValidator` (not inlined)?
- [ ] Is all ML/ELA logic delegated to services (not inlined)?
- [ ] Does the route return structured JSON `{status, message, code}` on errors?

### Testing Check
- [ ] Is there a corresponding test file in `tests/`?
- [ ] Do tests use synthetic images, not actual CASIA dataset files?
- [ ] Does `pytest tests/` pass with zero failures?
- [ ] Is there at least one happy-path and one failure-path test per public function?

---

## 5. Common AI Mistakes to Watch For

### 5.1 Deprecated TensorFlow APIs
```python
# ❌ AI-generated (TF 1.x compat — do not use)
with tf.compat.v1.Session() as sess:
    output = sess.run(model.output)

tf.placeholder(tf.float32, shape=[None, 224, 224, 3])

# ✅ Correct (TF 2.x eager execution)
output = model(input_tensor, training=False)
```

### 5.2 Wrong Input Shape
```python
# ❌ AI might generate (wrong — missing batch dimension or wrong size)
input_tensor = np.array(image)  # shape (224, 224, 3) — missing batch dim
model.predict(input_tensor)

# ✅ Correct
input_array = np.expand_dims(image_array, axis=0)  # shape (1, 224, 224, 3)
prediction = model.predict(input_array)
```

### 5.3 Model Loaded Inside Request Handler
```python
# ❌ AI-generated (loads model on every request — catastrophically slow)
@detection_bp.route("/analyze", methods=["POST"])
def analyze():
    model = tf.keras.models.load_model("artifacts/models/cnn_model_v1.keras")
    prediction = model.predict(...)

# ✅ Correct (model loaded once at startup, injected as app state)
@detection_bp.route("/analyze", methods=["POST"])
def analyze():
    service = DetectionService(model=current_app.model)
    result = service.analyze(image_path, model_name)
```

### 5.4 Missing secure_filename()
```python
# ❌ AI might skip this — path traversal vulnerability
filename = request.files["image"].filename
save_path = os.path.join(Config.UPLOAD_FOLDER, filename)

# ✅ Always sanitize
from werkzeug.utils import secure_filename
filename = secure_filename(request.files["image"].filename)
save_path = Config.UPLOAD_FOLDER / session_id / filename
```

### 5.5 Hardcoded Model Path
```python
# ❌ Hardcoded — breaks on any other machine
model = tf.keras.models.load_model("/home/salman/project/artifacts/models/model.h5")

# ✅ Use Config
model_path = Config.MODEL_DIR / Config.DEFAULT_MODEL_FILENAME
model = tf.keras.models.load_model(model_path)
```

### 5.6 Fabricated Performance Metrics
```python
# ❌ AI hallucination — DELETE immediately
# This model achieves 94.7% accuracy on the CASIA v2 test set.

# ✅ No performance claims in code — only in reports from actual training runs
```

### 5.7 Wrong MobileNetV2 Preprocessing
```python
# ❌ Generic normalization — wrong for MobileNetV2
image_array = image_array / 255.0

# ✅ MobileNetV2-specific preprocessing (scales to [-1, 1])
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
image_array = preprocess_input(image_array)
```

### 5.8 ELA Applied Identically to PNG
```python
# ❌ AI might apply JPEG ELA to PNG without warning
def generate(self, image_path: str) -> Image.Image:
    img = Image.open(image_path)
    img.save(temp_path, "JPEG", quality=self.quality)  # silently converts PNG

# ✅ Detect format and warn
def generate(self, image_path: str) -> Image.Image:
    img = Image.open(image_path)
    if img.format == "PNG":
        logger.warning(
            "PNG input detected (%s). ELA requires JPEG compression history. "
            "Converting to JPEG — results may be less reliable than for original JPEGs.",
            image_path
        )
    img.save(temp_path, "JPEG", quality=self.quality)
```

---

## 6. Reviewing AI Code — Category Checklists

### 6.1 ML Code Review (src/models/, src/training/)

| Item | Check |
|------|-------|
| TF version compatibility | No `tf.compat.v1` usage |
| Input preprocessing | Correct normalization for each model type |
| Output layer | Single neuron with sigmoid for binary classification |
| Loss function | `binary_crossentropy` |
| Metrics | At minimum `accuracy`; ideally also `AUC` |
| Dropout rates | Match `Config.DROPOUT_RATE_1`, `Config.DROPOUT_RATE_2` |
| Batch normalization | Present after each Conv block in CNN |
| Fine-tuning | MobileNetV2 phase 2 only unfreezes last N layers |
| Model saving | Uses `.keras` format, saved to `Config.MODEL_DIR` |
| No hardcoded shapes | `input_shape` passed as parameter from `Config.IMAGE_SIZE` |

### 6.2 Flask Code Review (web/routes/)

| Item | Check |
|------|-------|
| `secure_filename()` | Applied to every uploaded filename |
| File size check | Handled by `Config.MAX_CONTENT_LENGTH` + `FileValidator` |
| MIME type check | Delegated to `FileValidator` |
| Session UUID | Generated for every upload; used in temp path |
| Temp cleanup | Scheduled or handled on session end |
| Exception handling | `FileNotFoundError`, `ValueError`, `RuntimeError` caught |
| Error response | JSON `{status, message, code}` with appropriate HTTP code |
| No business logic | All logic in services, not in route function body |
| Template variables | All variables documented in `web/README.md` |
| ELA disclaimer | Present in template via `Config.ELA_DISCLAIMER` |

### 6.3 Testing Code Review (tests/)

| Item | Check |
|------|-------|
| Synthetic images | No dependency on CASIA dataset files |
| Fixtures in conftest | `app`, `client`, `synthetic_jpeg`, `synthetic_png` |
| Mock for ML | `monkeypatch` or `unittest.mock` used when models unavailable |
| Coverage | Happy path + at least one failure path per function |
| Isolation | Each test is independent; no shared state between tests |
| Passes without models | Full test suite passes in a fresh clone |
| Naming | `test_<function_name>_<scenario>` pattern |
