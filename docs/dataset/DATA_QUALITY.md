# Dataset Quality Assurance & Anomaly Handling

## 1. Quality Control Objectives
The CASIA benchmark collections, while foundational in academic forensics, were compiled in the late 2000s and contain known format defects, labeling quirks, and dimensional variance. The dataset quality pipeline enforces systematic screening before images enter model training routines.

---

## 2. Quality Dimensions & Screening Rules

| Anomaly Category | Defect Description | Detection Method | Mitigation Protocol |
| :--- | :--- | :--- | :--- |
| **Corrupted Images** | Incomplete byte streams, missing EOF markers | `PIL.Image.open().verify()` | Move file to `corrupted/` log; exclude from training inventory |
| **Color Cast Discrepancies** | Grayscale (1-channel) or CMYK images | Inspect `img.mode` | Convert L and CMYK to standard 3-channel RGB: `img.convert('RGB')` |
| **Alpha Transparency** | RGBA PNG images with transparent backgrounds | Check `img.mode == 'RGBA'` | Composite over solid white canvas: `Image.alpha_composite` |
| **Extreme Aspect Ratios** | Images with aspect ratios $> 4:1$ | Calculate $W / H$ | Log dimension warning; pad to square prior to resizing |
| **Exact Duplicate Files** | Repeated files under different names | MD5 / SHA-256 binary hash | Retain first occurrence; remove duplicate references in inventory |
| **Near-Duplicate Crops** | Unaltered crops of the same scene | Perceptual Hashing (pHash) | Group under same `group_id` to prevent split leakage |
| **Mislabeled CASIA Tags**| Known misclassification in CASIA v2 naming | Reference `namtpham` correction log | Apply filename reconciliation map to correct `Tp_S` vs `Tp_D` |

---

## 3. Class Imbalance Mitigation
In CASIA v2.0:
- Authentic images: ~7,491 (59.4%)
- Manipulated images: ~5,123 (40.6%)

While this imbalance is moderate, training without weighting can bias predictions toward predicting Authentic. The training pipeline compensates using **balanced class weighting**:

$$W_c = \frac{N_{\text{total}}}{2 \times N_c}$$

For CASIA v2:
- $W_0 (\text{Authentic}) \approx \frac{12614}{2 \times 7491} \approx 0.84$
- $W_1 (\text{Manipulated}) \approx \frac{12614}{2 \times 5123} \approx 1.23$
