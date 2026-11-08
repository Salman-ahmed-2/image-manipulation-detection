# [ISSUE #7] Custom 4-Block CNN Architecture & Training Pipeline

## 📌 Issue Metadata
- **Milestone:** M2 — Custom CNN Baseline
- **Phase:** Phase 4 (Deep Learning Models)
- **Estimated Effort:** 4–5 hours
- **Labels:** `machine-learning`, `cnn`, `tensorflow`, `keras`, `training`
- **Dependencies:** Issue #4 (`preprocessing`), Issue #6 (`data/metadata/dataset_split.csv`)
- **Blocks:** Issue #9 (Model Evaluation), Issue #10 (Model Loader)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a Deep Learning Engineer.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/machine_learning/CUSTOM_CNN_ARCHITECTURE.md`
> 2. `docs/machine_learning/MODEL_TRAINING.md`
> 3. `AGENTS.md` (Strict rules: Model saved to `artifacts/models/`, input shape `(224, 224, 3)`, no fabricating training results, use Keras callbacks).

---

## 🎯 Objective & Context
Implement the 4-block Custom Convolutional Neural Network architecture in `src/models/cnn_model.py` and the training pipeline in `src/training/train_cnn.py`. The model is designed for binary classification (0 = Authentic, 1 = Potentially Manipulated) and learns localized manipulation artifacts from scratch using balanced class weighting, spatial dropout, and learning rate scheduling.

---

## 📋 Technical Requirements

### 1. Custom CNN Model Builder (`src/models/cnn_model.py`)
- Implement `build_custom_cnn(input_shape: Tuple[int, int, int] = (224, 224, 3)) -> tf.keras.Model`:
  - **Block 1:** `Conv2D(32, (3,3), padding="same", activation="relu")` $\rightarrow$ `BatchNormalization()` $\rightarrow$ `MaxPooling2D((2,2))` $\rightarrow$ `SpatialDropout2D(0.2)`.
  - **Block 2:** `Conv2D(64, (3,3), padding="same", activation="relu")` $\rightarrow$ `BatchNormalization()` $\rightarrow$ `MaxPooling2D((2,2))` $\rightarrow$ `SpatialDropout2D(0.2)`.
  - **Block 3:** `Conv2D(128, (3,3), padding="same", activation="relu")` $\rightarrow$ `BatchNormalization()` $\rightarrow$ `MaxPooling2D((2,2))` $\rightarrow$ `SpatialDropout2D(0.25)`.
  - **Block 4:** `Conv2D(256, (3,3), padding="same", activation="relu")` $\rightarrow$ `BatchNormalization()` $\rightarrow$ `MaxPooling2D((2,2))` $\rightarrow$ `SpatialDropout2D(0.25)`.
  - **Classification Head:**
    `Flatten()` $\rightarrow$ `Dense(512, activation="relu", kernel_regularizer=l2(1e-4))` $\rightarrow$ `Dropout(0.5)` $\rightarrow$ `Dense(256, activation="relu")` $\rightarrow$ `Dropout(0.3)` $\rightarrow$ `Dense(1, activation="sigmoid")`.
  - Compile with:
    - Optimizer: `Adam(learning_rate=1e-3)`
    - Loss: `"binary_crossentropy"`
    - Metrics: `["accuracy", tf.keras.metrics.Precision(name="precision"), tf.keras.metrics.Recall(name="recall")]`

### 2. Training Callbacks (`src/training/callbacks.py`)
- `get_callbacks(model_name: str) -> List[tf.keras.callbacks.Callback]`:
  - `EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True, verbose=1)`
  - `ModelCheckpoint(filepath=Config.MODEL_DIR / f"{model_name}.keras", monitor="val_loss", save_best_only=True, verbose=1)`
  - `ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6, verbose=1)`
  - `CSVLogger(filename=Config.PLOTS_DIR / f"{model_name}_training_history.csv")`

### 3. Training Script (`src/training/train_cnn.py`)
- Loads `data/metadata/dataset_split.csv`.
- Builds train and validation `tf.data.Dataset` streams using `image_loader` and `image_normalizer`.
- Calculates balanced class weights to address moderate class imbalance (~59% authentic vs 41% tampered).
- Executes `model.fit(..., epochs=Config.DEFAULT_EPOCHS, callbacks=callbacks, class_weight=class_weights)`.
- Saves final model artifact to `artifacts/models/cnn_model.keras`.

### 4. Unit Tests (`tests/test_models.py` - Part 1)
- Verify `build_custom_cnn()` compiles without error.
- Verify input shape is `(None, 224, 224, 3)` and output shape is `(None, 1)`.
- Execute a forward pass using synthetic tensor `tf.zeros((2, 224, 224, 3))`; assert output values are strictly within $[0.0, 1.0]$.

---

## 📂 Target Files
- `src/models/cnn_model.py`
- `src/training/callbacks.py`
- `src/training/train_cnn.py`
- `tests/test_models.py`

---

## 🧪 Verification & Testing
```bash
pytest tests/test_models.py -k "test_custom_cnn" -v
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] CNN model architecture matches the 4-block ConvNet specification.
- [ ] Forward pass executes cleanly on CPU and GPU with valid Sigmoid probability output.
- [ ] Training callbacks save best checkpoint to `artifacts/models/` in `.keras` format.
- [ ] `pytest tests/test_models.py` passes 100%.
