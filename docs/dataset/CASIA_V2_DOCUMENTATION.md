# CASIA v2.0 — Complete Dataset Documentation

> [!IMPORTANT]
> CASIA v2.0 is the **primary training dataset** for this project. It is used for all model training and internal validation. See [DATASET_OVERVIEW.md](DATASET_OVERVIEW.md) for the full project strategy.

---

## 1. Dataset Summary

| Property | Value |
|----------|-------|
| **Full Name** | CASIA Image Tampering Detection Evaluation Database v2.0 |
| **Short Name** | CASIA v2.0 / CASIA-ITDE v2 |
| **Releasing Organisation** | Institute of Automation, Chinese Academy of Sciences (CASIA) |
| **Year** | 2013 (v2 release) |
| **Total Images** | **12,614** |
| **Authentic Images** | **7,491** |
| **Tampered Images** | **5,123** |
| — Copy-Move | ~3,295 (prefix `Tp_S_`) |
| — Splicing | ~1,828 (prefix `Tp_D_`) |
| **Manipulation Types** | Copy-move AND Image splicing |
| **Image Format** | JPEG |
| **Resolution** | Various (not uniform) |
| **Colour Space** | RGB |
| **Ground-Truth Masks** | Yes — binary PNG masks via `namtpham/casia2groundtruth` |
| **License** | Academic / research use only |

---

## 2. Origin and Publication

CASIA v2.0 is an extended and improved version of CASIA v1.0, created by the same team at the **National Laboratory of Pattern Recognition (NLPR), Institute of Automation, Chinese Academy of Sciences**.

Key improvements over v1.0:
- **Significantly larger**: 12,614 images vs. 1,721.
- **Two manipulation types**: both copy-move and splicing (v1.0 had splicing only).
- **Variable resolutions**: reflects more realistic imaging conditions.
- **More diverse content**: broader range of scenes, objects, and categories.

Introduced in:

> Dong, J., Wang, W., & Tan, T. (2013). *CASIA Image Tampering Detection Evaluation Database*. IEEE China Summit and International Conference on Signal and Information Processing (ChinaSIP), 422–426.

---

## 3. Statistics

| Category | Count | Percentage |
|----------|-------|-----------|
| Authentic | 7,491 | 59.4 % |
| Tampered — Copy-Move | ~3,295 | ~26.1 % |
| Tampered — Splicing | ~1,828 | ~14.5 % |
| **Tampered Total** | **5,123** | **40.6 %** |
| **Grand Total** | **12,614** | **100 %** |

> [!NOTE]
> The counts for copy-move (~3,295) and splicing (~1,828) are approximate. The exact counts depend on which correction version is applied from `namtpham/casia2groundtruth`, as some images were originally mislabelled. For binary classification purposes (authentic=0, manipulated=1), the precise sub-type counts do not affect training.

---

## 4. Manipulation Type Descriptions

### 4.1 Image Splicing

**Definition:** A region is copied from one source image and pasted into a completely different target image. The donor and recipient images are unrelated.

| Characteristic | Description |
|---------------|-------------|
| Naming prefix | `Tp_D_` (`D` = Different source image) |
| Donor source | A different image than the target |
| Common artefacts | Lighting inconsistency, boundary blur, noise level mismatch, JPEG re-compression artefacts |
| Detection cues | Noise pattern discontinuity, lighting angle mismatch, texture inconsistency |

**Example filename:** `Tp_D_CNN_M_B_nat00013_art00001_10289.jpg`

### 4.2 Copy-Move

**Definition:** A region is copied from one part of an image and pasted into a different location within the **same** image, typically to conceal or duplicate an object.

| Characteristic | Description |
|---------------|-------------|
| Naming prefix | `Tp_S_` (`S` = Same source image) |
| Donor source | The same image as the target |
| Common artefacts | Repeated texture blocks, correlated noise patterns, block-matching artefacts |
| Detection cues | Local similarity (keypoint matching), DCT coefficient patterns, PatchMatch |

**Example filename:** `Tp_S_NNN_S_B_ani00001_ani00039_00291.jpg`

---

## 5. Naming Convention

### 5.1 Authentic Images

```
Au_[category]_[serial].jpg
```

| Part | Description | Example Value |
|------|-------------|--------------|
| `Au` | Authentic prefix | `Au` |
| `[category]` | 3-letter semantic category | `ani`, `nat`, `arc`, … |
| `[serial]` | Zero-padded sequence number | `00001` |

**Examples:**
```
Au_ani_00001.jpg
Au_nat_00089.jpg
Au_arc_00042.jpg
```

### 5.2 Tampered — Splicing

```
Tp_D_[filter]_[size]_[blend]_[source1][id1]_[source2][id2]_[serial].jpg
```

| Part | Description |
|------|-------------|
| `Tp` | Tampered prefix |
| `D` | Different-source splice |
| `[filter]` | Post-processing filter applied (N=none, C=contrast, N=noise, R=rotation, etc.) |
| `[size]` | Size modifier (S=small, M=medium, L=large) |
| `[blend]` | Blending type (B=blurred edges, N=no blending) |
| `[source1][id1]` | Category and index of donor region |
| `[source2][id2]` | Category and index of target image |
| `[serial]` | Unique 5-digit identifier |

