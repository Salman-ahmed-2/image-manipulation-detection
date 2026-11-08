# Troubleshooting & Common Issues Guide

## 1. Environment & Dependency Issues

### Issue: `ImportError: libGL.so.1: cannot open shared object file`
- **Cause:** OpenCV (`opencv-python`) requires OpenGL system libraries that may be missing on headless Linux/Docker environments.
- **Resolution:**
  ```bash
  # Option A (Debian/Ubuntu system package):
  sudo apt-get update && sudo apt-get install -y libgl1-mesa-glx libglib2.0-0

  # Option B (Use headless PyPI package):
  pip uninstall opencv-python
  pip install opencv-python-headless
  ```

### Issue: TensorFlow Fails to Find Local GPU
- **Cause:** Missing or incompatible NVIDIA CUDA/cuDNN driver installation.
- **Diagnostic Command:**
  ```bash
  python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
  ```
- **Resolution:** If running locally without an NVIDIA GPU, TensorFlow defaults to CPU gracefully. For training, switch to Google Colab with a free T4 GPU runtime.

---

## 2. Image Processing & ELA Issues

### Issue: `PIL.UnidentifiedImageError: cannot identify image file`
- **Cause:** Uploaded file is either truncated, corrupted, or not a genuine image despite having a `.jpg` extension.
- **Resolution:** Ingest within a `try/except` block catching `(PIL.UnidentifiedImageError, OSError)`, log the anomaly, and return a clean `HTTP 400 Bad Request`.

### Issue: ELA Output for PNG Images is Almost Completely White / Bright
- **Cause:** PNG files are lossless. When recompressing to JPEG at quality 90, the initial quantization introduces an error floor across the entire canvas.
- **Resolution:** This is expected forensic behavior. Ensure the UI displays the disclaimer explaining that ELA on PNG inputs reflects format conversion artifacts.

---

## 3. Web & Runtime Issues

### Issue: `413 Request Entity Too Large`
- **Cause:** Uploaded image exceeds `Config.MAX_CONTENT_LENGTH` (16 MB).
- **Resolution:** Ensure the client-side JavaScript warns the user before uploading large raw files.

### Issue: `KeyError: 'image'` when calling `POST /analyze`
- **Cause:** HTML form missing `enctype="multipart/form-data"` attribute or file input key is not named `image`.
- **Resolution:** Verify that `<form method="POST" action="/analyze" enctype="multipart/form-data">` contains `<input type="file" name="image">`.
