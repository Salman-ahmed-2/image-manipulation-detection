# Prompt Templates for AI-Assisted Development

This document provides standardized, context-rich prompt templates designed for AI coding assistants (Copilot, Gemini, Claude, Cursor, ChatGPT). Each template incorporates file constraints, architectural boundaries, and coding standards to ensure safe, reproducible AI code generation.

---

## Template 1: Dataset Exploration & Integrity Check
```markdown
You are assisting with the "Image Manipulation Detection System Using Deep Learning" project.
Before writing code, review:
- docs/dataset/DATASET_OVERVIEW.md
- docs/dataset/DATA_QUALITY.md

Task: Implement exploratory analysis logic for the CASIA v2.0 dataset under data/raw/casia_v2/.
Requirements:
1. Scan image files and identify authentic (prefix 'Au_') vs tampered ('Tp_S_' copy-move, 'Tp_D_' splicing).
2. Check for truncated or unidentifiable image files using Pillow (verify() method).
3. Record width, height, channel mode, and byte sizes into a Pandas DataFrame.
4. Output a summary table showing class balance and dimension distributions.
5. Follow PEP 8 and use Google-style docstrings. Do NOT fabricate missing files or metrics.
```

---

## Template 2: Dataset Preparation & Group-Aware Split
```markdown
You are implementing `scripts/prepare_dataset.py` for the Image Manipulation Detection project.
Before writing code, review:
- docs/dataset/DATASET_PREPARATION.md
- docs/dataset/DATA_SPLITTING.md
- docs/dataset/LABEL_MAPPING.md

Requirements:
1. Parse filenames across `data/raw/casia_v1/` and `data/raw/casia_v2/`.
2. Extract the donor base ID to construct a `group_id` for every image.
3. Use scikit-learn's `GroupShuffleSplit` to create a 70% train, 15% validation, and 15% test split.
4. Guarantee that authentic donor images and their tampered derivatives remain in the same split.
5. Export clean metadata to:
   - `data/metadata/dataset_inventory.csv`
   - `data/metadata/dataset_labels.csv`
   - `data/metadata/dataset_split.csv`
6. Include defensive error handling and logger outputs.
```

---

## Template 3: Error Level Analysis (ELA) Generator
```markdown
You are implementing `src/preprocessing/ela_generator.py` for the Image Manipulation Detection project.
Before writing code, review:
- docs/image_forensics/ELA_OVERVIEW.md
- docs/image_forensics/ELA_IMPLEMENTATION.md
- docs/image_forensics/ELA_LIMITATIONS.md

Requirements:
1. Implement the `ELAGenerator` class with method:
   `generate(image_input, output_path=None, quality=90, enhancement_factor=10.0) -> PIL.Image.Image`
2. Convert image to RGB mode. If input is PNG, log a diagnostic warning explaining format conversion artifacts.
3. Recompress to JPEG in-memory via io.BytesIO at quality=90.
4. Compute absolute difference between original and recompressed image using `ImageChops.difference`.
5. Scale brightness by enhancement_factor and return enhanced PIL Image.
6. Use Pillow exclusively. Do not import OpenCV.
7. Include complete Google-style docstrings and type annotations.
```

---

## Template 4: Custom CNN Architecture
```markdown
You are implementing `src/models/cnn_model.py` for the Image Manipulation Detection project.
Before writing code, review:
- docs/machine_learning/CUSTOM_CNN_ARCHITECTURE.md
- docs/machine_learning/MODEL_TRAINING.md

Requirements:
1. Implement function:
   `build_custom_cnn(input_shape=(224, 224, 3)) -> tf.keras.Model`
2. Construct 4 Convolutional blocks:
   - Block 1: Conv2D(32, (3,3), relu) + BatchNormalization + MaxPooling2D((2,2)) + SpatialDropout2D(0.25)
   - Block 2: Conv2D(64, (3,3), relu) + BatchNormalization + MaxPooling2D((2,2)) + SpatialDropout2D(0.25)
   - Block 3: Conv2D(128, (3,3), relu) + BatchNormalization + MaxPooling2D((2,2)) + SpatialDropout2D(0.25)
   - Block 4: Conv2D(256, (3,3), relu) + BatchNormalization + MaxPooling2D((2,2)) + SpatialDropout2D(0.25)
3. Dense classification head:
   - Flatten() -> Dense(512, relu) -> Dropout(0.5) -> Dense(256, relu) -> Dropout(0.3) -> Dense(1, sigmoid)
4. Compile with Adam optimizer (lr=0.001) and binary_crossentropy loss.
5. Include type hints and Google-style docstrings.
```

---

