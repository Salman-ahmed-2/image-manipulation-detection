# Functional Requirements Specification

## FR-001: Image File Upload
- **Description:** Provide an interactive upload component allowing users to submit a photographic image from their local filesystem.
- **Primary Actor:** General User.
- **Preconditions:** User has loaded the web application home page (`/`).
- **Postconditions:** File payload is received by the Flask application and staged in temporary session storage.
- **Main Flow:**
  1. User navigates to the upload interface.
  2. User selects an image via drag-and-drop or file picker.
  3. Client-side script verifies extension and preliminary file size.
  4. User clicks "Analyze Image".
  5. Browser dispatches a `multipart/form-data` POST request to `/analyze`.
- **Alternative Flows:**
  - *3a. Unsupported Extension:* Interface alerts user immediately without submitting payload.
  - *3b. Exceeds Size:* Interface alerts user that file exceeds the 16MB threshold.
- **Priority:** High (Mandatory).

---

## FR-002: Server-Side File Validation & Sanitization
- **Description:** Rigorously validate file integrity, verify binary magic numbers, sanitize filename, and enforce size constraints.
- **Primary Actor:** Image Validation Module (`src/utils/file_validator.py`).
- **Preconditions:** POST request received at `/analyze`.
- **Postconditions:** Validated file saved to `temp/uploads/<session_id>/<uuid_filename>.<ext>` or rejected with a clean error.
- **Main Flow:**
  1. Backend checks presence of `image` file key in `request.files`.
  2. System extracts file extension and checks against whitelist (`jpg`, `jpeg`, `png`).
  3. System inspects the first 32 bytes for binary magic signatures:
     - JPEG: `FF D8 FF`
     - PNG: `89 50 4E 47 0D 0A 1A 0A`
  4. System confirms byte length does not exceed `Config.MAX_CONTENT_LENGTH` (16 MB).
  5. System sanitizes filename using `werkzeug.utils.secure_filename` and assigns a UUID prefix to prevent collisions.
- **Alternative Flows:**
  - *1a. Missing file payload:* Throw `ValidationError("No file uploaded")`, return HTTP 400.
  - *3a. Spoofed file (e.g. executable renamed to .jpg):* Throw `ValidationError("Invalid image signature")`, return HTTP 400.
- **Priority:** High (Mandatory).

---

## FR-003: Image Preprocessing Pipeline
- **Description:** Ingest the validated raw image, ensure 3-channel RGB format, resize to model input dimensions, and produce normalized tensors.
- **Primary Actor:** Preprocessing Module (`src/preprocessing/`).
- **Preconditions:** Image file saved to session temporary directory.
- **Postconditions:** A batch-ready NumPy array `(1, 224, 224, 3)` with float32 values scaled to `[0.0, 1.0]` (or `[-1.0, 1.0]` for MobileNetV2).
- **Main Flow:**
  1. `image_loader.py` opens image using Pillow, converting grayscale or RGBA modes cleanly to RGB.
  2. `image_resizer.py` scales the image to exactly `(224, 224)` using bicubic interpolation.
  3. `image_normalizer.py` converts the array to `float32` and divides by 255.0 (or applies MobileNetV2 preprocessing function).
  4. Module expands dimensions to create batch shape `(1, 224, 224, 3)`.
- **Alternative Flows:**
  - *1a. Truncated or corrupt image:* Catch `PIL.UnidentifiedImageError`, log warning, return HTTP 400 with user-friendly error.
- **Priority:** High (Mandatory).

---

## FR-004: Custom CNN Model Inference
- **Description:** Execute binary classification on the preprocessed tensor using the trained Custom 4-block CNN.
- **Primary Actor:** Deep Learning Prediction Module (`src/models/predictor.py`).
- **Preconditions:** Preprocessed tensor ready; Custom CNN weights loaded in memory via `model_loader.py`.
- **Postconditions:** Floating-point probability scalar between `0.0` and `1.0`.
- **Main Flow:**
  1. `predictor.py` passes tensor to `cnn_model.predict(tensor)`.
  2. Model executes feed-forward computation across Conv2D, MaxPool2D, Dense, and Sigmoid layers.
  3. Raw probability $P$ is produced, where $P \ge 0.5$ denotes Manipulated and $P < 0.5$ denotes Authentic.
- **Priority:** High (Mandatory).

---

