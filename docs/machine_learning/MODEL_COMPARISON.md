# Model Comparison Framework: Custom CNN vs. MobileNetV2

## 1. Architectural & Theoretical Trade-Offs

| Evaluation Dimension | Custom CNN (from scratch) | MobileNetV2 (Transfer Learning) | Theoretical Expectation |
| :--- | :--- | :--- | :--- |
| **Weight Initialization** | Random Glorot / He normal | ImageNet-1k pre-trained weights | MobileNetV2 converges much faster with fewer required epochs |
| **Feature Focus** | Learns low-level forensic artifacts (noise, DCT edges) | High-level semantic features (objects, shapes) | Custom CNN may capture uncompressed sensor residuals better |
| **Parameter Count** | ~1.2M - 2.5M parameters | ~3.4M base + ~400k head | Custom CNN has a smaller weight footprint on disk |
| **Inference Latency** | Very low (~40ms CPU per image) | Low (~80ms CPU per image) | Both comfortably satisfy the < 5s end-to-end constraint |
| **Overfitting Risk** | Higher risk if training data is small | Mitigated by pre-trained feature regularization | MobileNetV2 expected to generalize better across diverse domains |

---

## 2. Experimental Benchmark Matrix (Template)

The table below will be filled directly from empirical test runs using `scripts/evaluate.py`:

| Evaluation Metric | Custom CNN | MobileNetV2 | Experimental Winner | Notes & Observations |
| :--- | :---: | :---: | :---: | :--- |
| **Test Accuracy** | *[PENDING]* | *[PENDING]* | *[PENDING]* | Measured on isolated 15% test split |
| **Test Precision** | *[PENDING]* | *[PENDING]* | *[PENDING]* | Evaluates false alarm rate |
| **Test Recall** | *[PENDING]* | *[PENDING]* | *[PENDING]* | Critical metric for manipulation catch rate |
| **Test F1-Score** | *[PENDING]* | *[PENDING]* | *[PENDING]* | Harmonic balance of Precision and Recall |
| **ROC-AUC** | *[PENDING]* | *[PENDING]* | *[PENDING]* | Threshold-independent discrimination |
| **Convergence Epochs**| *[PENDING]* | *[PENDING]* | *[PENDING]* | Epochs required to trigger EarlyStopping |
| **Model Size (.keras)**| *[PENDING]* | *[PENDING]* | *[PENDING]* | Weight file size in megabytes |
| **Inference Time (CPU)**| *[PENDING]* | *[PENDING]* | *[PENDING]* | Milliseconds per 224x224 sample |

---

## 3. Production Model Selection Protocol
The production default model in `config.py` (`Config.ACTIVE_MODEL`) will be selected using the following ranked criteria:
1. **Validation F1-Score:** Must achieve superior balance between Precision and Recall.
2. **Recall on Manipulated Class:** Priority given to minimizing missed tampers.
3. **Inference Latency:** Must maintain under 250ms forward-pass duration on CPU.
