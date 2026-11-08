# CASIA v1.0 — Complete Dataset Documentation

> [!NOTE]
> CASIA v1.0 is used as a **secondary / independent evaluation** dataset in this project. It is not used for primary model training. See [DATASET_OVERVIEW.md](DATASET_OVERVIEW.md) for the full project strategy.

---

## 1. Dataset Summary

| Property | Value |
|----------|-------|
| **Full Name** | CASIA Image Tampering Detection Evaluation Database v1.0 |
| **Short Name** | CASIA v1.0 / CASIA-ITDE v1 |
| **Releasing Organisation** | Institute of Automation, Chinese Academy of Sciences (CASIA) |
| **Year** | 2013 |
| **Total Images** | **1,721** |
| **Authentic Images** | **800** |
| **Tampered Images** | **921** |
| **Manipulation Type** | Image splicing (only) |
| **Image Format** | JPEG |
| **Resolution** | 384 × 256 pixels (uniform) |
| **Colour Space** | RGB |
| **Ground-Truth Masks** | Yes — binary PNG masks via `namtpham/casia1groundtruth` |
| **License** | Academic / research use only |

---

## 2. Origin and Publication

CASIA v1.0 was designed and released by the **National Laboratory of Pattern Recognition (NLPR)** at the **Institute of Automation, Chinese Academy of Sciences**, as part of the CASIA Image Tampering Detection Evaluation (ITDE) project.

The dataset was introduced in:

> Dong, J., Wang, W., & Tan, T. (2013). *CASIA Image Tampering Detection Evaluation Database*. IEEE China Summit and International Conference on Signal and Information Processing (ChinaSIP), 422–426.

**Primary intent:** Provide a standardised benchmark for evaluating image splicing detection algorithms. All tampered images in v1.0 were created by splicing region(s) from one source image into a target image, potentially with post-processing to reduce visual artifacts.

CASIA v1.0 was specifically designed with **uniform resolution (384 × 256 px)** to enable controlled experiments where image size is not a confounding variable.

---

## 3. Statistics

| Split | Count | Percentage |
|-------|-------|-----------|
| Authentic | 800 | 46.5 % |
| Tampered | 921 | 53.5 % |
| **Total** | **1,721** | **100 %** |

The dataset is approximately class-balanced, with slightly more tampered images than authentic.

---

## 4. Category Breakdown

Authentic images are organised into **8 semantic categories** with **100 images per category**.

| Category Code | Description | Image Count |
|--------------|-------------|-------------|
| `ani` | Animals | 100 |
| `arc` | Architecture | 100 |
| `art` | Art / Paintings | 100 |
| `cha` | Characters / People | 100 |
| `nat` | Nature | 100 |
| `pla` | Plants | 100 |
| `sec` | Scene / Setup | 100 |
| `txt` | Textures | 100 |
| **Total** | | **800** |

> [!NOTE]
> Tampered images (921 total) are created by splicing content across categories. No strict per-category breakdown is defined for the tampered subset in the original release.

---

## 5. Naming Convention

### Authentic Images

```
Au_[category]_[serial].jpg
```

| Part | Description | Example |
|------|-------------|---------|
| `Au` | Prefix indicating authentic image | `Au` |
| `[category]` | 3-letter semantic category code | `ani`, `arc`, `art`, `cha`, `nat`, `pla`, `sec`, `txt` |
| `[serial]` | Zero-padded 5-digit sequence number | `00001` |

**Examples:**
```
Au_ani_00001.jpg   → Authentic, animals,       index 1
Au_arc_00047.jpg   → Authentic, architecture,  index 47
Au_art_00013.jpg   → Authentic, art,            index 13
Au_cha_00088.jpg   → Authentic, people,         index 88
Au_nat_00005.jpg   → Authentic, nature,         index 5
Au_pla_00072.jpg   → Authentic, plants,         index 72
Au_sec_00031.jpg   → Authentic, scene/setup,    index 31
Au_txt_00099.jpg   → Authentic, textures,       index 99
```

### Tampered Images

```
Tp_[code]_[serial].jpg
```

| Part | Description |
|------|-------------|
| `Tp` | Prefix indicating tampered image |
| `[code]` | Encoded metadata about the forgery operation |
| `[serial]` | Sequence number |

**Examples:**
```
Tp_D_NNN_S_N_art00052_art00076_10289.jpg
Tp_D_NRN_M_N_nat00013_arc00001_00413.jpg
```

---

## 6. Ground-Truth Masks

Ground-truth binary segmentation masks for CASIA v1.0 are provided by the community repository:

