# Dataset Overview — Image Manipulation Detection System

> [!IMPORTANT]
> This project uses two datasets: **CASIA v1.0** (secondary/evaluation) and **CASIA v2.0** (primary training). Both are for **academic use only**. The original images must be obtained from authorised sources; the GitHub ground-truth repositories listed below do **not** contain the raw images.

---

## 1. Overview

The CASIA Image Tampering Detection Evaluation Database (CASIA-ITDE) is the de-facto benchmark for image forgery detection research. Created by the Institute of Automation, Chinese Academy of Sciences, the database provides paired authentic/tampered images along with binary segmentation masks that identify manipulated regions.

### Why These Two Datasets?

| Criterion | Rationale |
|-----------|-----------|
| **Standard benchmark** | Both versions are widely used in peer-reviewed forensics literature, enabling fair comparison with published baselines. |
| **Ground-truth masks** | Pixel-level binary masks allow both binary classification (authentic vs. manipulated) and segmentation-based localisation training. |
| **Dual manipulation types** | CASIA v2.0 covers copy-move and splicing; v1.0 covers splicing only. Together they provide broad coverage. |
| **Scale** | Combined dataset of 14,335 images is sufficient for training a deep learning model without requiring proprietary data. |
| **Complementary roles** | v2.0 is large enough for primary training; v1.0 serves as an independent evaluation set, reducing overfitting to a single distribution. |

---

## 2. Dataset Summary Table

| Property | CASIA v1.0 | CASIA v2.0 |
|----------|-----------|-----------|
| **Total Images** | 1,721 | 12,614 |
| **Authentic** | 800 | 7,491 |
| **Tampered** | 921 | 5,123 |
| **Manipulation Type** | Splicing | Copy-move & Splicing |
| **Format** | JPEG | JPEG |
| **Resolution** | 384 × 256 px (uniform) | Various |
| **Authentic Categories** | 8 semantic categories | Multiple categories |
| **Ground-Truth Masks** | Yes (via GitHub repo) | Yes (via GitHub repo) |
| **Primary Role** | Secondary / Evaluation | Primary Training |

---

## 3. Dataset Purpose in This Project

```
CASIA v2.0  →  Primary training dataset
              Large, diverse, two manipulation types
              70 / 15 / 15 train-val-test split

CASIA v1.0  →  Secondary / independent evaluation
              Held out as a cross-distribution test
              Uniform resolution; splicing-only
```

### Rationale for this Split

- **CASIA v2.0** (12,614 images) provides sufficient volume for training deep neural networks (EfficientNet, ResNet-50, ViT, MobileNetV3).
- **CASIA v1.0** (1,721 images) is used as a held-out cross-dataset evaluation set to measure generalisation beyond the primary training distribution.
- Using v1.0 only for evaluation prevents any form of training contamination and gives a true out-of-distribution performance number.

---

## 4. GitHub Repository Analysis

> [!WARNING]
> Neither GitHub repository (`namtpham/casia2groundtruth` or `namtpham/casia1groundtruth`) contains the original raw images. They provide **masks, correction metadata, and download links only**.

### 4.1 `namtpham/casia2groundtruth`

**URL:** `https://github.com/namtpham/casia2groundtruth`

| Item Provided | Description |
|---------------|-------------|
| Binary segmentation masks | PNG masks for all 5,123 tampered images. White pixels = manipulated region; black pixels = authentic background. |
| Correction logs | CSV / Excel files listing images that were originally mislabelled (copy-move classified as splicing, and vice-versa). |
| Rename scripts | Python/shell scripts to rename files according to corrected labels. |
| Download links | Google Drive and OneDrive mirrors pointing to the original CASIA v2.0 image archive. |

**What it does NOT provide:**
- The 7,491 authentic images (`Au_*`)
- The 5,123 tampered images (`Tp_*`)
- Any model weights or preprocessing scripts

### 4.2 `namtpham/casia1groundtruth`

**URL:** `https://github.com/namtpham/casia1groundtruth`

| Item Provided | Description |
|---------------|-------------|
| Binary segmentation masks | PNG masks for all 921 tampered images. |
| File organisation info | Directory structure and filename mapping between masks and source images. |

**What it does NOT provide:**
- The 800 authentic images
- The 921 tampered images

### 4.3 What Must Be Obtained Separately

| Component | Source |
|-----------|--------|
| CASIA v1.0 raw images (authentic + tampered) | `forensics.idealtest.org` → Kaggle community uploads → HuggingFace |
| CASIA v2.0 raw images (authentic + tampered) | `forensics.idealtest.org` → Kaggle community uploads → HuggingFace (`KhangTruong/Casia-v2.0-Fake` for tampered subset) |

See [DATASET_DOWNLOAD_GUIDE.md](DATASET_DOWNLOAD_GUIDE.md) for step-by-step instructions.

---

## 5. Naming Convention Reference Table