## Template 5: MobileNetV2 Transfer Learning Architecture
```markdown
You are implementing `src/models/mobilenet_model.py` for the Image Manipulation Detection project.
Before writing code, review:
- docs/machine_learning/MOBILENETV2_ARCHITECTURE.md
- docs/machine_learning/MODEL_TRAINING.md

Requirements:
1. Implement function:
   `build_mobilenet_v2(input_shape=(224, 224, 3), fine_tune_layers=30) -> tf.keras.Model`
2. Load `tf.keras.applications.MobileNetV2(weights='imagenet', include_top=False, input_shape=input_shape)`.
3. Freeze base layers (`base_model.trainable = False`) for Phase 1.
4. Attach head: GlobalAveragePooling2D() -> Dense(256, relu) -> Dropout(0.4) -> Dense(128, relu) -> Dropout(0.3) -> Dense(1, sigmoid).
5. Provide helper function `unfreeze_for_fine_tuning(model, fine_tune_layers=30, learning_rate=1e-5)` for Phase 2.
6. Use TensorFlow 2.x Keras APIs with type hints and docstrings.
```

---

## Template 6: Model Evaluation & Metric Calculation
```markdown
You are implementing `src/evaluation/metrics.py` and `scripts/evaluate.py`.
Before writing code, review:
- docs/machine_learning/MODEL_EVALUATION.md
- docs/machine_learning/MODEL_COMPARISON.md

Requirements:
1. In `src/evaluation/metrics.py`, provide functions calculating Accuracy, Precision, Recall, F1-Score, and ROC-AUC.
2. In `scripts/evaluate.py`, load trained `.keras` model, evaluate on `data/splits/test/`, and generate:
   - Console classification report.
   - Confusion matrix saved to `artifacts/plots/<model>_confusion_matrix.png`.
   - ROC curve saved to `artifacts/plots/<model>_roc_curve.png`.
3. Never fabricate or hardcode expected metrics. Compute from actual test predictions.
```

---

## Template 7: Flask Detection Service Layer
```markdown
You are implementing `src/services/detection_service.py` for the Image Manipulation Detection project.
Before writing code, review:
- docs/architecture/COMPONENT_ARCHITECTURE.md
- docs/application/BACKEND_DOCUMENTATION.md

Requirements:
1. Implement `DetectionService` class coordinating:
   - File validation via `src/utils/file_validator.py`.
   - Preprocessing via `src/preprocessing/image_loader.py`.
   - Model prediction via `src/models/predictor.py`.
   - ELA generation via `src/preprocessing/ela_generator.py`.
2. Return a standardized results dictionary containing verdict label, confidence percentage, raw probability, and artifact URLs.
3. Attach `Config.ELA_DISCLAIMER` to all result objects.
4. Catch domain exceptions and re-raise structured service errors.
```

---

## Template 8: Bootstrap 5 Results Dashboard Template
```markdown
You are implementing `web/templates/result.html` for the Image Manipulation Detection project.
Before writing code, review:
- docs/application/FRONTEND_DOCUMENTATION.md

Requirements:
1. Extend `base.html`.
2. Display verdict badge (Green for Authentic, Red/Orange for Potentially Manipulated).
3. Display confidence score as a Bootstrap 5 progress bar.
4. Render side-by-side responsive cards displaying the Original Image and the ELA Visualization.
5. Prominently display the mandatory forensic disclaimer alert box.
6. Provide action buttons: "Download PDF Report" (`/report/{{ session_id }}`) and "Analyze Another Image" (`/`).
```

---

## Template 9: PDF Report Generation Service
```markdown
You are implementing `src/services/report_service.py` using `fpdf2`.
Before writing code, review:
- docs/application/REPORT_GENERATION.md

Requirements:
1. Implement `ReportService.generate_pdf(session_data, orig_image_path, ela_image_path) -> bytes`.
2. Assemble clean header with project title, timestamp, and unique report ID.
3. Embed original photograph thumbnail and ELA visualization map side-by-side.
4. Display prediction verdict, confidence score, and model metadata.
5. Ingest and display the mandatory academic/forensic disclaimer text in a bordered box.
6. Return binary bytes ready for streaming as an attachment.
```

---

## Template 10: Pytest Unit Test Suite
```markdown
You are authoring unit tests under `tests/`.
Before writing code, review:
- docs/testing/UNIT_TESTING.md
- docs/testing/TESTING_STRATEGY.md

Requirements:
1. In `tests/conftest.py`, define synthetic image fixtures (valid JPEG, valid PNG, corrupted bytes) using PIL in-memory.
2. Under no circumstances access actual CASIA dataset files from disk.
3. In `tests/test_file_validation.py`, test allowed extensions, magic bytes verification, oversized payloads, and filename sanitization.
4. In `tests/test_ela.py`, test recompression output dimensions, enhancement factor scaling, and quality boundary values.
5. Assert on specific return types and ranges. Aim for >80% code coverage.
```

---

## Template 11: Bug Resolution & Defensive Patching
```markdown
You are resolving a reported defect in the Image Manipulation Detection project.
Before modifying code:
1. Inspect the stack trace and identify the exact module and function.
2. Read the corresponding module documentation under `docs/`.
3. Isolate the root cause without altering unrelated functionality.
4. Apply defensive validation and log errors using `src/utils/logger.py`.
5. Add a regression unit test in `tests/` reproducing the edge case.
```