**Example:**
```
Tp_D_CNN_M_B_nat00013_art00001_10289.jpg
     ^^^  Filters: Contrast, Noise, Noise
          ^ Size: Medium
            ^ Blend: Blurred
              ^^^^^^^^ Donor: nat image 00013
                       ^^^^^^^^ Target: art image 00001
```

### 5.3 Tampered — Copy-Move

```
Tp_S_[filter]_[size]_[blend]_[source1][id1]_[source2][id2]_[serial].jpg
```

Same structure as splicing, but with `S` (Same-source) instead of `D`.

**Example:**
```
Tp_S_NNN_S_B_ani00001_ani00039_00291.jpg
```

---

## 6. Ground-Truth Masks

Ground-truth binary segmentation masks for CASIA v2.0 are provided by the community repository:

**Repository:** [`namtpham/casia2groundtruth`](https://github.com/namtpham/casia2groundtruth)

### What This Repository Contains

| Artifact | Description |
|----------|-------------|
| Binary PNG masks | One mask per tampered image; matching pixel dimensions |
| Correction logs | CSV / Excel files listing mislabelled images (copy-move ↔ splicing) |
| Rename scripts | Scripts to correct filenames based on correction logs |
| Download links | Google Drive and OneDrive mirrors for the full image dataset |

### Mask Pixel Convention

| Pixel Value | Semantic Meaning |
|-------------|-----------------|
| White (255, 255, 255) | Manipulated / forged region |
| Black (0, 0, 0) | Authentic, unaltered background |

### Mask-to-Image Matching

Masks share the same basename as their corresponding tampered image:

```
tampered/Tp_D_CNN_M_B_nat00013_art00001_10289.jpg
masks/   Tp_D_CNN_M_B_nat00013_art00001_10289.png  ← same basename, .png extension
```

Programmatic matching:
```python
import os

def get_mask_path(image_path: str, mask_dir: str) -> str:
    """Given a tampered image path, return the corresponding mask path."""
    basename = os.path.splitext(os.path.basename(image_path))[0]
    return os.path.join(mask_dir, basename + ".png")
```

---

## 7. Known Labelling Issues

> [!WARNING]
> A documented subset of images in the original CASIA v2.0 release has **incorrect manipulation-type labels**. Some copy-move images were released with the `Tp_D_` (splicing) prefix, and some splicing images with the `Tp_S_` (copy-move) prefix.

### Source of the Issue

This appears to have been a data-entry error during the original dataset compilation. The forgery operation performed does not always match the filename prefix encoding.

### How to Correct

The `namtpham/casia2groundtruth` repository provides:

1. **`correction.csv` / `correction.xlsx`** — A table listing each mislabelled image, its original filename, and its corrected filename.
2. **Rename scripts** — Shell or Python scripts that rename the files based on the correction log.

### Impact on This Project

| Use Case | Impact |
|----------|--------|
| Binary classification (authentic vs. manipulated) | **None** — top-level label is correct regardless of sub-type |
| Copy-move vs. splicing sub-classification | **High** — must apply correction logs before training |
| Segmentation (mask-to-image matching) | **None** — mask basenames match image basenames regardless of prefix |

> [!TIP]
> For this project's binary classification task, it is acceptable to use uncorrected files. If a copy-move vs. splicing classifier is added in the future, apply the correction logs from `namtpham/casia2groundtruth` first.

---

## 8. How to Download

> [!WARNING]
> `forensics.idealtest.org` has experienced extended downtime. Follow the fallback sources if unavailable.

### Step a — Try the Official Source

1. Navigate to `http://forensics.idealtest.org/casiav2/`
2. Register or log in if prompted.
3. Download the full CASIA v2.0 archive.
4. Extract to `data/raw/casia_v2/`.

### Step b — Kaggle Community Mirrors

1. Go to [https://www.kaggle.com/datasets](https://www.kaggle.com/datasets).
2. Search for: `CASIA 2.0 image tampering detection`.
3. Download the dataset (free Kaggle account required).

```bash
pip install kaggle
# Ensure ~/.kaggle/kaggle.json is configured
kaggle datasets download -d <owner>/<slug>
unzip <slug>.zip -d data/raw/casia_v2/
```

### Step c — HuggingFace (Tampered Subset Only)

The HuggingFace dataset `KhangTruong/Casia-v2.0-Fake` provides the **tampered images subset**.  
Authentic images must be sourced separately.

```python
from datasets import load_dataset

ds = load_dataset("KhangTruong/Casia-v2.0-Fake")
# Save images locally as needed
```

> [!NOTE]
> Since this HuggingFace dataset contains only tampered images, you must combine it with authentic images obtained from Kaggle or the official source.

### Step d — Ground-Truth Masks and Corrections (namtpham GitHub)

```bash
# Clone the ground-truth repository
git clone https://github.com/namtpham/casia2groundtruth.git

# (Optional) Apply correction scripts to fix mislabelled filenames
# Follow the README in the cloned repo for exact steps

# Copy masks to your data directory
cp -r casia2groundtruth/CASIA2.0_Groundtruth/ data/raw/casia_v2/masks/
```

---

## 9. File Organisation After Download

```
data/
└── raw/
    └── casia_v2/
        ├── authentic/                  # 7,491 authentic images
        │   ├── Au_ani_00001.jpg
        │   ├── Au_arc_00001.jpg
        │   └── ...
        ├── tampered/                   # 5,123 tampered images
        │   ├── splicing/               # ~1,828 images (Tp_D_ prefix)
        │   │   ├── Tp_D_CNN_M_B_nat00013_art00001_10289.jpg
        │   │   └── ...
        │   └── copy_move/             # ~3,295 images (Tp_S_ prefix)
        │       ├── Tp_S_NNN_S_B_ani00001_ani00039_00291.jpg
        │       └── ...
        └── masks/                      # 5,123 binary PNG masks
            ├── Tp_D_CNN_M_B_nat00013_art00001_10289.png
            ├── Tp_S_NNN_S_B_ani00001_ani00039_00291.png
            └── ...
```

> [!TIP]
> You may also keep all tampered images flat (without the `splicing/` and `copy_move/` subdirectories) if sub-type classification is not needed. The label derivation from filename prefix works regardless of directory structure.

---

## 10. Identifying Authentic vs. Tampered Images

| Filename Starts With | Label | Numeric Label | Manipulation Sub-type |
|---------------------|-------|--------------|----------------------|
| `Au_` | Authentic | `0` | None |
| `Tp_D_` | Manipulated | `1` | Splicing |
| `Tp_S_` | Manipulated | `1` | Copy-Move |

```python
def get_label_v2(filename: str) -> dict:
    """
    Returns label info for a CASIA v2.0 image filename.
    """
    import os
    bn = os.path.basename(filename)

    if bn.startswith("Au_"):
        return {"label": 0, "label_name": "authentic", "manipulation_type": "none"}
    elif bn.startswith("Tp_D_"):
        return {"label": 1, "label_name": "manipulated", "manipulation_type": "splicing"}
    elif bn.startswith("Tp_S_"):
        return {"label": 1, "label_name": "manipulated", "manipulation_type": "copy_move"}
    elif bn.startswith("Tp_"):
        return {"label": 1, "label_name": "manipulated", "manipulation_type": "unknown"}
    else:
        raise ValueError(f"Unrecognised filename prefix: {bn}")
```

---

## 11. Ground-Truth Mask Correspondence

Each tampered image has exactly one corresponding binary mask. The mask and image share the same basename with different extensions:

| Image file | Mask file |
|------------|----------|
| `Tp_D_CNN_M_B_nat00013_art00001_10289.jpg` | `Tp_D_CNN_M_B_nat00013_art00001_10289.png` |
| `Tp_S_NNN_S_B_ani00001_ani00039_00291.jpg` | `Tp_S_NNN_S_B_ani00001_ani00039_00291.png` |

### Verification

```bash
# Verify every tampered image has a corresponding mask
for img in data/raw/casia_v2/tampered/**/*.jpg; do
    base=$(basename "${img}" .jpg)
    mask="data/raw/casia_v2/masks/${base}.png"
    if [ ! -f "$mask" ]; then
        echo "MISSING MASK: $img"
    fi
done
```

Authentic images intentionally have **no mask** because they contain no manipulated regions.

---

## 12. Class Distribution Analysis

### Binary Distribution

| Class | Count | Percentage |
|-------|-------|-----------|
| Authentic (label = 0) | 7,491 | **59.4 %** |
| Manipulated (label = 1) | 5,123 | **40.6 %** |
| **Total** | **12,614** | **100 %** |

This represents a **moderate class imbalance** (~1.46:1 authentic-to-manipulated ratio).

### Manipulation Sub-type Distribution (within manipulated class)

| Sub-type | Count | % of Tampered | % of Total |
|----------|-------|--------------|-----------|
| Copy-Move | ~3,295 | ~64.3 % | ~26.1 % |
| Splicing | ~1,828 | ~35.7 % | ~14.5 % |

### Mitigation Strategies for Class Imbalance

| Strategy | Method | When to Use |
|----------|--------|-------------|
| **Class weights** | `weight = N_total / (2 × N_class)` | Recommended; built into most frameworks |
| **Oversampling** | Randomly duplicate manipulated samples | When dataset is small |
| **Data augmentation** | Apply augmentations more aggressively to minority class | Effective for image data |
| **Threshold tuning** | Adjust decision threshold from 0.5 to maximise F1 | Post-training calibration |

For this project, **class weights** are the primary mitigation strategy during training.

---

## 13. Citation / Attribution

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

Additionally acknowledge:

```
Ground-truth masks and correction logs for CASIA v2.0 were obtained from:
  namtpham/casia2groundtruth (GitHub)
  https://github.com/namtpham/casia2groundtruth
```

---

*Last updated: November 2026 | Project: Image Manipulation Detection System Using Deep Learning*