| Prefix | Dataset | Class | Description |
|--------|---------|-------|-------------|
| `Au_[category]_[serial].jpg` | v1 & v2 | Authentic (0) | Unmodified original image |
| `Tp_[code]_[serial].jpg` | v1 | Manipulated (1) | Spliced tampered image |
| `Tp_D_[info]_[serial].jpg` | v2 | Manipulated — Splicing (1) | Different-source splice (`D` = different) |
| `Tp_S_[info]_[serial].jpg` | v2 | Manipulated — Copy-Move (1) | Same-source copy-move (`S` = same) |

### Examples

```
Au_ani_00001.jpg   → Authentic, animals category, index 00001
Au_arc_00047.jpg   → Authentic, architecture category, index 00047
Tp_D_CNN_M_B_nat00013_art00001_10289.jpg  → Tampered (splicing), v2
Tp_S_NNN_S_B_ani00001_ani00039_00291.jpg  → Tampered (copy-move), v2
```

---

## 6. Ground-Truth Mask Description

Ground-truth masks are binary PNG images that share the same dimensions as their corresponding tampered image.

| Pixel Value | Meaning |
|-------------|---------|
| **White (255, 255, 255)** | Manipulated / forged region |
| **Black (0, 0, 0)** | Authentic, unaltered background |

### Mask Usage in This Project

| Task | Mask Required? | Notes |
|------|----------------|-------|
| Binary classification (authentic vs. manipulated) | No | Label derived from filename prefix |
| Manipulation localisation / segmentation | Yes | Mask used as pixel-level annotation |
| Evaluation of segmentation head | Yes | IoU and pixel-accuracy against mask |
| Visualisation and explainability | Optional | GradCAM overlaid on tampered region |

---

## 7. Licensing and Attribution Requirements

> [!CAUTION]
> Both CASIA datasets are released for **academic and research use only**. Commercial use is strictly prohibited. Any publication using these datasets must cite the original authors.

### Required Citation (Dong et al.)

```bibtex
@inproceedings{dong2013casia,
  title     = {CASIA Image Tampering Detection Evaluation Database},
  author    = {Dong, Jing and Wang, Wei and Tan, Tieniu},
  booktitle = {IEEE China Summit and International Conference on Signal and
               Information Processing (ChinaSIP)},
  year      = {2013},
  pages     = {422--426},
  doi       = {10.1109/ChinaSIP.2013.6625374}
}
```

### Conditions of Use

1. Use only for non-commercial academic research.
2. Do not redistribute the original images publicly.
3. Cite Dong et al. (2013) in any publication or report.
4. Acknowledge the Institute of Automation, Chinese Academy of Sciences.
5. The ground-truth mask repositories (`namtpham/*`) must also be credited where applicable.

---

## 8. Known Issues

### 8.1 Mislabelling in CASIA v2.0

A known community-identified issue is that a subset of images in CASIA v2.0 have **incorrect manipulation type labels**:

- Some images with the `Tp_D_` (splicing) prefix were actually created using copy-move operations, and vice versa.
- The `namtpham/casia2groundtruth` repository provides **correction CSV/Excel logs** enumerating the affected files.
- Correction scripts are provided to rename or remap labels accordingly.

> [!NOTE]
> For binary classification (authentic vs. manipulated), these mislabellings do **not** affect the top-level label. They are only relevant if you use the manipulation sub-type (`copy-move` vs. `splicing`) as a secondary label.

### 8.2 Potential Post-Processing Artefacts

Some tampered images in both datasets may exhibit minor post-processing (blur, contrast adjustment) applied to mask the forgery. These artefacts are intentional and reflect real-world conditions.

### 8.3 Resolution Diversity (v2.0)

CASIA v2.0 images vary in resolution. All must be resized to a uniform dimension (224 × 224 px) during preprocessing. See [DATASET_PREPARATION.md](DATASET_PREPARATION.md).

---

## 9. Dataset Availability Status

> [!WARNING]
> `forensics.idealtest.org` has experienced extended downtime and may be unavailable. Always verify before attempting to download.

| Source | Dataset | Status | Notes |
|--------|---------|--------|-------|
| `forensics.idealtest.org` | v1 & v2 | ⚠️ May be offline | Official source; check first |
| Kaggle — community uploads | v1 & v2 | ✅ Generally available | Search "CASIA image forgery detection" |
| HuggingFace — `KhangTruong/Casia-v2.0-Fake` | v2 (tampered only) | ✅ Available | Tampered images subset; authentic needed separately |
| `namtpham/casia2groundtruth` (GitHub) | v2 masks + links | ✅ Available | Contains Google Drive / OneDrive links to full dataset |
| `namtpham/casia1groundtruth` (GitHub) | v1 masks | ✅ Available | Masks only |

See [DATASET_DOWNLOAD_GUIDE.md](DATASET_DOWNLOAD_GUIDE.md) for the complete step-by-step download procedure.

---

*Last updated: November 2026 | Project: Image Manipulation Detection System Using Deep Learning*
