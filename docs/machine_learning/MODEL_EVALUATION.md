# Model Evaluation Methodology & Metric Formulation

## 1. Evaluation Protocol: Held-Out Test Isolation
To avoid optimistic evaluation bias:
1. **Hyperparameter Tuning & Checkpointing:** Driven exclusively by the **Validation Split** (15% of grouped images).
2. **Final Benchmark Evaluation:** Executed exactly **once** on the untouched **Test Split** (15% of grouped images) using `scripts/evaluate.py`.
3. Under no circumstances should test set predictions influence early stopping or learning rate adjustments.

---

## 2. Quantitative Metric Formulations

### 2.1 Confusion Matrix Layout

| Actual \ Predicted | Predicted Authentic (0) | Predicted Manipulated (1) |
| :--- | :---: | :---: |
| **Actual Authentic (0)** | **True Negative (TN)** | **False Positive (FP)** |
| **Actual Manipulated (1)** | **False Negative (FN)** | **True Positive (TP)** |

- **True Positive (TP):** Tampered image correctly identified as Manipulated.
- **True Negative (TN):** Pristine image correctly identified as Authentic.
- **False Positive (FP):** Pristine image falsely flagged as Manipulated (False Alarm).
- **False Negative (FN):** Tampered image missed by the system (Severe Forensic Risk).

### 2.2 Mathematical Formulations

- **Classification Accuracy:**
  $$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$
  *Limitation:* In the presence of class imbalance, accuracy alone is misleading.

- **Precision:**
  $$\text{Precision} = \frac{TP}{TP + FP}$$
  *Meaning:* When the system alerts that an image is manipulated, how likely is it actually tampered?

- **Recall (Sensitivity):**
  $$\text{Recall} = \frac{TP}{TP + FN}$$
  *Meaning:* What proportion of all actual manipulations did the detector catch? Minimizing False Negatives ($FN$) is paramount in forensics.

- **F1-Score (Harmonic Mean):**
  $$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = \frac{2TP}{2TP + FP + FN}$$

- **Area Under the ROC Curve (ROC-AUC):** Measures discrimination threshold independence across all classification cutoffs between $0.0$ and $1.0$.

---

## 3. Evaluation Script Interface (`scripts/evaluate.py`)
The evaluation script loads the saved model weights, evaluates on `data/splits/test/`, and outputs:
- Classification report (Accuracy, Precision, Recall, F1).
- Confusion matrix heatmap saved to `artifacts/plots/<model>_confusion_matrix.png`.
- ROC curve plot saved to `artifacts/plots/<model>_roc_curve.png`.
