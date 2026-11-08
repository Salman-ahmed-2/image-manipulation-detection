# Custom CNN Architecture

## Table of Contents

1. [Architecture Rationale](#1-architecture-rationale)
2. [Layer-by-Layer Architecture](#2-layer-by-layer-architecture)
3. [Training Configuration](#3-training-configuration)
4. [Data Augmentation](#4-data-augmentation)
5. [Class Weight Handling](#5-class-weight-handling)
6. [Architecture Code Skeleton](#6-architecture-code-skeleton)
7. [Expected Training Behavior](#7-expected-training-behavior)
8. [Model Saving](#8-model-saving)
9. [Known Challenges](#9-known-challenges)

---

## 1. Architecture Rationale

### Why a Custom CNN for Image Forensics?

A Convolutional Neural Network trained from scratch is chosen as the first model for the following reasons:

**Full Architectural Control**
Unlike transfer learning, a custom CNN allows every layer, filter size, depth, and regularization choice to be tuned specifically for the forensic detection task. The network is not constrained by feature detectors learned for a different domain (e.g., ImageNet object classification).

**Learning Forensics-Specific Features**
Image manipulation leaves low-level artifacts that may differ fundamentally from the semantic object features learned during ImageNet pretraining. A custom CNN trained on ELA-transformed images can potentially learn to detect:
- Block boundary artifacts from JPEG splicing
- Noise level discontinuities at manipulation boundaries
- Compression-level inconsistencies between regions
- Copy-move replication patterns in pixel statistics

**Transparency for Research Comparison**
Having a from-scratch baseline allows fair comparison with the transfer learning approach (MobileNetV2). This comparison is a core research contribution of the project.

**Progressive Complexity Design**
The architecture follows the standard pattern of progressive spatial compression via pooling layers while increasing the number of filters (feature maps) at each stage. This allows the network to:
- Early layers: detect simple features (edges, gradients, JPEG block patterns)
- Middle layers: combine features into more complex patterns
- Late layers: detect high-level forgery indicators before classification

---

## 2. Layer-by-Layer Architecture

The architecture consists of **4 convolutional blocks** (each with Conv2D + MaxPooling2D), followed by **2 fully connected dense layers** with dropout regularization, and a **sigmoid output** for binary classification.

### Architecture Table

| # | Layer | Type | Configuration | Output Shape |
|---|---|---|---|---|
| 1 | Input | Input Layer | 224 × 224 × 3 (RGB) | `(224, 224, 3)` |
| 2 | Conv1 | Conv2D | 32 filters, 3×3 kernel, ReLU, same/valid padding | `(222, 222, 32)` |
| 3 | Pool1 | MaxPooling2D | 2×2 pool size, stride 2 | `(111, 111, 32)` |
| 4 | Conv2 | Conv2D | 64 filters, 3×3 kernel, ReLU | `(109, 109, 64)` |
| 5 | Pool2 | MaxPooling2D | 2×2 pool size, stride 2 | `(54, 54, 64)` |
| 6 | Conv3 | Conv2D | 128 filters, 3×3 kernel, ReLU | `(52, 52, 128)` |
| 7 | Pool3 | MaxPooling2D | 2×2 pool size, stride 2 | `(26, 26, 128)` |
| 8 | Conv4 | Conv2D | 256 filters, 3×3 kernel, ReLU | `(24, 24, 256)` |
| 9 | Pool4 | MaxPooling2D | 2×2 pool size, stride 2 | `(12, 12, 256)` |
| 10 | Flatten | Flatten | — | `(36864,)` |
| 11 | Dense1 | Dense (FC) | 512 units, ReLU activation | `(512,)` |
| 12 | Dropout1 | Dropout | Rate = 0.5 | `(512,)` |
| 13 | Dense2 | Dense (FC) | 256 units, ReLU activation | `(256,)` |
| 14 | Dropout2 | Dropout | Rate = 0.3 | `(256,)` |
| 15 | Output | Dense (FC) | 1 unit, Sigmoid activation | `(1,)` |

> [!NOTE]
> Output shapes assume **valid** (no) padding for Conv2D layers. If **same** padding is used, the spatial dimensions after convolution will match the input spatial dimensions to that layer, changing intermediate shapes. The table above reflects valid padding behavior. The actual padding setting used is defined in the implementation code.

### Design Decisions

**Why 4 Convolutional Blocks?**
Four blocks of strided pooling reduce the 224×224 spatial input down to a 12×12 feature map. This progressive reduction provides a sufficient receptive field for the final dense layers to integrate spatial information across the entire image — necessary for detecting splicing that spans large regions.

**Why Increasing Filter Counts (32→64→128→256)?**
Increasing depth encourages the network to compose simpler low-level features (detected by fewer early filters) into increasingly complex representations. This follows standard CNN design practice validated across many computer vision tasks.

**Why ReLU Activation?**
ReLU (Rectified Linear Unit) is used in all convolutional and dense layers because:
- It avoids the vanishing gradient problem during backpropagation
- It is computationally efficient
- It introduces nonlinearity while maintaining gradient flow for positive activations

**Why Sigmoid Output (not Softmax)?**
Since this is binary classification, the output layer uses a single neuron with Sigmoid. This directly outputs a probability in [0, 1], where values ≥ 0.5 indicate the manipulated class.

**Why Two Dropout Layers?**
Dropout is a critical regularization technique for this task due to the relatively modest dataset size (~14,000 images). The higher dropout rate (0.5) after Dense1 aggressively regularizes the larger 512-unit layer. The lower rate (0.3) after Dense2 provides lighter regularization for the smaller 256-unit layer, allowing some feature specificity to be retained before the output.

---

## 3. Training Configuration

### Loss Function

| Setting | Value | Rationale |
|---|---|---|
| **Loss Function** | Binary Cross-Entropy | Standard loss for binary classification; penalizes confident wrong predictions |
| **Formula** | `-[y·log(ŷ) + (1−y)·log(1−ŷ)]` | Measures divergence between predicted probability and true label |

Binary cross-entropy is appropriate because the model outputs a sigmoid probability and the task is a two-class problem.

### Optimizer

| Setting | Value |
|---|---|
| **Optimizer** | Adam (Adaptive Moment Estimation) |
| **Initial Learning Rate** | 0.001 |
| **Beta 1** | 0.9 (default) |
| **Beta 2** | 0.999 (default) |
| **Epsilon** | 1e-7 (default) |

Adam is chosen for its adaptive learning rate properties. It maintains per-parameter learning rates and converges faster than standard SGD on most deep learning tasks.

### Training Parameters

| Parameter | Value | Notes |
|---|---|---|
| **Batch Size** | 32 | Balance between memory usage and gradient estimation quality |
| **Maximum Epochs** | 50 | Upper bound; training stops earlier via EarlyStopping |
| **Early Stopping Patience** | 10 | Stop if validation loss does not improve for 10 consecutive epochs |
| **Early Stopping Monitor** | `val_loss` | Validation loss is the primary stopping criterion |
| **Early Stopping Mode** | `min` | Lower validation loss is better |
| **LR Reduction Patience** | 5 | Reduce LR if no improvement for 5 epochs |
| **LR Reduction Factor** | 0.5 | New LR = current LR × 0.5 |
| **LR Reduction Minimum** | 1e-7 | Prevents LR from becoming uselessly small |
| **Checkpoint Monitor** | `val_loss` | Save model at the epoch with the lowest validation loss |

### Callback Summary

| Callback | Configuration | Purpose |
|---|---|---|
| `EarlyStopping` | `patience=10, monitor='val_loss'` | Prevent overfitting; stop training when validation stops improving |
| `ModelCheckpoint` | `save_best_only=True, monitor='val_loss'` | Persist the best model weights to disk |
| `ReduceLROnPlateau` | `patience=5, factor=0.5` | Fine-tune learning rate when progress plateaus |
| `TensorBoard` | Log directory: `artifacts/logs/cnn/` | Visualize training curves in TensorBoard |

---

## 4. Data Augmentation

Data augmentation is applied **only to the training set** to artificially increase dataset diversity and reduce overfitting. The validation and test sets receive no augmentation (only normalization).

### Augmentation Parameters

| Transformation | Setting | Rationale |
|---|---|---|
| **Horizontal Flip** | Enabled | Manipulations can appear on either side of an image |
| **Vertical Flip** | Enabled | Less common but valid for some image types |
| **Rotation** | ±20° | Mimics slight orientation variation; keeps forensic artifacts intact |
| **Zoom** | ±10% | Simulates slight camera distance variation |
| **Brightness Adjustment** | Range: [0.8, 1.2] | Mimics exposure variation without destroying compression artifacts |
| **Width Shift** | ±5% | Minor horizontal translation |
| **Height Shift** | ±5% | Minor vertical translation |
| **Fill Mode** | `nearest` | Fill newly created pixels with nearest neighbor values |

> [!CAUTION]
> Avoid aggressive augmentations (e.g., JPEG re-compression, sharpening, blurring) during training, as these can destroy or mimic the ELA artifacts that the network is trying to learn to detect.

---

## 5. Class Weight Handling

The CASIA datasets may not have perfectly equal numbers of authentic and manipulated images. If a class imbalance exists, the network may become biased toward predicting the majority class.

### Strategy: Computed Class Weights

Class weights are computed from the training set distribution and passed to the `model.fit()` call via the `class_weight` parameter:

```python
# Class weight computation (documentation — not final implementation)
# from sklearn.utils.class_weight import compute_class_weight
# class_weights = compute_class_weight('balanced', classes=[0, 1], y=train_labels)
# class_weight_dict = {0: class_weights[0], 1: class_weights[1]}
```

**Effect of Class Weighting**: The loss function penalizes misclassifications of the minority class more heavily during gradient updates. This encourages the model to maintain high recall on the minority class (typically the manipulated class) even if it slightly reduces overall accuracy.

> [!TIP]
> As an alternative or complement to class weighting, consider oversampling the minority class using techniques such as duplication or SMOTE (applied at the feature level). However, class weighting is simpler to implement and effective for moderate imbalances.

---

## 6. Architecture Code Skeleton

The following code sketch illustrates the sequential layer structure of the Custom CNN. This is **documentation only** — it is not a complete, runnable implementation.

```python
# Architecture sketch — documentation only, not final implementation
# Full implementation is in src/models/custom_cnn.py

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Conv2D, MaxPooling2D, Flatten,
    Dense, Dropout, Input
)

def build_custom_cnn(input_shape=(224, 224, 3)):
    """
    Custom CNN for binary image forgery detection.
    
    Args:
        input_shape: Tuple (height, width, channels). Default: (224, 224, 3)
    
    Returns:
        Uncompiled Keras Sequential model.
    """
    model = Sequential([
        # Block 1
        Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
        MaxPooling2D(2, 2),

        # Block 2
        Conv2D(64, (3, 3), activation='relu'),
        MaxPooling2D(2, 2),

        # Block 3
        Conv2D(128, (3, 3), activation='relu'),
        MaxPooling2D(2, 2),

        # Block 4
        Conv2D(256, (3, 3), activation='relu'),
        MaxPooling2D(2, 2),

        # Classifier Head
        Flatten(),
        Dense(512, activation='relu'),
        Dropout(0.5),
        Dense(256, activation='relu'),
        Dropout(0.3),

        # Output
        Dense(1, activation='sigmoid')
    ], name='custom_cnn_forensics')

    return model

# Compilation sketch
# model = build_custom_cnn()
# model.compile(
#     optimizer=Adam(learning_rate=0.001),
#     loss='binary_crossentropy',
#     metrics=['accuracy', Precision(), Recall(), AUC()]
# )
```

---

## 7. Expected Training Behavior

The following describes the **conceptually expected** behavior of a correctly configured training run. These are not performance guarantees.

### Early Training (Epochs 1–10)

- **Training loss**: Should decrease rapidly as the network learns basic features
- **Validation loss**: Should also decrease, tracking training loss with a small gap
- **Training accuracy**: Rises quickly from ~50% (random) toward higher values
- **Validation accuracy**: Rises similarly; small gap between train and val is expected and healthy

### Mid Training (Epochs 10–30)

- Training loss continues to decrease, potentially at a slower rate
- Validation loss should still decrease or remain stable
- If validation loss begins to **rise while training loss falls**, this is an **overfitting signal**
- `ReduceLROnPlateau` may trigger, lowering the learning rate and potentially resuming improvement

### Late Training / Convergence (Epochs 30–50)

- Both losses should be stable and close together (small generalization gap)
- `EarlyStopping` will trigger if no improvement is seen for 10 epochs
- The best model checkpoint (lowest `val_loss`) is saved automatically

### Overfitting Warning Signs

| Signal | Likely Cause | Remedy |
|---|---|---|
| Val loss rising, train loss falling | Overfitting | Increase dropout, reduce model size, add augmentation |
| Both losses stagnating at high values | Underfitting | Increase model capacity, reduce dropout, adjust LR |
| Oscillating val loss | LR too high | Allow ReduceLROnPlateau to reduce LR |
| Very slow convergence | LR too low or batch size mismatch | Increase LR or check data pipeline |

---

## 8. Model Saving

The trained Custom CNN model is saved to the following locations:

| Format | Path | Use Case |
|---|---|---|
| **Keras HDF5** | `artifacts/models/cnn_model.h5` | Default; easy to load with `tf.keras.models.load_model()` |
| **SavedModel** | `artifacts/models/cnn_savedmodel/` | TensorFlow's native format; better for TensorFlow Serving |
| **Best Checkpoint** | `artifacts/models/cnn_best_checkpoint.h5` | Saved during training at best `val_loss` epoch |

```python
# Model saving sketch (documentation only)
# model.save('artifacts/models/cnn_model.h5')
# or
# model.save('artifacts/models/cnn_savedmodel/')  # SavedModel format
```

> [!NOTE]
> When running on Google Colab, save model files to the mounted Google Drive path (e.g., `/content/drive/MyDrive/image_forensics/artifacts/models/`) to ensure they persist after the session ends.

---

## 9. Known Challenges

### 9.1 Overfitting on Limited Data

With approximately 14,000 images combined across CASIA v1.0 and v2.0, and a model capable of learning millions of parameters, overfitting is the primary risk. The combination of Dropout, data augmentation, and EarlyStopping is designed to mitigate this, but careful monitoring of validation curves is essential.

### 9.2 Sensitivity to ELA Preprocessing Parameters

If ELA is used as the input transformation, the quality parameter (typically 90%) and the enhancement factor (typically 10×) can significantly affect what patterns the model learns. Inconsistent preprocessing between training and inference will degrade model performance.

### 9.3 Learning Rate Sensitivity

Binary classification with imbalanced data and sigmoid output can be sensitive to the initial learning rate. If the learning rate is too high, the network may converge to predicting one class exclusively. The `ReduceLROnPlateau` callback provides a safeguard, but initial rate selection matters.

### 9.4 Training-Inference Preprocessing Mismatch

The model must receive **identically preprocessed** images during both training and inference. Any difference in normalization, resizing interpolation method, or color channel ordering will cause unpredictable prediction behavior.

### 9.5 CASIA Dataset Bias

Both CASIA v1.0 and v2.0 contain specific types of manipulation (splicing, copy-move, removal) with specific characteristics. The trained model may not generalize to manipulation techniques not represented in this dataset (e.g., GAN-generated images, deepfakes, adversarially perturbed images).

---

*Document Version: 1.0 | Model: Custom CNN | Project: Image Manipulation Detection System*
