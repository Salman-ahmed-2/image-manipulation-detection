# [ISSUE #6] Group-Aware Dataset Splitting to Prevent Data Leakage

## 📌 Issue Metadata
- **Milestone:** M1 — Data Pipeline & Forensics
- **Phase:** Phase 3 (Dataset Engineering)
- **Estimated Effort:** 3–4 hours
- **Labels:** `dataset`, `data-splitting`, `leakage-prevention`, `scikit-learn`
- **Dependencies:** Issue #5 (`src/data/`, `data/metadata/`)
- **Blocks:** Issue #7 (Custom CNN), Issue #8 (MobileNetV2)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as an ML Research Engineer.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/dataset/DATA_SPLITTING.md`
> 2. `docs/decisions/ADR-002-DATASET-SELECTION.md`
> 3. `AGENTS.md` (Strict rules: Test set must be completely isolated, GroupShuffleSplit required, authentic donor and its manipulated offspring must stay in the same split).

---

## 🎯 Objective & Context
Implement group-aware dataset partitioning in `src/data/dataset_splitter.py` and integrate it into `scripts/prepare_dataset.py`. Standard random splitting causes severe data leakage in image forensics because tampered images share textures with their authentic donor images. The split must partition **groups** (based on donor image ID) using a 70% Train / 15% Validation / 15% Test distribution, exporting `data/metadata/dataset_split.csv`.

---

## 📋 Technical Requirements

### 1. `DatasetSplitter` (`src/data/dataset_splitter.py`)
- Implement `class DatasetSplitter`:
  ```python
  class DatasetSplitter:
      def __init__(
          self,
          train_ratio: float = 0.70,
          val_ratio: float = 0.15,
          test_ratio: float = 0.15,
          random_state: int = 42
      ):
          ...
          
      def split_dataframe(self, df: pd.DataFrame, group_col: str = "group_id") -> pd.DataFrame:
          """Execute two-stage GroupShuffleSplit ensuring zero cross-split leakage.
          
          Stage 1: 70% Train groups, 30% Temp groups.
          Stage 2: Split 30% Temp into 50% Val groups (15% total) and 50% Test groups (15% total).
          
          Returns:
              DataFrame with an added 'split' column ('train', 'validation', 'test').
          """
  ```
- **Integrity Assertion:** Implement `verify_no_leakage(split_df: pd.DataFrame, group_col: str = "group_id") -> bool` that asserts:
  $$\text{groups}(\text{train}) \cap \text{groups}(\text{val}) = \emptyset$$
  $$\text{groups}(\text{train}) \cap \text{groups}(\text{test}) = \emptyset$$
  $$\text{groups}(\text{val}) \cap \text{groups}(\text{test}) = \emptyset$$
  Raise `AssertionError` if any group ID spans multiple splits.

### 2. Integration into `scripts/prepare_dataset.py`
- Ingest `data/metadata/dataset_labels.csv`.
- Apply `DatasetSplitter`.
- Output `data/metadata/dataset_split.csv` containing:
  `image_id`, `filename`, `label`, `label_name`, `group_id`, `split`, `dataset_version`.
- Log split breakdown summary (Total samples, Authentic count, Manipulated count per split).

### 3. Unit Tests (`tests/test_dataset.py` - Part 2)
- Construct a synthetic pandas DataFrame with 10 groups, each containing 1 authentic and 2 tampered derivatives.
- Run `split_dataframe()`.
- Assert no `group_id` appears in more than one split partition.
- Verify approximately 70% / 15% / 15% sample proportions.

---

## 📂 Target Files
- `src/data/dataset_splitter.py`
- `scripts/prepare_dataset.py` (enhanced)
- `tests/test_dataset.py` (enhanced)

---

## 🧪 Verification & Testing
```bash
pytest tests/test_dataset.py -k "test_split" -v
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] GroupShuffleSplit guarantees complete donor-offspring group isolation.
- [ ] `verify_no_leakage()` passes with zero intersection between train, val, and test groups.
- [ ] Output CSV `data/metadata/dataset_split.csv` is correctly populated.
- [ ] All unit tests in `tests/test_dataset.py` pass.