**Repository:** [`namtpham/casia1groundtruth`](https://github.com/namtpham/casia1groundtruth)

### What This Repository Contains

| Artifact | Description |
|----------|-------------|
| Binary PNG masks | One mask per tampered image; same pixel dimensions as the source image |
| File organisation info | Mapping between tampered image filenames and their corresponding mask filenames |

### Mask Pixel Convention

| Pixel Value | Semantic Meaning |
|-------------|-----------------|
| White (255, 255, 255) | Manipulated / forged region |
| Black (0, 0, 0) | Authentic, unaltered background |

### Mask Filename Convention

Masks typically follow the same basename as the tampered image, stored in a separate directory:

```
data/
  casia_v1/
    tampered/
      Tp_D_NNN_S_N_art00052_art00076_10289.jpg
    masks/
      Tp_D_NNN_S_N_art00052_art00076_10289.png   ← corresponding mask
```

> [!IMPORTANT]
> Authentic images do **not** have masks, as they contain no manipulated regions. Only tampered images have associated masks.

---

## 7. Image Characteristics

| Property | Value |
|----------|-------|
| **Width** | 384 pixels |
| **Height** | 256 pixels |
| **Colour Space** | RGB (3 channels) |
| **Bit Depth** | 8 bits per channel (24-bit total) |
| **Format** | JPEG (.jpg) |
| **Compression** | Lossy JPEG (varies by quality setting) |
| **Aspect Ratio** | 3:2 |

The uniform resolution is a key characteristic of v1.0, making it straightforward to process without variable-size handling. When fed into deep learning models, images are resized to 224 × 224 px.

---

## 8. How to Download

> [!WARNING]
> `forensics.idealtest.org` has experienced extended downtime and may not be accessible. Follow the fallback steps if the primary source is unavailable.

### Step 1 — Try the Official Source

1. Open a browser and navigate to `http://forensics.idealtest.org/casiav1/`
2. Register for an account if required.
3. Download the CASIA v1.0 image archive (typically provided as a `.zip` or `.tar.gz` file).
4. Extract the archive.

### Step 2 — Fallback: Kaggle Community Uploads

1. Go to [https://www.kaggle.com/datasets](https://www.kaggle.com/datasets).
2. Search for: `CASIA 1.0 image forgery detection`.
3. Download the dataset (requires a free Kaggle account).
4. Extract to your local machine.

Alternatively, using the Kaggle CLI:
```bash
# Install Kaggle CLI
pip install kaggle

# Configure credentials (~/.kaggle/kaggle.json)
# Search for the dataset slug, then:
kaggle datasets download -d <dataset-owner>/<dataset-slug>
unzip <dataset-slug>.zip -d data/raw/casia_v1/
```

### Step 3 — Download Ground-Truth Masks

```bash
git clone https://github.com/namtpham/casia1groundtruth.git
# Copy or symlink the masks into your data directory:
cp -r casia1groundtruth/CASIA1.0groundtruth/ \
      data/raw/casia_v1/masks/
```

### Step 4 — Verify File Counts

```bash
# Count authentic images
find data/raw/casia_v1/authentic/ -name "Au_*.jpg" | wc -l
# Expected: 800

# Count tampered images
find data/raw/casia_v1/tampered/ -name "Tp_*.jpg" | wc -l
# Expected: 921

# Count masks
find data/raw/casia_v1/masks/ -name "*.png" | wc -l
# Expected: 921
```

---

## 9. File Organisation After Download

The recommended directory structure after downloading and organising CASIA v1.0:

```
data/
└── raw/
    └── casia_v1/
        ├── authentic/                  # 800 authentic images
        │   ├── Au_ani_00001.jpg
        │   ├── Au_ani_00002.jpg
        │   ├── ...
        │   ├── Au_arc_00001.jpg
        │   ├── ...
        │   └── Au_txt_00100.jpg
        ├── tampered/                   # 921 tampered images
        │   ├── Tp_D_NNN_S_N_art00052_art00076_10289.jpg
        │   ├── ...
        │   └── Tp_D_NRN_M_N_nat00013_arc00001_00413.jpg
        └── masks/                      # 921 binary masks (from namtpham/casia1groundtruth)
            ├── Tp_D_NNN_S_N_art00052_art00076_10289.png
            ├── ...
            └── Tp_D_NRN_M_N_nat00013_arc00001_00413.png
```

---

## 10. Identifying Authentic vs. Tampered Images

Classification is performed entirely based on filename prefix — no external metadata file is required:

| Filename Starts With | Label | Numeric Label |
|---------------------|-------|--------------|
| `Au_` | Authentic | `0` |
| `Tp_` | Manipulated | `1` |

**Python label extraction:**
```python
import os

def get_label_from_filename(filename: str) -> int:
    """
    Returns 0 for authentic images, 1 for tampered images.
    Works for CASIA v1.0 filenames.
    """
    basename = os.path.basename(filename)
    if basename.startswith("Au_"):
        return 0
    elif basename.startswith("Tp_"):
        return 1
    else:
        raise ValueError(f"Unrecognised filename prefix: {basename}")
```

---

## 11. Limitations of CASIA v1.0 for This Project

| Limitation | Detail | Impact |
|------------|--------|--------|
| **Small dataset** | Only 1,721 total images | Insufficient for primary training of deep models |
| **Splicing-only** | No copy-move manipulation present | Model trained on v2.0 may not generalise copy-move detection back to v1.0 |
| **Uniform resolution** | All images are 384 × 256 px | Does not reflect real-world resolution diversity |
| **Age** | Dataset created ~2013 | Does not reflect modern image editing tools (AI inpainting, diffusion-based edits) |
| **JPEG-only** | No PNG or RAW images | May bias model toward JPEG-specific artefact patterns |
| **Limited variety** | 8 fixed categories | Does not cover all image content types encountered in practice |

Despite these limitations, v1.0 remains valuable as an **independent evaluation set** because its distribution is different from v2.0, providing a meaningful measure of cross-dataset generalisation.

---

## 12. Citation / Attribution

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
Ground-truth masks for CASIA v1.0 were obtained from:
  namtpham/casia1groundtruth (GitHub)
  https://github.com/namtpham/casia1groundtruth
```

---

*Last updated: November 2026 | Project: Image Manipulation Detection System Using Deep Learning*
