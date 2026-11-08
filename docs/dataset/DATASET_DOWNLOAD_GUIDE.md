# Dataset Download Guide — Image Manipulation Detection System

> [!IMPORTANT]
> The original CASIA images are **not** distributed through the GitHub ground-truth repositories. The images must be obtained from the official source or community mirrors. This guide walks through every step of the process.

---

## 1. Prerequisites

Before beginning, ensure you have the following tools and resources:

| Requirement | Notes |
|-------------|-------|
| **Git** | `git --version` to verify |
| **Python 3.8+** | Required for Kaggle CLI and verification scripts |
| **pip** | For installing `kaggle` and `datasets` packages |
| **~5 GB free disk space** | CASIA v2.0 is ~4 GB; v1.0 is ~300 MB |
| **Internet connection** | Required for all downloads |
| **Kaggle account** | Free; required for Kaggle downloads |
| **HuggingFace account** | Free; required for HuggingFace datasets |

### Install Dependencies

```bash
# Kaggle CLI (for Kaggle downloads)
pip install kaggle

# HuggingFace datasets (for HuggingFace downloads)
pip install datasets

# Image processing for verification
pip install Pillow
```

### Configure Kaggle Credentials

```bash
# 1. Go to https://www.kaggle.com/settings → API → Create New Token
# 2. Download kaggle.json
# 3. Place it in the correct location:
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

---

## 2. Downloading CASIA v2.0

CASIA v2.0 is the primary training dataset. Download it first.

### Step 1 — Check the Official Source

1. Open a browser and navigate to: `http://forensics.idealtest.org/casiav2/`
2. Create an account if prompted (free academic registration).
3. If the site loads correctly, download the full CASIA v2.0 archive.
4. Extract to your project directory:

```bash
mkdir -p data/raw/casia_v2
# Example extraction (adjust archive name as downloaded):
unzip CASIA_v2.zip -d data/raw/casia_v2/
# or
tar -xzf CASIA_v2.tar.gz -C data/raw/casia_v2/
```

> [!WARNING]
> `forensics.idealtest.org` has experienced extended periods of unavailability. If the site does not load within 30 seconds, proceed to Step 2.

---

### Step 2 — If Unavailable: Search Kaggle

Kaggle hosts several community-uploaded mirrors of CASIA v2.0.

```bash
# Search for available datasets on Kaggle:
kaggle datasets list -s "CASIA 2.0 image tampering"

# Common dataset slugs (verify before use):
# - divg07/casia-dataset
# - sophatvathana/casia-dataset
# - username/casia-2-image-tampering-detection

# Download (replace <owner>/<slug> with actual values):
kaggle datasets download -d <owner>/<slug> -p data/raw/casia_v2/ --unzip
```

