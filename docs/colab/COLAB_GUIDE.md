# Google Colab Training Guide

> This guide covers the complete workflow for training the MobileNetV2 image manipulation
> detection model on Google Colab using the CASIA v1.0 and v2.0 datasets.

---

## Overview

Training MobileNetV2 on the combined CASIA dataset (~14,000 images) requires several hours of
compute time and a GPU. Rather than requiring every team member to own a capable GPU, the project
uses a **three-notebook Colab pipeline**:

| Notebook | File | What it does |
|---|---|---|
| **1** | `notebooks/colab/01_dataset_preparation.ipynb` | Scans CASIA directories, validates filenames, builds inventory CSV, creates reproducible train/val/test split |
| **2** | `notebooks/colab/02_mobilenetv2_training.ipynb` | Runs two-phase MobileNetV2 training with checkpoint saves after every epoch |
| **3** | `notebooks/colab/03_mobilenetv2_evaluation.ipynb` | Evaluates the saved model on the test split and exports `evaluation_results.json` |

The trained `.keras` model is downloaded from Colab and placed in `artifacts/models/` on the
developer's local machine. The Flask app then loads it at startup — **no training happens locally**.

---

## Prerequisites

| Requirement | Details |
|---|---|
| Google account | Required for Colab and Google Drive access |
| Colab plan | Free tier works; Colab Pro recommended for longer sessions (up to 24 h) |
| CASIA v1.0 dataset | ~100 MB zip — 1,721 images total |
| CASIA v2.0 dataset | ~2.1 GB zip — 12,614 images total |
| Kaggle account (optional) | Needed only if using the Kaggle API method to supply the dataset |

> **Dataset licensing:** The CASIA dataset is for academic and research use only.
> Download it via the official channels described in `docs/dataset/DATASET_OVERVIEW.md`.

---

## Notebook 1: Dataset Preparation

### Opening in Colab

1. Navigate to the notebook in the GitHub repository:
   `notebooks/colab/01_dataset_preparation.ipynb`
