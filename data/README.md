# Data Directory Organization

This directory stores all raw dataset archives, ground-truth localization masks, preprocessed tensors, split partitions, and metadata catalogs.

## Directory Structure

```
data/
├── raw/                      # READ-ONLY source of truth (never modified by code)
│   ├── casia_v1/             # 1,721 raw CASIA v1.0 images
│   └── casia_v2/             # 12,614 raw CASIA v2.0 images
│
├── annotations/              # Ground-truth binary manipulation masks
│   ├── casia_v1/             # Masks from namtpham/casia1groundtruth
│   └── casia_v2/             # Masks from namtpham/casia2groundtruth
│
├── processed/                # Preprocessed images scaled to 224x224 RGB
│   ├── authentic/            # Standardized authentic images
│   └── manipulated/          # Standardized manipulated images
│
├── splits/                   # Partitioned subsets for training experiments
│   ├── train/                # 70% of groups (authentic & manipulated)
│   ├── validation/           # 15% of groups (authentic & manipulated)
│   └── test/                 # 15% of groups (ISOLATED for final evaluation)
│
└── metadata/                 # Authoritative CSV tracking files
    ├── dataset_inventory.csv # Inventory of all scanned files with dimensions & status
    ├── dataset_labels.csv    # Label mapping (0=Authentic, 1=Manipulated)
    └── dataset_split.csv     # Group-aware split assignments
```

## Storage & Access Policies
1. **`data/raw/` is Strictly Read-Only:** Scripts and pipelines must never alter, overwrite, or delete raw images.
2. **Version Control:** Raw and processed image binaries are excluded from Git via `.gitignore`. Only metadata CSVs under `data/metadata/` should be tracked.
3. **Download Instructions:** Refer to [`docs/dataset/DATASET_DOWNLOAD_GUIDE.md`](../docs/dataset/DATASET_DOWNLOAD_GUIDE.md) for step-by-step dataset acquisition instructions.