Alternatively, download via the Kaggle web interface:
1. Go to [kaggle.com/datasets](https://www.kaggle.com/datasets).
2. Search: `CASIA 2.0 image tampering detection`.
3. Click the dataset → **Download** button.
4. Extract to `data/raw/casia_v2/`.

---

### Step 3 — Alternative: HuggingFace (Tampered Subset)

The HuggingFace dataset `KhangTruong/Casia-v2.0-Fake` contains the tampered images subset.

```python
# download_hf_casia2.py
from datasets import load_dataset
import os, shutil
from PIL import Image

SAVE_DIR = "data/raw/casia_v2/tampered"
os.makedirs(SAVE_DIR, exist_ok=True)

ds = load_dataset("KhangTruong/Casia-v2.0-Fake", split="train")

for i, example in enumerate(ds):
    img: Image.Image = example["image"]
    filename = example.get("filename", f"img_{i:05d}.jpg")
    save_path = os.path.join(SAVE_DIR, filename)
    img.save(save_path, "JPEG")

print(f"Saved {i+1} tampered images to {SAVE_DIR}")
```

```bash
python download_hf_casia2.py
```

> [!NOTE]
> This HuggingFace source provides **tampered images only**. You must obtain the 7,491 authentic images separately via Kaggle or the official source.

---

### Step 4 — Download Ground-Truth Masks from namtpham GitHub

Regardless of where you obtained the images, the ground-truth masks come from:

```bash
# Clone the ground-truth repository
git clone https://github.com/namtpham/casia2groundtruth.git

# Create the masks directory
mkdir -p data/raw/casia_v2/masks

# Copy masks into the project data directory
cp -r casia2groundtruth/CASIA2.0_Groundtruth/* data/raw/casia_v2/masks/

# (Optional) Review correction logs
ls casia2groundtruth/

# (Optional) Apply corrections to rename mislabelled images
# Follow the README in casia2groundtruth/ for detailed correction steps
```

---

## 3. Downloading CASIA v1.0

CASIA v1.0 is the secondary evaluation dataset.

### Step 1 — Check the Official Source

```
http://forensics.idealtest.org/casiav1/
```

1. Open the URL in a browser.
2. Register if required.
3. If available, download and extract:

```bash
mkdir -p data/raw/casia_v1
unzip CASIA_v1.zip -d data/raw/casia_v1/
```

> [!WARNING]
> Same availability caveat as v2.0 — the official site may be offline. Use Kaggle fallback if needed.

---

### Step 2 — Fallback: Search Kaggle

```bash
# Search Kaggle
kaggle datasets list -s "CASIA 1.0 image forgery detection"

# Download (replace with actual slug):
kaggle datasets download -d <owner>/<slug> -p data/raw/casia_v1/ --unzip
```

Web search terms: `"CASIA 1.0" image forgery detection kaggle`

---

### Step 3 — Download Masks from namtpham GitHub

```bash
# Clone the v1 ground-truth repository
git clone https://github.com/namtpham/casia1groundtruth.git

# Create masks directory
mkdir -p data/raw/casia_v1/masks

# Copy masks
cp -r casia1groundtruth/CASIA1.0groundtruth/* data/raw/casia_v1/masks/
```

---

## 4. Directory Setup

After downloading, organise files into the expected directory structure. Run the following commands from the project root:

```bash
# Create the full directory structure
mkdir -p data/raw/casia_v1/authentic
mkdir -p data/raw/casia_v1/tampered
mkdir -p data/raw/casia_v1/masks

mkdir -p data/raw/casia_v2/authentic
mkdir -p data/raw/casia_v2/tampered
mkdir -p data/raw/casia_v2/masks

mkdir -p data/processed/train
mkdir -p data/processed/val
mkdir -p data/processed/test

mkdir -p data/metadata
```

Move downloaded images into the correct subdirectories:

```bash
# CASIA v1.0 — separate by prefix
find data/raw/casia_v1/ -maxdepth 2 -name "Au_*.jpg" \
    -exec mv {} data/raw/casia_v1/authentic/ \;

find data/raw/casia_v1/ -maxdepth 2 -name "Tp_*.jpg" \
    -exec mv {} data/raw/casia_v1/tampered/ \;

# CASIA v2.0 — separate by prefix
find data/raw/casia_v2/ -maxdepth 2 -name "Au_*.jpg" \
    -exec mv {} data/raw/casia_v2/authentic/ \;

find data/raw/casia_v2/ -maxdepth 2 -name "Tp_*.jpg" \
    -exec mv {} data/raw/casia_v2/tampered/ \;
```

---

## 5. Verifying Downloads

### Image Count Verification

```bash
echo "=== CASIA v1.0 ==="
echo "Authentic: $(find data/raw/casia_v1/authentic/ -name 'Au_*.jpg' | wc -l)  (expected: 800)"
echo "Tampered:  $(find data/raw/casia_v1/tampered/  -name 'Tp_*.jpg' | wc -l)  (expected: 921)"
echo "Masks:     $(find data/raw/casia_v1/masks/     -name '*.png'    | wc -l)  (expected: 921)"

echo ""
echo "=== CASIA v2.0 ==="
echo "Authentic: $(find data/raw/casia_v2/authentic/ -name 'Au_*.jpg' | wc -l)  (expected: 7491)"
echo "Tampered:  $(find data/raw/casia_v2/tampered/  -name 'Tp_*.jpg' | wc -l)  (expected: 5123)"
echo "Masks:     $(find data/raw/casia_v2/masks/     -name '*.png'    | wc -l)  (expected: 5123)"
```

### Format and Integrity Check

```python
# verify_downloads.py
import os
from PIL import Image
from pathlib import Path

def verify_images(directory: str, expected_count: int, label: str):
    paths = list(Path(directory).rglob("*.jpg")) + \
            list(Path(directory).rglob("*.png"))
    corrupt = []
    for p in paths:
        try:
            with Image.open(p) as img:
                img.verify()
        except Exception as e:
            corrupt.append((str(p), str(e)))

    print(f"\n[{label}]")
    print(f"  Found:    {len(paths):,}  (expected: {expected_count:,})")
    print(f"  Corrupt:  {len(corrupt)}")
    if corrupt:
        for path, err in corrupt[:5]:
            print(f"    - {path}: {err}")

verify_images("data/raw/casia_v1/authentic", 800,  "CASIA v1 Authentic")
verify_images("data/raw/casia_v1/tampered",  921,  "CASIA v1 Tampered")
verify_images("data/raw/casia_v2/authentic", 7491, "CASIA v2 Authentic")
verify_images("data/raw/casia_v2/tampered",  5123, "CASIA v2 Tampered")
```

```bash
python verify_downloads.py
```

---

## 6. Dealing with Missing Files

If some images are unavailable after trying all sources:

| Situation | Action |
|-----------|--------|
| A few images missing (< 1 %) | Proceed; note missing count in experiment logs |
| Many images missing (> 5 %) | Try another Kaggle mirror; re-check the HuggingFace dataset |
| Authentic images missing but tampered available | Obtain authentic separately — do NOT mix partial downloads |
| Masks missing for specific tampered images | Mark those images as `has_mask = False` in `dataset_labels.csv`; exclude from segmentation evaluation but keep for classification |

```python
# find_missing_masks.py
import os
from pathlib import Path

TAMPERED_DIR = "data/raw/casia_v2/tampered"
MASKS_DIR    = "data/raw/casia_v2/masks"

missing = []
for img_path in Path(TAMPERED_DIR).rglob("*.jpg"):
    mask_name = img_path.stem + ".png"
    mask_path = Path(MASKS_DIR) / mask_name
    if not mask_path.exists():
        missing.append(img_path.name)

print(f"Tampered images without masks: {len(missing)}")
for m in missing[:20]:
    print(f"  {m}")
```

---

## 7. Mask-to-Image Matching Verification

After downloading both images and masks, verify that every tampered image has a corresponding mask:

```python
# verify_mask_matching.py
from pathlib import Path

def verify_matching(tampered_dir: str, mask_dir: str, dataset_label: str):
    tampered_stems = {p.stem for p in Path(tampered_dir).rglob("*.jpg")}
    mask_stems     = {p.stem for p in Path(mask_dir).rglob("*.png")}

    missing_masks  = tampered_stems - mask_stems
    orphan_masks   = mask_stems - tampered_stems

    print(f"\n[{dataset_label}]")
    print(f"  Tampered images:         {len(tampered_stems):,}")
    print(f"  Masks:                   {len(mask_stems):,}")
    print(f"  Missing masks:           {len(missing_masks)}")
    print(f"  Orphaned masks (no img): {len(orphan_masks)}")

    if missing_masks:
        print("  First 5 missing mask images:")
        for name in list(missing_masks)[:5]:
            print(f"    {name}.jpg")

verify_matching(
    "data/raw/casia_v1/tampered",
    "data/raw/casia_v1/masks",
    "CASIA v1.0"
)
verify_matching(
    "data/raw/casia_v2/tampered",
    "data/raw/casia_v2/masks",
    "CASIA v2.0"
)
```

```bash
python verify_mask_matching.py
```

A fully matched dataset will report **0 missing masks** and **0 orphaned masks**.

---

*Last updated: November 2026 | Project: Image Manipulation Detection System Using Deep Learning*
