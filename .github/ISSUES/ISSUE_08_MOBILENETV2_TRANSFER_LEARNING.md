# [ISSUE #8] MobileNetV2 Transfer Learning & Two-Phase Fine-Tuning Pipeline

## 📌 Issue Metadata
- **Milestone:** M3 — Transfer Learning & Comparison
- **Phase:** Phase 4 (Deep Learning Models)
- **Estimated Effort:** 4–5 hours
- **Labels:** `machine-learning`, `transfer-learning`, `mobilenet`, `fine-tuning`
- **Dependencies:** Issue #4 (`preprocessing`), Issue #6 (`dataset_split.csv`), Issue #7 (`callbacks.py`)
- **Blocks:** Issue #9 (Model Evaluation), Issue #10 (Model Loader)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a Transfer Learning & Computer Vision Specialist.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/machine_learning/MOBILENETV2_ARCHITECTURE.md`
> 2. `docs/machine_learning/MODEL_TRAINING.md`
> 3. `AGENTS.md` (Strict rules: Two-phase training required, input normalization must use MobileNet scale `[-1, 1]`, weights saved to `artifacts/models/`).

---

## 🎯 Objective & Context
Implement the transfer learning pipeline using a pre-trained **MobileNetV2** backbone in `src/models/mobilenet_model.py` and the two-phase training script in `src/training/train_mobilenet.py`. In Phase 1, the base network is frozen to train a custom binary classification head. In Phase 2, the top 30 layers are unfrozen for fine-tuning at a reduced learning rate ($\eta = 10^{-5}$).

---

## 📋 Technical Requirements

### 1. MobileNetV2 Architecture (`src/models/mobilenet_model.py`)
- `build_mobilenet_model(input_shape=(224, 224, 3)) -> tf.keras.Model`:
  - Load `tf.keras.applications.MobileNetV2(input_shape=input_shape, include_top=False, weights="imagenet")`.
  - Phase 1: Set `base_model.trainable = False`.
  - Attach Classification Head:
    `GlobalAveragePooling2D()` $\rightarrow$ `Dense(256, activation="relu")` $\rightarrow$ `Dropout(0.4)` $\rightarrow$ `Dense(128, activation="relu")` $\rightarrow$ `Dropout(0.3)` $\rightarrow$ `Dense(1, activation="sigmoid")`.
  - Compile with `Adam(learning_rate=1e-3)` and `"binary_crossentropy"`.
- `unfreeze_mobilenet_layers(model: tf.keras.Model, num_layers_to_unfreeze: int = 30, fine_tune_lr: float = 1e-5) -> tf.keras.Model`:
  - Access base MobileNetV2 layer.
  - Set `base_model.trainable = True`.
  - Freeze all base layers except the last `num_layers_to_unfreeze`.
  - Re-compile with `Adam(learning_rate=fine_tune_lr)` to prevent catastrophic forgetting.

### 2. Two-Stage Training Script (`src/training/train_mobilenet.py`)
- Prepare dataset using MobileNetV2 normalization mode: $[-1.0, 1.0]$.
- **Phase 1 Execution:**
  - Fit frozen model for 15 warmup epochs with EarlyStopping.
- **Phase 2 Execution:**
  - Call `unfreeze_mobilenet_layers(model, num_layers_to_unfreeze=30, fine_tune_lr=1e-5)`.
  - Fit for an additional 25 epochs.
- Save best model checkpoint to `artifacts/models/mobilenet_model.keras`.

### 3. Unit Tests (`tests/test_models.py` - Part 2)
- Test `build_mobilenet_model()` constructs expected layers.
- Test base model layers have `trainable == False` initially.
- Test `unfreeze_mobilenet_layers()` correctly unfreezes exactly the top $N$ layers.
- Test synthetic forward pass produces valid scalar in $[0.0, 1.0]$.

---

## 📂 Target Files
- `src/models/mobilenet_model.py`
- `src/training/train_mobilenet.py`
- `tests/test_models.py` (enhanced)

---

## 🧪 Verification & Testing
```bash
pytest tests/test_models.py -k "test_mobilenet" -v
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] MobileNetV2 integrates ImageNet weights with custom classification head.
- [ ] Two-phase training logic is cleanly separated and functional.
- [ ] Layer unfreezing selectively activates only the designated top layers.
- [ ] All unit tests in `tests/test_models.py` pass.