## FR-005: MobileNetV2 Model Inference
- **Description:** Execute binary classification using the fine-tuned MobileNetV2 transfer learning model.
- **Primary Actor:** Deep Learning Prediction Module (`src/models/predictor.py`).
- **Preconditions:** MobileNetV2 weights loaded in memory.
- **Postconditions:** Floating-point probability scalar between `0.0` and `1.0`.
- **Main Flow:**
  1. Ingest preprocessed tensor normalized to `[-1.0, 1.0]`.
  2. Feed tensor through inverted residual blocks and custom classification head.
  3. Return raw classification probability.
- **Priority:** High (Mandatory).

---

## FR-006: Prediction Verdict & Confidence Computation
- **Description:** Translate raw model output probabilities into categorical verdicts and intuitive confidence percentages.
- **Primary Actor:** Detection Service (`src/services/detection_service.py`).
- **Preconditions:** Prediction probability $P \in [0.0, 1.0]$ available.
- **Postconditions:** Dictionary containing `label` ("Authentic" | "Potentially Manipulated") and `confidence` (percentage string).
- **Logic:**
  - If $P \ge 0.5$:
    - Label = "Potentially Manipulated"
    - Confidence = $P \times 100\%$
  - Else:
    - Label = "Authentic"
    - Confidence = $(1.0 - P) \times 100\%$
- **Priority:** High (Mandatory).

---

## FR-007: Error Level Analysis (ELA) Generation
- **Description:** Perform JPEG recompression, compute absolute pixel error, amplify the residual, and produce an ELA visualization image.
- **Primary Actor:** ELA Generator (`src/preprocessing/ela_generator.py`).
- **Preconditions:** Source image path verified.
- **Postconditions:** ELA visualization image saved to `temp/uploads/<session_id>/ela_<filename>.png`.
- **Main Flow:**
  1. Open image in RGB mode.
  2. If PNG, log explicit diagnostic warning: *"ELA on PNG inputs reflects conversion recompression and may introduce boundary artifacts."*
  3. Save in-memory JPEG copy at quality = 90 (`Config.ELA_QUALITY`).
  4. Reload the recompressed JPEG image.
  5. Calculate absolute pixel-wise difference: $\Delta = |I_{\text{orig}} - I_{\text{recomp}}|$.
  6. Apply 10x enhancement multiplier: $E = \text{clip}(\Delta \times 10, 0, 255)$.
  7. Save resulting map as PNG to preserve exact difference artifacts.
- **Priority:** High (Mandatory).

---

## FR-008: Side-by-Side Visualization Dashboard
- **Description:** Display original image and generated ELA map side-by-side with zoom/inspect capability.
- **Primary Actor:** Frontend UI Layer (`web/templates/result.html`).
- **Preconditions:** Detection service completes successfully.
- **Postconditions:** Rendered HTML view containing both images, verdict badge, confidence bar, and disclaimer.
- **Priority:** High (Mandatory).

---

## FR-009: Downloadable PDF Forensic Report
- **Description:** Compile analysis findings, prediction metrics, metadata, original image thumbnail, ELA image, and disclaimer into a downloadable PDF document.
- **Primary Actor:** Report Service (`src/services/report_service.py`).
- **Preconditions:** User clicks "Download PDF Report" from results dashboard.
- **Postconditions:** Streamed binary PDF (`Content-Type: application/pdf`).
- **Main Flow:**
  1. User triggers GET `/report/<session_id>`.
  2. Report service instantiates `FPDF` canvas.
  3. Injects project title, date/time stamp, model name, and input dimensions.
  4. Places original image and ELA visualization side-by-side.
  5. Injects prediction verdict and confidence progress visual.
  6. Appends mandatory legal/academic forensic disclaimer in prominent alert box.
  7. Streams output directly to browser with `attachment; filename="forensic_report.pdf"`.
- **Priority:** High (Mandatory).

---

## FR-010: Ephemeral Storage Lifecycle & Session Purge
- **Description:** Automatically delete all user-uploaded files, generated ELA maps, and PDF artifacts after analysis session expiration.
- **Primary Actor:** Application Cleanup Task (`src/services/detection_service.py`).
- **Preconditions:** Session ends, report is downloaded, or 30-minute idle threshold reached.
- **Postconditions:** User directory under `temp/uploads/<session_id>/` is completely removed from disk.
- **Priority:** High (Mandatory).
