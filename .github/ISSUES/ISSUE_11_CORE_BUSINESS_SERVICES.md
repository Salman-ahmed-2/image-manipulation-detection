# [ISSUE #11] Core Business Logic Services (Detection & ELA Services)

## 📌 Issue Metadata
- **Milestone:** M3 — Transfer Learning & Comparison
- **Phase:** Phase 5 (Model Serving & Backend)
- **Estimated Effort:** 3–4 hours
- **Labels:** `services`, `business-logic`, `detection`, `ela`
- **Dependencies:** Issue #2 (`utils`), Issue #3 (`ela_generator`), Issue #4 (`preprocessing`), Issue #10 (`predictor`)
- **Blocks:** Issue #12 (Flask Routes), Issue #13 (Report Service)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a Senior Backend Architect.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/architecture/COMPONENT_ARCHITECTURE.md`
> 2. `docs/architecture/DATA_FLOW.md`
> 3. `docs/application/BACKEND_DOCUMENTATION.md`
> 4. `AGENTS.md` (Strict rules: Business logic lives ONLY in `src/services/`, never in web routes, attach `Config.ELA_DISCLAIMER` to all results).

---

## 🎯 Objective & Context
Implement `src/services/detection_service.py` and `src/services/ela_service.py`. The service layer acts as the unified bridge between the web controllers and the underlying vision, deep learning, and forensic modules. It orchestrates file validation, tensor preprocessing, inference execution, ELA rendering, and session aggregation into a clean, presentation-ready analysis result.

---

## 📋 Technical Requirements

### 1. ELA Service (`src/services/ela_service.py`)
- Implement `class ELAService`:
  - `generate_and_save(image_path: Path, session_id: str, quality: int = 90) -> Path`:
    - Calls `ELAGenerator.generate()`.
    - Saves output PNG to `Config.UPLOAD_FOLDER / session_id / "ela_result.png"`.
    - Returns the path to the generated ELA artifact.

### 2. Detection Service (`src/services/detection_service.py`)
- Implement `class DetectionService`:
  ```python
  class DetectionService:
      def __init__(self, model_name: Optional[str] = None):
          self.model_name = model_name or Config.ACTIVE_MODEL
          self.predictor = Predictor(model_name=self.model_name)
          self.ela_service = ELAService()

      def analyze_image(
          self,
          file_storage: Any,
          session_id: str,
          model_choice: Optional[str] = None
      ) -> Dict[str, Any]:
          """Orchestrate end-to-end image authenticity analysis.
          
          Workflow:
          1. Validate uploaded file payload (magic bytes, size, format).
          2. Save original file securely to temp/uploads/<session_id>/<uuid>_orig.<ext>.
          3. Preprocess image into batch tensor (224, 224, 3).
          4. Execute model forward pass and extract confidence metrics.
          5. Generate ELA visualization map (PNG).
          6. Compile results dictionary with Config.ELA_DISCLAIMER.
          
          Returns:
              Comprehensive results dictionary ready for template rendering.
          """
  ```
- **Results Structure:**
  ```python
  {
      "session_id": session_id,
      "verdict_label": "Potentially Manipulated",
      "verdict_code": 1,
      "confidence": 94.20,
      "raw_probability": 0.9420,
      "model_used": "mobilenet_v2",
      "original_image_path": str(orig_path),
      "ela_image_path": str(ela_path),
      "original_filename": file_storage.filename,
      "disclaimer": Config.ELA_DISCLAIMER,
      "timestamp": datetime.utcnow().isoformat()
  }
  ```

---

## 📂 Target Files
- `src/services/ela_service.py`
- `src/services/detection_service.py`

---

## 🧪 Verification & Testing
```bash
# Verify DetectionService instantiation and method signatures
python3 -c "
from src.services.detection_service import DetectionService
service = DetectionService()
print('DetectionService initialized successfully with model:', service.model_name)
"
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] `DetectionService` coordinates file validation, preprocessing, prediction, and ELA generation cleanly.
- [ ] `Config.ELA_DISCLAIMER` is attached to every analysis result object.
- [ ] Domain exceptions are caught and surfaced with clean messages.
- [ ] No ML inference code or ELA logic is leaked into the web route layer.
