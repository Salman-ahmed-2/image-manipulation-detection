# Model Training Specification & Procedures

## 1. Training Environment & Infrastructure
Model training is executed primarily in an accelerated compute environment (such as Google Colab with an NVIDIA T4 / A100 GPU, or a local Linux workstation equipped with CUDA-compatible hardware).

---

## 2. Training Pipelines

### 2.1 Custom CNN Training Protocol
The Custom CNN is trained from scratch to discover localized manipulation artifacts directly from forensic pixel distributions:
- **Optimizer:** Adam with initial learning rate $\eta = 10^{-3}$ ($0.001$).
- **Loss Function:** Binary Cross-Entropy (`binary_crossentropy`).
- **Batch Size:** 32 images.
- **Maximum Epochs:** 50 epochs.
- **Regularization:**
  - Spatial Dropout ($p = 0.25$) after Conv blocks.
  - Fully Connected Dropout ($p = 0.5$) after Dense 512, and ($p = 0.3$) after Dense 256.
  - L2 kernel regularization ($\lambda = 10^{-4}$).

### 2.2 MobileNetV2 Two-Phase Transfer Learning Protocol
MobileNetV2 adapts low-level edge and texture representations learned from ImageNet:

#### Phase 1: Feature Extraction (Top Classifier Warmup)
- **Base Layers:** All 154 layers of MobileNetV2 are **frozen** (`base_model.trainable = False`).
- **Classification Head:** GlobalAveragePooling2D $\rightarrow$ Dense(256, ReLU) $\rightarrow$ Dropout(0.4) $\rightarrow$ Dense(128, ReLU) $\rightarrow$ Dropout(0.3) $\rightarrow$ Dense(1, Sigmoid).
- **Optimizer:** Adam with $\eta = 10^{-3}$.
- **Duration:** 15 epochs.

#### Phase 2: Fine-Tuning (End-to-End Adaptation)
- **Base Layers:** Top 30 layers unfrozen (`trainable = True`).
- **Optimizer:** Adam with low learning rate $\eta = 10^{-5}$ to avoid catastrophic forgetting.
- **Duration:** 25 additional epochs.

---

## 3. Data Augmentation Policy

Digital forensic artifacts can be destroyed by aggressive lossy distortions. The augmentation pipeline uses safe, artifact-preserving spatial transforms:
- Horizontal Flip: Enabled ($p = 0.5$).
- Vertical Flip: Enabled ($p = 0.2$).
- Random Rotation: Minor adjustments $\pm 10^\circ$.
- **Explicitly Disabled Augmentations:**
  - ❌ Heavy JPEG recompression (destroys baseline quantization residuals).
  - ❌ Gaussian blur / Median filtering (erases manipulation boundary traces).
  - ❌ Random color jittering / contrast distortions.

---

## 4. Training Callbacks Architecture

```python
import tensorflow as tf
from pathlib import Path

def get_training_callbacks(model_name: str, checkpoint_dir: str = "artifacts/models") -> list:
    """Instantiate standard production training callbacks."""
    ckpt_path = Path(checkpoint_dir) / f"{model_name}_best.keras"
    
    return [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=8,
            restore_best_weights=True,
            verbose=1
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(ckpt_path),
            monitor="val_loss",
            save_best_only=True,
            verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-6,
            verbose=1
        ),
        tf.keras.callbacks.CSVLogger(
            filename=f"artifacts/plots/{model_name}_training_log.csv"
        )
    ]
```

> ⚠️ **ACADEMIC INTEGRITY NOTE:**
> No fabricated training results, loss curves, or final accuracy numbers are documented here. All numerical metrics will be recorded in `docs/reports/RESULTS_TEMPLATE.md` during actual training execution.