2. Click **Open in Colab** (badge at the top of the notebook) **or** go to
   [colab.research.google.com](https://colab.research.google.com), choose **GitHub**, and
   paste the repository URL.
3. Colab opens a copy in your session. No files are written to GitHub automatically.

### Providing the CASIA Dataset

Colab sessions run on Google's servers and have no access to your local disk. You must upload
or link the CASIA images every new session.

#### Method 1: Direct Upload (recommended for CASIA v1 only)

```python
from google.colab import files
uploaded = files.upload()   # a file picker dialog appears in the notebook output
```

After upload, unzip:

```python
import zipfile, os
zip_path = list(uploaded.keys())[0]
os.makedirs('/content/data', exist_ok=True)
with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall('/content/data')
print("Extracted to /content/data")
```

This method works well for CASIA v1 (~100 MB). For CASIA v2 (~2 GB), the upload is too slow
— use Method 2 or 3 instead.

#### Method 2: Kaggle API (recommended for CASIA v2)

1. Generate a Kaggle API token at [kaggle.com/settings](https://www.kaggle.com/settings)
   (Account → API → Create New Token). This downloads `kaggle.json`.
2. Store the credentials in **Colab Secrets** (🔑 icon in the left sidebar):
   - Add secret `KAGGLE_USERNAME` → your Kaggle username
   - Add secret `KAGGLE_KEY` → the API key from `kaggle.json`
3. In the notebook setup cell:

```python
from google.colab import userdata
import os, subprocess

os.environ["KAGGLE_USERNAME"] = userdata.get("KAGGLE_USERNAME")
os.environ["KAGGLE_KEY"]      = userdata.get("KAGGLE_KEY")

# Replace <dataset-slug> with the actual Kaggle dataset slug, e.g. "divg07/casia-20-image-tampering-detection-dataset"
subprocess.run(["kaggle", "datasets", "download", "-d", "<dataset-slug>",
                "-p", "/content/data/", "--unzip"], check=True)
```

#### Method 3: Manual Zip Upload via Google Drive

If you have already uploaded the CASIA zips to Google Drive:

```python
from google.colab import drive
drive.mount('/content/drive')

import zipfile, os
os.makedirs('/content/data', exist_ok=True)

# Update the path to match your Drive folder structure
casia_v1_zip = '/content/drive/MyDrive/datasets/CASIA_v1.zip'
casia_v2_zip = '/content/drive/MyDrive/datasets/CASIA_v2.zip'

with zipfile.ZipFile(casia_v1_zip, 'r') as z:
    z.extractall('/content/data/casia_v1')
with zipfile.ZipFile(casia_v2_zip, 'r') as z:
    z.extractall('/content/data/casia_v2')
print("Datasets ready.")
```

This is the fastest method for CASIA v2 since Drive transfers happen server-to-server.

### Running the Notebook

After providing the dataset, run all cells in order (`Runtime → Run all`). The notebook:

1. Scans both CASIA directories and validates that filenames start with `Au_` (authentic) or `Tp_` (tampered).
2. Logs and skips any file that does not match either prefix.
3. Builds `dataset_inventory.csv` listing every valid image with its label.
4. Applies a **stratified split** (default 70% train / 15% val / 15% test) using a fixed random seed for reproducibility.
5. Writes `dataset_split.csv` assigning each image to a split partition.

Expected runtime: **5–10 minutes** on a CPU runtime (no GPU needed for Notebook 1).

### Output Files

| File | Colab Path | What it contains |
|---|---|---|
| `dataset_inventory.csv` | `/content/data/metadata/dataset_inventory.csv` | Image path, label int, label name, dataset version, file size |
| `dataset_split.csv` | `/content/data/splits/dataset_split.csv` | Image path, label, split assignment (train/val/test) |

**Download and commit `dataset_split.csv`** to `data/splits/dataset_split.csv` in the repository.
All subsequent training and evaluation runs must reference this exact file.

```python
from google.colab import files
files.download('/content/data/splits/dataset_split.csv')
files.download('/content/data/metadata/dataset_inventory.csv')
```

---

## Notebook 2: MobileNetV2 Training

### GPU Runtime Setup

Before running Notebook 2, switch to a GPU runtime:

1. In the Colab menu: `Runtime → Change runtime type`
2. Set **Hardware accelerator** to **T4 GPU** (free tier) or **A100** (Colab Pro+).
3. Click **Save**. The runtime restarts.

Verify the GPU is active:
```python
import tensorflow as tf
print("GPUs:", tf.config.list_physical_devices('GPU'))
# Expected: [PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]
```

If the list is empty, the runtime is CPU-only — repeat the steps above.

### Checkpoint System

The notebook saves a checkpoint file after every training epoch using the Keras
`ModelCheckpoint` callback. Checkpoints are written to `/content/checkpoints/`.

```
/content/checkpoints/
├── checkpoint_epoch_01_val0.7812.keras
├── checkpoint_epoch_02_val0.8034.keras
├── ...
└── best_model.keras           ← best val_accuracy so far (overwritten each epoch)
```

> **Important:** Colab session storage is wiped when the session ends. If you need checkpoints
> to survive a disconnect, copy them to Drive after each epoch (see the `BackupToDrive` callback
> cell in the notebook).

### Two-Phase Training

Training is split into two phases to stabilise convergence:

**Phase 1 — Head training (base frozen)**
- All MobileNetV2 base layers are frozen; only the custom classification head is trained.
- Learning rate: `1e-3` (Adam).
- Duration: 10 epochs by default.
- Purpose: initialise the head weights to a reasonable starting point before the larger model is exposed to gradient updates.

**Phase 2 — Fine-tuning (top layers unfrozen)**
- The last 30 layers of the MobileNetV2 base are unfrozen.
- Learning rate: `1e-5` (lower to avoid destroying pretrained features).
- Duration: 20 epochs by default.
- Purpose: adapt the high-level MobileNetV2 features to the CASIA image domain.

Total expected training time: **1.5–3 hours** on a T4 GPU.

### Monitoring Training

Colab displays live training progress in the cell output. Additionally, the notebook plots
accuracy and loss curves after each phase using Matplotlib. These plots are saved to
`/content/artifacts/plots/`.

You can also monitor training via TensorBoard if the TensorBoard callback cell is enabled:
```python
%load_ext tensorboard
%tensorboard --logdir /content/logs
```

### Session Recovery

If the Colab session disconnects mid-training:

1. Reconnect and re-open the notebook.
2. Re-run the **setup cells** (pip installs, Drive mount, dataset re-link).
3. Scroll to the **"Resume from Checkpoint"** section and set:
   ```python
   RESUME_FROM_CHECKPOINT = "/content/checkpoints/best_model.keras"
   ```
4. If using Drive backup, the best checkpoint path would be:
   ```python
   RESUME_FROM_CHECKPOINT = "/content/drive/MyDrive/image-detection-checkpoints/best_model.keras"
   ```
5. Run the resume cell — it loads the saved weights and continues from the next epoch.

> **Tip:** Colab Pro sessions last up to 24 hours and are much less likely to disconnect
> during a 3-hour training run.

### Saving the Model

At the end of Phase 2, the notebook saves the final trained model:

```python
model.save('/content/mobilenetv2.keras')
print("Model saved to /content/mobilenetv2.keras")
```

It also computes a final validation score and prints a summary of the best epoch reached.

---

## Notebook 3: Model Evaluation

### Loading the Trained Model

Notebook 3 loads the trained model directly from `/content/mobilenetv2.keras`. If you are
evaluating a checkpoint rather than the final model, update the path:

```python
MODEL_PATH = '/content/mobilenetv2.keras'   # or a checkpoint path
```

### Test Dataset

The notebook reads `dataset_split.csv` and filters rows where `split == "test"`. It then
builds a `tf.data.Dataset` pipeline that:
1. Loads each image from disk.
2. Resizes to `(224, 224)`.
3. Applies MobileNetV2 normalisation: `pixel / 127.5 - 1.0`.

The test set is never used during training or hyperparameter tuning — it is held out
exclusively for the final evaluation reported in `evaluation_results.json`.

### Evaluation Metrics

The notebook computes and displays:

| Metric | Description |
|---|---|
| Accuracy | Fraction of correctly classified images |
| Precision | TP / (TP + FP) for the "Manipulated" class |
| Recall | TP / (TP + FN) for the "Manipulated" class |
| F1 Score | Harmonic mean of precision and recall |
| ROC-AUC | Area under the ROC curve |
| Confusion Matrix | 2×2 matrix (Authentic vs. Manipulated) |

A classification report (per-class precision, recall, F1) is also printed.

### Saving Results

```python
import json
results = {
    "status": "evaluated",
    "model_path": MODEL_PATH,
    "metrics": {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "roc_auc": float(roc_auc),
        "confusion_matrix": cm.tolist()
    }
}
with open('/content/evaluation_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Saved evaluation_results.json")
```

Download this file and place it in `artifacts/models/evaluation_results.json`.

---

## Model Export

### Downloading from Colab

Run the following in a cell at the end of Notebook 2 or 3:

```python
from google.colab import files
files.download('/content/mobilenetv2.keras')
files.download('/content/evaluation_results.json')
```

Your browser will prompt you to save both files.

### Local Deployment

Place the downloaded files in the local repository:

```bash
cp ~/Downloads/mobilenetv2.keras        artifacts/models/mobilenetv2.keras
cp ~/Downloads/evaluation_results.json  artifacts/models/evaluation_results.json
```

The file `artifacts/models/mobilenetv2.keras` is listed in `.gitignore` and **should not be
committed to Git** (the binary is too large). Share it with teammates via Google Drive or a
GitHub Release asset instead.

### Verifying the Model

After placing the model, verify that the project's model loader can read it without errors:

```bash
source .venv/bin/activate

python - <<'EOF'
from src.models.model_loader import ModelLoader
loader = ModelLoader()
model = loader.load_mobilenet()
print("Input shape :", model.input_shape)
print("Output shape:", model.output_shape)
print("Trainable params:", model.count_params())
print("OK — model verified.")
EOF
```

Expected output:
```
Input shape : (None, 224, 224, 3)
Output shape: (None, 1)
Trainable params: <some large number>
OK — model verified.
```

If you see a `FileNotFoundError`, confirm that `artifacts/models/mobilenetv2.keras` exists
and that `Config.MODEL_PATH_MOBILENET_V2` in `config.py` points to the correct path.

---

## Troubleshooting

### Common Issues

#### "CUDA out of memory" during training
- Reduce `BATCH_SIZE` in the notebook from `32` to `16` or `8`.
- Restart the runtime (`Runtime → Restart runtime`) and run again.
- Switch to a Colab Pro session with an A100 GPU for more VRAM.

#### Session disconnects before training finishes
- Enable the **Drive backup callback** in the notebook to copy checkpoints to Google Drive after each epoch.
- Resume from the latest checkpoint using the "Resume from Checkpoint" cell (see [Session Recovery](#session-recovery)).

#### `dataset_split.csv not found` error
- Run Notebook 1 first and upload `dataset_split.csv` to Colab before running Notebook 2.
- If using Drive mount, verify the path in the notebook points to the correct Drive location.

#### Model produces all-zero predictions after loading
- This usually means the preprocessing normalisation does not match training.
- Ensure that images are normalised with `pixel / 127.5 - 1.0` (MobileNetV2 standard), not divided by `255.0`.
- Check `artifacts/models/preprocessing_config.json` for the expected normalisation formula.

#### Colab badge links return 404
- The repository must be **public** on GitHub for Colab badge links to work.
- If the repo is private, open the notebook via `File → Open notebook → GitHub` in Colab and authenticate.

#### `ValueError: Input 0 of layer is incompatible` when running Flask app
- The model was saved with a different input shape than `(224, 224, 3)`.
- Retrain with the default input shape, or update `Config.IMAGE_SIZE` and `Config.INPUT_SHAPE` in `config.py` to match.

#### TensorFlow version mismatch
- The model must be loaded with the **same major TensorFlow version** used during training.
- Check the training cell output for the TF version printed at startup, and ensure your local environment matches.
- Run `pip install tensorflow==<version>` to align versions if needed.
