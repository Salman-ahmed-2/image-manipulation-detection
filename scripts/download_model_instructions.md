# Downloading and Deploying the Trained MobileNetV2 Model

After completing training in Google Colab, follow these steps to bring the model
into your local Flask application.

---

## Step 1 — Download the model from Colab

At the end of `notebooks/colab/02_mobilenetv2_training.ipynb`, the model is saved to:

```
artifacts/models/mobilenetv2.keras
```

### Option A — Colab Files panel

1. Open the **Files** panel (folder icon on the left sidebar in Colab).
2. Navigate to `artifacts/models/`.
3. Right-click `mobilenetv2.keras` → **Download**.

### Option B — Code cell

Add and run this cell at the end of the training notebook:

```python
from google.colab import files
files.download('artifacts/models/mobilenetv2.keras')
```

---

## Step 2 — Place the model in your local project

Copy the downloaded file to:

```
<project-root>/artifacts/models/mobilenetv2.keras
```

The Flask application prefers `mobilenetv2.keras` over `mobilenet_model.keras`
automatically — no renaming required.

---

## Step 3 — Also download the evaluation config files (optional but recommended)

Download these from Colab and place them in `artifacts/models/`:

- `model_config.json` — architecture record
- `class_labels.json` — class mapping
- `preprocessing_config.json` — normalization settings
- `evaluation_results.json` — test-set metrics

---

## Step 4 — Verify the model loads correctly

```bash
cd <project-root>

# Activate your virtual environment
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows

python -c "
from src.models.model_loader import ModelLoader
ModelLoader.load_all_models()
is_real = not ModelLoader.is_fallback('mobilenet')
print('Model loaded successfully:', is_real)
"
```

Expected output:

```
Model loaded successfully: True
```

If you see `False`, the `.keras` file was not found or could not be loaded. Check:
- The file exists at `artifacts/models/mobilenetv2.keras`
- The file is not corrupted (expected size: several MB)
- TensorFlow version matches Colab (>=2.15.0)

---

## Step 5 — Start the Flask application

```bash
python run.py
```

Open your browser at **http://127.0.0.1:5000**

Upload a test image — the app will use MobileNetV2 for inference.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Using fallback mock model" in logs | `.keras` file missing | Re-check file placement in `artifacts/models/` |
| `InvalidArgumentError` on prediction | Preprocessing mismatch | Ensure `mode="mobilenet"` ([-1,1] range) was used in training |
| Very slow first prediction | Model warmup on CPU | First request triggers graph build; subsequent requests are fast |
| `OSError: file not found` | Wrong working directory | Run `python run.py` from the project root |
