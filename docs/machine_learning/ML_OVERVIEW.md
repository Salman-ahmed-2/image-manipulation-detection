# Machine Learning Approach Overview

## Table of Contents

1. [ML Approach Overview](#1-ml-approach-overview)
2. [Task Definition](#2-task-definition)
3. [Models Comparison](#3-models-comparison)
4. [Why Two Models](#4-why-two-models)
5. [Model Selection Criteria](#5-model-selection-criteria)
6. [Training Environment](#6-training-environment)
7. [Evaluation Strategy](#7-evaluation-strategy)
8. [Metrics Overview](#8-metrics-overview)
9. [Why Accuracy Alone is Insufficient](#9-why-accuracy-alone-is-insufficient)

---

## 1. ML Approach Overview

This project applies **supervised binary classification** using deep learning to detect image manipulation (image forgery). The system learns to distinguish between authentic (unaltered) images and manipulated (forged) images by training on labeled datasets.

### Learning Paradigm

| Property | Detail |
|---|---|
| Learning Type | Supervised Learning |
| Task Type | Binary Classification |
| Input Modality | RGB Images |
| Output | Class label (Authentic / Manipulated) + Confidence score |
| Supervision Signal | Ground-truth labels from CASIA v1.0 and CASIA v2.0 datasets |

The models are trained end-to-end on image data, learning to extract features that correlate with forensic artifacts such as:
- JPEG compression inconsistencies
- Pixel-level discontinuities at splice boundaries
- Texture and noise inconsistencies between regions
- Lighting and shadow inconsistencies

Error Level Analysis (ELA) is used as a **preprocessing step** to transform input images into a representation that highlights compression-level differences, making forensic artifacts more salient for the network.

---

## 2. Task Definition

### Formal Problem Statement

Given an input image **x** (RGB, 224×224×3), the model learns a function **f** such that:

```
f(x) → (ŷ, c)
```

Where:
- **ŷ ∈ {0, 1}** — predicted class label
  - `0` = **Authentic** (image has not been manipulated)
  - `1` = **Manipulated** (image has been tampered with — spliced, copy-moved, or removed)
- **c ∈ [0.0, 1.0]** — confidence score (sigmoid output probability)

### Decision Boundary

```
if sigmoid_output >= 0.5 → Manipulated (class 1)
if sigmoid_output <  0.5 → Authentic  (class 0)
```

The threshold of 0.5 is the default starting point. This threshold may be adjusted during evaluation to optimize for precision vs. recall trade-offs based on the application's requirements.

### Input Specification

| Property | Specification |
|---|---|
| Input Image Format | JPEG, PNG |
| Preprocessing | ELA transformation (optional / configurable) |
| Resize Target | 224 × 224 pixels |
| Color Mode | RGB (3 channels) |
| Pixel Value Range | [0.0, 1.0] (normalized) or model-specific range |

### Dataset Used

| Dataset | Images | Description |
|---|---|---|
| CASIA v1.0 | 1,721 images | Spliced and copy-moved forgeries at standard resolution |
| CASIA v2.0 | 12,614 images | Extended version with additional manipulation types and higher resolution |

> [!NOTE]
> Both datasets provide ground-truth binary labels (authentic / manipulated). The combined dataset is split into training, validation, and test sets. Test set labels are **never used** for model selection decisions.

---

## 3. Models Comparison

Two independent deep learning models are developed and evaluated in this project. The table below provides a side-by-side architectural and operational comparison.

| Aspect | Custom CNN | MobileNetV2 |
|---|---|---|
| **Approach** | Train from scratch | Transfer learning |
| **Base Architecture** | None (designed for this task) | ImageNet pretrained (1.28M images) |
| **Parameters** | ~[TBD — determined experimentally] | ~3.4M base + custom classification head |
| **Input Shape** | 224 × 224 × 3 | 224 × 224 × 3 |
| **Preprocessing** | Normalize to [0, 1] | `preprocess_input` → scale to [−1, 1] |
| **Training Time** | [PENDING — depends on hardware & dataset] | [PENDING — Phase 1 + Phase 2 fine-tuning] |
| **Inference Speed** | Fast | Fast (architecture optimized for mobile deployment) |
| **Interpretability** | Architecture fully controlled | Base layers are fixed/known; head is custom |
| **Data Requirement** | Higher (learning from scratch) | Lower (pre-trained feature extraction) |
| **Forensics-Specific Tuning** | Fully tunable from scratch | Limited to head + last ~30 base layers |
| **Model File Size** | [TBD] | ~14MB base + head |

---

## 4. Why Two Models

Developing two architecturally distinct models serves several important purposes for this research project:

### 4.1 Architectural Diversity Provides Comparison Baselines

A Custom CNN trained from scratch gives the team full control over every aspect of the architecture. This allows the network to potentially learn forensics-specific low-level features (e.g., JPEG block artifacts, noise patterns) without being biased by ImageNet priors.

MobileNetV2, on the other hand, leverages strong feature detectors already learned from 1.28 million diverse images. This provides a strong baseline and can demonstrate how well general-purpose visual features transfer to forensic tasks.

### 4.2 Demonstrates Transfer Learning vs. Scratch Training Trade-offs

| Concern | Custom CNN | MobileNetV2 |
|---|---|---|
| Works well with large data | ✅ Yes | ✅ Yes |
| Works well with small data | ⚠️ May overfit | ✅ Better generalization |
| Learns forensic features | ✅ From scratch | ⚠️ May not transfer perfectly |
| Training compute cost | Higher | Lower (Phase 1 converges fast) |

### 4.3 Practical Deployment Consideration

MobileNetV2 was designed for efficiency on mobile and embedded hardware. If the system is ever deployed on resource-constrained devices or in real-time applications, MobileNetV2's inference efficiency is an advantage.

### 4.4 Risk Mitigation

If one model fails to generalize well (e.g., overfits on training data), the alternative model provides a fallback. Having two models increases the probability of a deployable, well-performing system.

---

## 5. Model Selection Criteria

After both models are fully trained and evaluated, the **final production model** will be selected based on the following criteria, in priority order:

| Priority | Criterion | Rationale |
|---|---|---|
| 1 | **Recall (Sensitivity)** | Detecting all manipulated images is the primary goal; missing a fake is worse than a false alarm |
| 2 | **F1-Score** | Balances precision and recall; robust to class imbalance |
| 3 | **Validation Accuracy** | General measure of correctness |
| 4 | **Precision** | Avoid excessive false positives degrading user trust |
| 5 | **Inference Time** | Must be acceptable for web application use |
| 6 | **Model File Size** | Practical constraint for deployment |
| 7 | **AUC-ROC** | Measure of discriminative ability across all thresholds |

> [!IMPORTANT]
> Model selection decisions must use **validation set** metrics only. The test set is reserved exclusively for final reporting. Using test set results to guide model selection constitutes data leakage.

---

## 6. Training Environment

### Recommended Setup: Google Colab (GPU Runtime)

Google Colab provides free access to NVIDIA GPU instances (T4 or higher with Colab Pro), which significantly accelerates training for both CNN and MobileNetV2.

| Resource | Colab (Free) | Colab Pro | Local GPU |
|---|---|---|---|
| GPU | NVIDIA T4 (typical) | NVIDIA A100 / V100 | Depends on hardware |
| VRAM | ~15 GB | ~40 GB | Depends |
| RAM | ~12 GB | ~25 GB | Depends |
| Session Limit | ~12 hours | Longer | No limit |
| Storage | Google Drive (mount required) | Google Drive | Local filesystem |

### Local GPU Setup (Optional)

If a CUDA-capable GPU is available locally:
- **Framework**: TensorFlow 2.x with CUDA support
- **CUDA Version**: Compatible with installed TensorFlow version (see `tf.sysconfig.get_build_info()`)
- **cuDNN**: Required alongside CUDA

### CPU-Only Training

CPU-only training is **not recommended** for this project due to the size of CASIA v2.0 (12,614 images) and the depth of both models. Training times on CPU would be prohibitively long for iterative experimentation.

> [!TIP]
> When using Google Colab, mount Google Drive at the start of training to persist model checkpoints between sessions. Without Drive mounting, model files are lost when the session disconnects.

---

## 7. Evaluation Strategy

### Data Split Strategy

The dataset is divided into three non-overlapping subsets:

```
Full Dataset (CASIA v1.0 + v2.0)
         │
         ├── Training Set (~70%)     ← Used for gradient updates
         ├── Validation Set (~15%)   ← Used for hyperparameter tuning & model selection
         └── Test Set (~15%)         ← Used ONLY for final evaluation reporting
```

> [!CAUTION]
> The test set must **never** be used to make decisions during training or model selection. Any evaluation on the test set that influences training decisions invalidates the test results as an unbiased performance estimate.

### Validation Set Use

The validation set is used for:
- Monitoring overfitting (validation loss rising while training loss falls)
- Early stopping decisions
- Learning rate scheduling
- Checkpoint selection (save model at best validation loss/accuracy)
- Comparing hyperparameter configurations

### Test Set Use

The test set is used for:
- Final performance reporting after the best model is selected
- Generating the confusion matrix, precision, recall, F1, and AUC-ROC reported in the project

---

## 8. Metrics Overview

The following metrics are computed for each model during evaluation:

### 8.1 Accuracy

```
Accuracy = (TP + TN) / (TP + TN + FP + FN)
```

Overall percentage of correctly classified images. Easy to interpret but insufficient alone when classes are imbalanced.

### 8.2 Precision

```
Precision = TP / (TP + FP)
```

Of all images predicted as manipulated, what fraction actually were? Low precision means many authentic images are incorrectly flagged.

### 8.3 Recall (Sensitivity)

```
Recall = TP / (TP + FN)
```

Of all actually manipulated images, what fraction did the model catch? Low recall means the model misses real forgeries — the most dangerous error in this application.

### 8.4 F1-Score

```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

Harmonic mean of precision and recall. Useful single metric when both matter and class distribution is uneven.

### 8.5 Confusion Matrix

A 2×2 matrix showing the counts of TP, TN, FP, and FN:

|  | Predicted Authentic | Predicted Manipulated |
|---|---|---|
| **Actual Authentic** | TN | FP |
| **Actual Manipulated** | FN | TP |

### 8.6 AUC-ROC

The Area Under the Receiver Operating Characteristic curve measures the model's ability to discriminate between classes across all possible decision thresholds. A perfect classifier has AUC = 1.0; a random classifier has AUC = 0.5.

---

## 9. Why Accuracy Alone is Insufficient

### The Class Imbalance Problem

The CASIA datasets contain a mix of authentic and manipulated images, but the ratio is not guaranteed to be perfectly balanced. Consider a hypothetical scenario:

**Example**: If the test set contains 60% authentic images and 40% manipulated images:

| Strategy | Accuracy | Recall | F1 |
|---|---|---|---|
| Predict "always authentic" | 60% | **0%** | 0% |
| A random classifier | ~50% | ~50% | ~50% |
| A good model | High | High | High |

A naive model that always predicts "authentic" achieves 60% accuracy while **completely failing** to detect any manipulation. This makes accuracy a misleading metric in isolation.

### The Cost of False Negatives

In image forensics, the two types of errors have very different consequences:

| Error Type | Description | Consequence |
|---|---|---|
| **False Positive (FP)** | Authentic image flagged as manipulated | Inconvenience; user can re-verify |
| **False Negative (FN)** | Manipulated image classified as authentic | **Dangerous** — forgery goes undetected |

Because missing a manipulated image (FN) is significantly more harmful than raising a false alarm (FP), **Recall** is treated as the primary metric for this project, followed by F1-Score.

> [!WARNING]
> Never optimize a model solely for accuracy in a forensics or security application. Always examine the full confusion matrix and compute precision, recall, and F1-score before drawing conclusions about model quality.

---

*Document Version: 1.0 | Project: Image Manipulation Detection System | Framework: TensorFlow 2.x / Keras*
