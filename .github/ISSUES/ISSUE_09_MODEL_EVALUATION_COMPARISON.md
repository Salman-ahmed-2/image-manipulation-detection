# [ISSUE #9] Model Evaluation, Comparison Metrics & Benchmark Reporting

## 📌 Issue Metadata
- **Milestone:** M3 — Transfer Learning & Comparison
- **Phase:** Phase 4 (Deep Learning Models)
- **Estimated Effort:** 4–5 hours
- **Labels:** `evaluation`, `metrics`, `visualization`, `benchmarks`
- **Dependencies:** Issue #7 (Custom CNN), Issue #8 (MobileNetV2)
- **Blocks:** Issue #10 (Production Model Selection)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as an ML Evaluation Specialist.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/machine_learning/MODEL_EVALUATION.md`
> 2. `docs/machine_learning/MODEL_COMPARISON.md`
> 3. `docs/reports/RESULTS_TEMPLATE.md`
> 4. `AGENTS.md` (Strict rules: Test set must be evaluated ONLY once, never fabricate benchmark numbers, save plots to `artifacts/plots/`).

---

## 🎯 Objective & Context
Implement model evaluation functions and visualization routines under `src/evaluation/` and a unified evaluation CLI script `scripts/evaluate.py`. Evaluate the trained Custom CNN and MobileNetV2 models on the held-out test split, compute quantitative metrics (Accuracy, Precision, Recall, F1-Score, ROC-AUC), render confusion matrices and ROC curves, and record empirical findings into `docs/reports/RESULTS_TEMPLATE.md`.

---

## 📋 Technical Requirements

### 1. Metrics Module (`src/evaluation/metrics.py`)
- Implement:
  - `compute_classification_metrics(y_true: np.ndarray, y_pred_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, float]`:
    - `accuracy`, `precision`, `recall`, `f1_score`, `roc_auc`, `specificity`.
  - `compute_confusion_matrix(y_true: np.ndarray, y_pred_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, int]`:
    - Returns dictionary with `tn`, `fp`, `fn`, `tp`.

### 2. Plotting Utilities (`src/evaluation/confusion_matrix.py` & `src/evaluation/visualization.py`)
- `plot_confusion_matrix(cm_dict: Dict[str, int], model_name: str, output_path: Path) -> Path`:
  - Uses Seaborn / Matplotlib to render a 2x2 confusion matrix heatmap with counts and percentages.
  - Saves figure to `artifacts/plots/<model_name>_confusion_matrix.png`.
- `plot_roc_curve(y_true: np.ndarray, y_pred_prob: np.ndarray, model_name: str, output_path: Path) -> Path`:
  - Computes False Positive Rate and True Positive Rate; plots ROC curve with AUC metric.
  - Saves figure to `artifacts/plots/<model_name>_roc_curve.png`.
- `plot_training_history(history_csv: Path, model_name: str) -> Path`:
  - Reads `CSVLogger` output and renders side-by-side Loss and Accuracy curves across training and validation epochs.

### 3. Evaluation CLI Script (`scripts/evaluate.py`)
- CLI script accepting `--model` (`cnn` or `mobilenet` or `both`) and `--split` (default `test`).
- Loads model from `artifacts/models/`.
- Streams test set batches from `data/splits/test/` (or via `dataset_split.csv`).
- Prints formatted evaluation report to stdout.
- Exports confusion matrix and ROC curve plots to `artifacts/plots/`.
- Appends benchmark results to `docs/reports/RESULTS_TEMPLATE.md`.

---

## 📂 Target Files
- `src/evaluation/metrics.py`
- `src/evaluation/confusion_matrix.py`
- `src/evaluation/visualization.py`
- `scripts/evaluate.py`

---

## 🧪 Verification & Testing
```bash
# Verify evaluation functions with synthetic ground truth
python3 -c "
import numpy as np
from src.evaluation.metrics import compute_classification_metrics
y_true = np.array([0, 0, 1, 1])
y_prob = np.array([0.1, 0.4, 0.8, 0.9])
res = compute_classification_metrics(y_true, y_prob)
assert res['accuracy'] == 1.0
print('Metrics verification passed:', res)
"
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] Precision, Recall, F1, Accuracy, and ROC-AUC calculations match standard definitions.
- [ ] Confusion matrix plots and ROC curves are generated and saved to `artifacts/plots/`.
- [ ] Held-out test set is evaluated in isolation without influencing model training.
- [ ] Script logs all results without hardcoded or fabricated numbers.
