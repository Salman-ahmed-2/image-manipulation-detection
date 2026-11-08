# [ISSUE #5] Dataset Ingestion, Integrity Audit & Label Mapping Automation

## 📌 Issue Metadata
- **Milestone:** M1 — Data Pipeline & Forensics
- **Phase:** Phase 3 (Dataset Engineering)
- **Estimated Effort:** 4–5 hours
- **Labels:** `dataset`, `casia`, `metadata`, `pandas`
- **Dependencies:** Issue #1 (`config.py`), Issue #2 (`src/utils/`)
- **Blocks:** Issue #6 (Group-Aware Splitting), Issue #7 (CNN Training)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a Data Engineer and ML Researcher.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/dataset/DATASET_OVERVIEW.md`
> 2. `docs/dataset/CASIA_V1_DOCUMENTATION.md`
> 3. `docs/dataset/CASIA_V2_DOCUMENTATION.md`
> 4. `docs/dataset/LABEL_MAPPING.md`
> 5. `docs/dataset/DATA_QUALITY.md`
> 6. `AGENTS.md` (Strict rules: `data/raw/` is READ-ONLY, labels derived from filename prefixes only, no inventing file counts or labels).

---

## 🎯 Objective & Context
Implement dataset scanning, integrity verification, and label extraction logic for CASIA v1.0 and CASIA v2.0. Scan images in `data/raw/`, detect and isolate corrupted files, parse authentic vs. tampered labels directly from filename prefixes, and export the comprehensive catalog to `data/metadata/dataset_inventory.csv` and `data/metadata/dataset_labels.csv`.

---

## 📋 Technical Requirements

### 1. Dataset Validator & Scanner (`src/data/dataset_validator.py`)
- `scan_dataset_directory(raw_dir: Path) -> List[Dict[str, Any]]`:
  - Recursively locate all images with extensions `.jpg`, `.jpeg`, `.png`, `.tif`.
  - For each image, verify file readability via `PIL.Image.open().verify()`.
  - Catch corrupted images; record failure details in `corrupt_files.log` without crashing.
  - Extract image dimensions (width, height), colorspace mode, byte size, and format.

### 2. Label Extractor (`src/data/dataset_loader.py`)
- `extract_label_from_filename(filename: str) -> Dict[str, Any]`:
  - Follow verified CASIA rules:
    - Starts with `Au_` $\rightarrow$ `label = 0` ("Authentic"), manipulation = "Pristine".
    - Starts with `Tp_S_` $\rightarrow$ `label = 1` ("Manipulated"), manipulation = "Copy-Move".
    - Starts with `Tp_D_` or `Sp_` $\rightarrow$ `label = 1` ("Manipulated"), manipulation = "Splicing".
    - Starts with general `Tp_` $\rightarrow$ `label = 1` ("Manipulated"), manipulation = "General".
  - Extract base donor identifier (e.g. `nat10129`) to establish group identity.

### 3. Dataset Ingestion Script (`scripts/prepare_dataset.py` - Part 1)
- Write CLI utility that executes:
  1. Ingestion of `data/raw/casia_v1/` and `data/raw/casia_v2/`.
  2. Generation of `data/metadata/dataset_inventory.csv` with columns:
     `image_id`, `filepath`, `filename`, `dataset_version`, `format`, `width`, `height`, `channels`, `filesize_bytes`, `is_valid`.
  3. Generation of `data/metadata/dataset_labels.csv` with columns:
     `image_id`, `filename`, `label`, `label_name`, `manipulation_type`, `group_id`, `dataset_version`.

### 4. Unit Tests (`tests/test_dataset.py` - Part 1)
- Test label extraction across synthetic filenames:
  - `Au_ani_0001.jpg` $\rightarrow$ Label 0, Authentic
  - `Tp_S_CRN_M_N_nat10129_nat10129_00123.jpg` $\rightarrow$ Label 1, Copy-Move
  - `Tp_D_CRN_S_N_ani00073_ani00068_00192.jpg` $\rightarrow$ Label 1, Splicing
- Test invalid prefix logs a warning and raises `ValueError`.

---

## 📂 Target Files
- `src/data/dataset_validator.py`
- `src/data/dataset_loader.py`
- `scripts/prepare_dataset.py`
- `tests/test_dataset.py`

---

## 🧪 Verification & Testing
```bash
pytest tests/test_dataset.py -v
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] Filename parser accurately maps all CASIA v1 and v2 prefix conventions.
- [ ] Corrupt image handling logs bad files without aborting the batch pipeline.
- [ ] `data/raw/` is never modified or written to.
- [ ] `pytest tests/test_dataset.py` passes 100%.
