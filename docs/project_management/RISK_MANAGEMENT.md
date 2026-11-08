# Risk Assessment & Contingency Management Matrix

## 1. Technical & Operational Risk Assessment

| Risk ID | Risk Description | Likelihood | Impact | Severity | Mitigation Strategy | Contingency Plan |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- |
| **RSK-01** | **CASIA Download Mirror Offline:** Original institutional server (`forensics.idealtest.org`) is unreachable | High | High | Critical | Obtain verified community mirrors from Kaggle or HuggingFace (`KhangTruong/Casia-v2.0-Fake`) | Ingest CASIA v1 first (smaller footprint) while mirror mirrors download |
| **RSK-02** | **Custom CNN Overfitting:** Model memorizes dataset artifacts instead of learning manipulation traces | Medium | High | High | Implement spatial dropout, L2 regularization, Minor rotation/flip augmentation | Fallback to pretrained MobileNetV2 with frozen base layers |
| **RSK-03** | **Compute / GPU Constraints:** Team laptops lack dedicated CUDA GPUs for training | High | Medium | Medium | Use Google Colab T4 GPU compute runtime for training runs | Train with reduced image resolution (160x160) or smaller batch sizes |
| **RSK-04** | **Data Leakage in Splits:** Spliced images leak donor textures across train/test splits | High | Critical | Critical | Enforce strict GroupShuffleSplit using extracted donor IDs | Audit split CSV files to ensure 100% group isolation before training |
| **RSK-05** | **Memory Exhaustion on Upload:** Maliciously crafted image bombs crash Flask process | Low | High | Medium | Set `Image.MAX_IMAGE_PIXELS = 50_000_000` and `MAX_CONTENT_LENGTH = 16MB` | Discard request at WSGI layer before reading into memory |
| **RSK-06** | **Misinterpretation of ELA:** Users treat bright ELA regions as judicial proof of forgery | High | High | High | Embed prominent legal/forensic disclaimer on all views and PDF reports | Provide educational tooltips explaining natural edge false positives |
