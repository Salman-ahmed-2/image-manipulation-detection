# Machine Learning Model Verification & Testing (`tests/test_models.py`)

## 1. Testing Philosophy
Deep learning models cannot be tested with trivial deterministic assertions (e.g. `assert output == 1`). Instead, tests verify structural invariance, tensor dimensions, probability range boundaries, gradient propagation, and inference latency limits using **synthetic image tensors**.

> ⚠️ **TEST RULE:**
> Tests must never depend on the physical presence of the CASIA datasets on disk. All model tests construct synthetic NumPy/PIL tensors in memory.

---

## 2. Test Cases Overview

| Test Function | Target Module | Verified Invariant |
| :--- | :--- | :--- |
| `test_custom_cnn_input_shape()` | `src/models/cnn_model.py` | Model compiles and accepts `(None, 224, 224, 3)` |
| `test_custom_cnn_output_shape()` | `src/models/cnn_model.py` | Final layer outputs scalar shape `(None, 1)` with Sigmoid activation |
| `test_mobilenet_head_architecture()` | `src/models/mobilenet_model.py` | Classification head contains Dense 256, Dropout 0.4, Dense 128, Dense 1 |
| `test_mobilenet_frozen_layers()` | `src/models/mobilenet_model.py` | In Phase 1, base MobileNetV2 layers have `trainable == False` |
| `test_model_probability_bounds()` | `src/models/predictor.py` | Forward pass produces scalar $P \in [0.0, 1.0]$ |
| `test_inference_latency_cpu()` | `src/models/predictor.py` | CPU forward pass takes $< 300\text{ ms}$ for single sample |
| `test_model_loader_missing_weights()`| `src/models/model_loader.py` | Graceful fallback when weights file is absent |
