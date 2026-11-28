# CIFAKE Real-Photo vs. AI-Generated Image Classifier

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?logo=flask&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-FF6F00?logo=tensorflow&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Academic%20Project-blue)

A Flask web application that classifies uploaded images as **Real photo** (`0`) or **AI-generated** (`1`) using either a Custom CNN trained on CIFAKE or a Hugging Face ViT classifier.

> **Limitation Notice:** The active GenImage v3 CNN scored **50.93%** and the active ViT checkpoint scored **55.03%** on 10,000 images from the held-out Midjourney generator. The ViT continuation did not improve validation accuracy, so its checkpoint was retained from v2. These scores are generator-specific and do not establish accuracy on other generators or arbitrary real-world images.

---

## Key Features

- 📤 **Image Upload** — Drag-and-drop or file-picker upload for JPG/JPEG/PNG images (up to 16 MB)
- 🔍 **GenImage v3 CNN** — Resizes images to 32×32 RGB (Pillow bilinear resampling, normalized to `[0, 1]`) and classifies them as `Real photo` or `AI-generated`
- 🤗 **Hugging Face ViT** — Optional second classifier loaded locally from `artifacts/cifake/ai_vs_real_genimage_outputs_v3/huggingface_vit/` with its matching image processor.
- 📊 **Model Score** — Displays the selected classifier's sigmoid or softmax score for the AI-generated class
- 📄 **PDF Summary Report** — Downloadable PDF summary including the prediction, score type, and model-specific limitation notice
- ⚡ **Privacy-First** — No permanent storage of user images; temporary files are cleaned up per session
- 🌐 **Responsive UI** — Bootstrap 5 frontend, works on desktop and mobile browsers

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.11, Flask 2.x, Werkzeug |
| **Machine Learning** | TensorFlow/Keras for CIFAKE CNN; PyTorch/Transformers for the optional Hugging Face ViT |
| **Image Processing** | OpenCV, Pillow (PIL), NumPy |
| **Data / Analysis** | Pandas, Matplotlib, SciPy |
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript (Vanilla) |
| **Report Generation** | ReportLab / WeasyPrint |
| **Testing** | pytest, pytest-flask, pytest-cov |
| **Dev Tools** | Jupyter Notebook, Google Colab |

---

## Quick Start

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| pip | 23+ |
| Git | 2.x |
| (Optional) CUDA | 11.8+ for GPU training |

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-org>/image-manipulation-detection.git
cd image-manipulation-detection

# 2. Create and activate a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Copy and configure environment variables
cp .env.example .env
# Edit .env to set SECRET_KEY, model paths, etc.

# 5. Launch the development server
python run.py
```

> **Note:** The app loads the GenImage v3 CNN and ViT files from
> `artifacts/cifake/ai_vs_real_genimage_outputs_v3/`. The CNN scored 50.93% on a
> 10,000-image Midjourney holdout; the ViT scored 55.03%, but its v3 continuation did
> not improve validation and the v2 weights were retained. These results do not prove
> performance across other generators. Both models use separate preprocessing, and
> neither is a universal AI-image detector.

The application will be available at **http://127.0.0.1:5000** by default.

## Metadata-First Provenance Checks

Every validated upload is checked for C2PA Content Credentials and common EXIF/XMP
generator hints before model inference. Only a **Trusted** C2PA manifest with an
explicit AI-origin action skips the model. This requires a PEM trust-anchor list
configured with `C2PA_TRUST_ANCHORS_PATH` in `.env`; without it, C2PA claims do not
bypass inference. Obtain trust anchors from the official
[Content Credentials trust list](https://contentcredentials.org/trust/anchors.pem).

EXIF/XMP tags such as Stable Diffusion parameters or ComfyUI software names are
unverified and spoofable: they are displayed as clues, never treated as proof, and
the selected model still runs. Missing or unverifiable provenance also falls through
to model inference. The metadata scan includes nested XMP fields and the active
C2PA manifest's generator/assertion text, so Gemini markers are reported even when
they are carried in Content Credentials rather than ordinary EXIF tags. Neither
metadata nor model output guarantees that an image is authentic or AI-generated.

---

## Compare the CIFAKE Models

Use [`notebooks/colab/06_cifake_model_comparison.ipynb`](./notebooks/colab/06_cifake_model_comparison.ipynb)
to evaluate the CIFAKE Custom CNN and the Hugging Face ViT on the same held-out
CIFAKE test split. It reports accuracy and other metrics without retraining.
These results measure performance on CIFAKE only and do not establish real-world
AI-image detection accuracy.

To further fine-tune only the Hugging Face ViT, use
[`notebooks/colab/07_finetune_cifake_models_on_ai_vs_real_.ipynb`](./notebooks/colab/07_finetune_cifake_models_on_ai_vs_real_.ipynb)
in Colab. The v5 workflow continues from `ai_vs_real_genimage_outputs_v3.zip` and
accepts GenImage ZIP archive(s) uploaded from your computer through Colab's file
picker. You can upload one combined archive if generator folders are preserved, or
multiple archives named for their generator (for example `BigGAN.zip` and
`Midjourney.zip`). Dataset images are staged in Colab's temporary `/content`
storage, not read from Drive. The notebook can optionally accept a CIFAKE ZIP for
training only.

It documents dataset sources and terms, inventories archive contents, filters
exact and perceptual duplicates across splits, and keeps ADM for validation and
Midjourney for final held-out testing. It saves versioned run state and split
manifests to Drive, selects a validation-only threshold, and exports a ViT-only ZIP
containing the selected checkpoint, processor, manifests, metrics, and run metadata.
Drive is still used for the starting v3 checkpoint and output/resume files. Outputs
are saved under `My Drive/ai_vs_real_vit_genimage_outputs_v5/`; v3 remains unchanged
and the app is not switched automatically. A 90% unseen-generator score is not
guaranteed, and a random or familiar-source split does not establish real-world
generalization.

---

## Legacy CASIA MobileNetV2 Training Notes

> These older notebooks train a CASIA tampering detector and do not train either
> Real-photo-vs-AI model currently available in the app.

Training MobileNetV2 on the full CASIA dataset requires a GPU and several hours of compute time. The recommended approach is to use **Google Colab's free or Pro GPU runtime** via three purpose-built notebooks. No local GPU is needed.

### Overview of the 3-Notebook Pipeline

| Notebook | File | Purpose |
|---|---|---|
| **1** | `notebooks/colab/01_dataset_preparation.ipynb` | Scan CASIA images, build metadata CSV, create train/val/test splits |
| **2** | `notebooks/colab/02_mobilenetv2_training.ipynb` | Train MobileNetV2 (two-phase: head then fine-tuning), save checkpoints |
| **3** | `notebooks/colab/03_mobilenetv2_evaluation.ipynb` | Load model, run evaluation on test split, export metrics JSON |

### Opening Notebooks in Colab

Click a badge below to open the notebook directly in Google Colab:

| Notebook | Open in Colab |
|---|---|
| Dataset Preparation | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<your-org>/image-manipulation-detection/blob/main/notebooks/colab/01_dataset_preparation.ipynb) |
| MobileNetV2 Training | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<your-org>/image-manipulation-detection/blob/main/notebooks/colab/02_mobilenetv2_training.ipynb) |
| Model Evaluation | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<your-org>/image-manipulation-detection/blob/main/notebooks/colab/03_mobilenetv2_evaluation.ipynb) |

> Replace `<your-org>` with your actual GitHub organisation or username once the repo is public.

### Providing the CASIA Dataset to Colab

Colab sessions do not have access to your local disk. Use one of the three methods below to supply the CASIA images:

**Method 1 — Colab file upload widget (small batches)**
```python
from google.colab import files
uploaded = files.upload()   # select your zip archive in the dialog
```
Best for CASIA v1 (~100 MB). Can be slow for CASIA v2 (~2 GB).

**Method 2 — Kaggle API (recommended for CASIA v2)**
```python
# In the notebook's setup cell:
from google.colab import userdata
import os
os.environ["KAGGLE_USERNAME"] = userdata.get("KAGGLE_USERNAME")
os.environ["KAGGLE_KEY"]      = userdata.get("KAGGLE_KEY")
!kaggle datasets download -d <dataset-slug> -p /content/data/
!unzip /content/data/<dataset>.zip -d /content/data/
```
Store your Kaggle API credentials in Colab Secrets (🔑 icon in the left sidebar).

**Method 3 — Manual zip upload via Google Drive**
1. Upload your CASIA zip to Google Drive.
2. Mount Drive in Colab: `from google.colab import drive; drive.mount('/content/drive')`
3. Copy or unzip directly from `/content/drive/MyDrive/`.

### Step-by-Step Training Instructions

**Step 1 — Run Notebook 1 (Dataset Preparation)**
1. Open `01_dataset_preparation.ipynb` in Colab.
2. Provide the CASIA dataset using one of the methods above.
3. Run all cells. The notebook produces:
   - `data/metadata/dataset_inventory.csv`
   - `data/splits/dataset_split.csv` (train / val / test assignment for every image)
4. Download `dataset_split.csv` to your local `data/splits/` folder and commit it so all team members use identical splits.

**Step 2 — Run Notebook 2 (MobileNetV2 Training)**
1. Switch to a **GPU runtime**: `Runtime → Change runtime type → T4 GPU`.
2. Open `02_mobilenetv2_training.ipynb`.
3. Upload or link the CASIA dataset and the `dataset_split.csv` from Step 1.
4. Run all cells. Training proceeds in two phases:
   - **Phase 1:** Only the custom classification head is trained (base frozen).
   - **Phase 2:** The top 30 layers of MobileNetV2 are unfrozen and fine-tuned at a lower learning rate.
5. Checkpoints are saved automatically to `/content/checkpoints/` after each epoch.
6. At the end of training, the model is saved as `/content/mobilenetv2.keras`.

**Step 3 — Run Notebook 3 (Evaluation)**
1. Open `03_mobilenetv2_evaluation.ipynb`.
2. Run all cells. The notebook loads `mobilenetv2.keras`, runs inference on the test split, and writes `evaluation_results.json`.

### Downloading the Trained Model and Placing it Locally

```python
# At the end of Notebook 2, run:
from google.colab import files
files.download('/content/mobilenetv2.keras')
```

Place the downloaded file in your local project:

```bash
cp ~/Downloads/mobilenetv2.keras artifacts/models/mobilenetv2.keras
```

The Flask app will automatically load this file on startup. See [Model Export and Deployment](#model-export-and-deployment) for full details.

---

## Three-Person Collaboration Workflow

### Team Roles and Responsibilities

| Member | Role | Primary Responsibilities |
|---|---|---|
| **Member 1** | Training Manager | Manage Colab sessions, run Notebooks 1–3, save and version checkpoints, distribute trained `.keras` files to the team |
| **Member 2** | Dataset Manager | Validate CASIA download, verify image counts and labels, produce and maintain `dataset_split.csv`, update `docs/dataset/` |
| **Member 3** | Evaluation & Integration | Load trained model into Flask, wire up `model_loader.py`, write integration tests, run `pytest`, update deployment docs |

### Git Workflow

**Branch naming convention:**

```
feature/<short-description>   # New features or capabilities
fix/<short-description>        # Bug fixes
docs/<short-description>       # Documentation only
test/<short-description>       # Test additions or fixes
```

**Pull request policy:**
- **Never commit directly to `main`.** All changes go through a pull request.
- Every PR requires **at least 1 reviewer** approval before merging.
- Delete the feature branch after merging.
- Run `pytest tests/ -v` locally and confirm all tests pass before opening a PR.

**Typical workflow:**
```bash
git checkout main && git pull
git checkout -b feature/integrate-mobilenet
# ... make changes ...
pytest tests/ -v
git add -p
git commit -m "feat(models): integrate mobilenetv2 model loader"
git push origin feature/integrate-mobilenet
# Open PR on GitHub → request review from a teammate
```

### Shared Dataset Split Requirement

All three team members **must use the same `data/splits/dataset_split.csv`** so that evaluation results are reproducible and comparable. The process:

1. Member 2 (Dataset Manager) generates the split using Notebook 1 and commits `dataset_split.csv` to `data/splits/` on `main`.
2. All other members pull `main` before training or evaluation.
3. **Never regenerate the split** after it has been committed — doing so invalidates all previously measured metrics.

### Training Session Protocol

- Only **one team member** should run a full training session at a time to avoid producing conflicting model files.
- When starting a training run, post a message in the team chat: *"Starting training run — ETA ~2 hours."*
- When done, share the `.keras` file (e.g. via Google Drive or as a GitHub Release asset) and announce the completion.
- Member 1 is responsible for maintaining `artifacts/models/evaluation_results.json` after each run.

---

## Model Export and Deployment

### After Colab Training

Once Notebook 2 completes, the following files are available in Colab's `/content/` directory:

| File | Purpose |
|---|---|
| `mobilenetv2.keras` | Trained model weights and architecture |
| `evaluation_results.json` | Test-set metrics produced by Notebook 3 |

The configuration files below are already committed to the repository and do **not** need to be downloaded from Colab:

| File | Location |
|---|---|
| `model_config.json` | `artifacts/models/model_config.json` |
| `class_labels.json` | `artifacts/models/class_labels.json` |
| `preprocessing_config.json` | `artifacts/models/preprocessing_config.json` |

### Downloading from Colab

```python
from google.colab import files
files.download('/content/mobilenetv2.keras')
files.download('/content/evaluation_results.json')
```

### Placing Files in the Local Project

```bash
# Place the model
cp ~/Downloads/mobilenetv2.keras artifacts/models/mobilenetv2.keras

# Update evaluation results
cp ~/Downloads/evaluation_results.json artifacts/models/evaluation_results.json
```

### Verifying the Model Loads Correctly

```bash
# Activate your virtual environment first
source .venv/bin/activate

python -c "
from src.models.model_loader import ModelLoader
loader = ModelLoader()
model = loader.load_mobilenet()
print('Model loaded. Input shape:', model.input_shape)
print('Output shape:', model.output_shape)
"
```

If the model loads without errors, the deployment is complete.

### Starting the Flask Application

```bash
python run.py
# Visit http://127.0.0.1:5000
```

The current app does not use this legacy MobileNetV2 model. It uses the CIFAKE CNN
or the selectable Hugging Face ViT described above.

---

## Checkpoint Recovery (Colab)

Colab free-tier sessions disconnect after approximately **12 hours** of inactivity or runtime. Notebook 2 saves a checkpoint after every epoch so that training can be resumed without starting over.

### Checkpoint Location

During training, checkpoints are saved to:
```
/content/checkpoints/checkpoint_epoch_{N:02d}_val{val_accuracy:.4f}.keras
```

The best checkpoint (highest validation accuracy) is also saved as:
```
/content/checkpoints/best_model.keras
```

### How to Resume Training

1. Reconnect to Colab and re-open `02_mobilenetv2_training.ipynb`.
2. Re-run the **setup cells** (install dependencies, mount Drive / re-upload data).
3. Scroll to the **"Resume from Checkpoint"** cell and set the path:
   ```python
   RESUME_FROM_CHECKPOINT = "/content/checkpoints/best_model.keras"
   ```
4. Run the resume cell — it loads weights from the checkpoint and continues training from the next epoch.

> **Recommendation:** Save your checkpoints to Google Drive during long training runs so they survive a session disconnect:
> ```python
> import shutil
> shutil.copy('/content/checkpoints/best_model.keras',
>             '/content/drive/MyDrive/image-detection-checkpoints/best_model.keras')
> ```

---

## Project Structure

```
image-manipulation-detection/
│
├── app.py                      # Flask application factory
├── run.py                      # Development server entry point
├── config.py                   # Configuration classes (Dev/Prod/Test)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .gitignore
│
├── src/                        # Core Python package
│   ├── data/                   # Dataset loading, splitting, augmentation
│   ├── models/                 # CNN and MobileNetV2 model definitions
│   ├── preprocessing/          # ELA generation, image resizing/normalisation
│   ├── training/               # Training loops, callbacks, evaluation
│   ├── evaluation/             # Metrics, confusion matrix, visualisation
│   ├── explainability/         # Grad-CAM implementation
│   ├── services/               # Detection, ELA, and report services
│   └── utils/                  # File validation, logging, exceptions
│
├── web/                        # Flask web layer
│   ├── routes/                 # Blueprint route handlers
│   │   ├── main_routes.py
│   │   └── detection_routes.py
│   ├── templates/              # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── result.html
│   │   ├── about.html
│   │   └── error.html
│   └── static/
│       ├── css/style.css
│       └── js/main.js
│
├── data/                       # Dataset storage (not committed to Git)
│   ├── CASIA1/
│   │   ├── Au/                 # Authentic images
│   │   └── Tp/                 # Tampered images
│   └── CASIA2/
│       ├── Au/
│       └── Tp/
│
├── artifacts/                  # Training outputs (not committed)
│   ├── models/                 # Saved .keras / .h5 model files
│   ├── plots/                  # Training curves, confusion matrices
│   └── reports/                # Evaluation JSON/CSV reports
│
├── notebooks/                  # Jupyter experimentation notebooks
│   ├── 01_dataset_exploration.ipynb
│   ├── 02_data_preprocessing.ipynb
│   ├── 03_ela_experiments.ipynb
│   ├── 04_cnn_experiments.ipynb
│   ├── 05_mobilenet_experiments.ipynb
│   └── 06_model_evaluation.ipynb
│
├── scripts/                    # CLI utility scripts
│   ├── prepare_dataset.py
│   ├── train.py
│   ├── evaluate.py
│   └── cleanup.py
│
├── tests/                      # pytest test suite
│   ├── test_api.py
│   ├── test_ela.py
│   ├── test_file_validation.py
│   ├── test_models.py
│   ├── test_prediction.py
│   ├── test_preprocessing.py
│   └── test_dataset.py
│
└── docs/                       # Project documentation
    ├── README.md               # Documentation index
    ├── PROJECT_OVERVIEW.md
    ├── PROJECT_SCOPE.md
    ├── PROBLEM_STATEMENT.md
    ├── PROJECT_OBJECTIVES.md
    ├── REQUIREMENTS.md
    ├── FUNCTIONAL_REQUIREMENTS.md
    ├── NON_FUNCTIONAL_REQUIREMENTS.md
    ├── INSTALLATION_GUIDE.md
    ├── SYSTEM_ARCHITECTURE.md
    ├── API_DOCUMENTATION.md
    ├── ELA_DOCUMENTATION.md
    ├── MODEL_DOCUMENTATION.md
    ├── DEVELOPER_GUIDE.md
    ├── USER_GUIDE.md
    ├── TESTING_STRATEGY.md
    ├── KNOWN_LIMITATIONS.md
    ├── dataset/
    │   └── DATASET_OVERVIEW.md
    ├── architecture/
    │   ├── system_architecture.md
    │   ├── component_diagram.md
    │   └── workflow_diagram.md
    ├── decisions/
    │   ├── ADR-001-technology-stack.md
    │   ├── ADR-002-dataset-selection.md
    │   ├── ADR-003-model-selection.md
    │   └── ADR-004-ela-implementation.md
    └── progress/
        ├── TASK_TRACKER.md
        ├── DEVELOPMENT_LOG.md
        └── CHANGELOG.md
```

---

## Usage

### Running the Application

```bash
# Development mode (auto-reload, debug toolbar)
python run.py

# Or using Flask CLI
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

### Analysing an Image

1. Open `http://127.0.0.1:5000` in your browser.
2. Click **Choose File** or drag-and-drop an image onto the upload area.
3. Supported formats: **JPG, JPEG, PNG** — maximum file size **16 MB**.
4. Optionally select either the CIFAKE Custom CNN or Hugging Face ViT.
5. Click **Analyse**.
6. View the prediction label (**Real photo** / **AI-generated**) and model score.
7. Click **Download PDF Report** to save the full analysis summary.

### Running Tests

```bash
# Run the full test suite
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run a specific test module
pytest tests/test_ela.py -v
```

---

## Dataset

This project uses the **CASIA Image Tampering Detection Evaluation Database** (v1.0 and v2.0).

| Version | Authentic | Tampered | Total |
|---|---|---|---|
| CASIA v1.0 | 800 | 921 | 1,721 |
| CASIA v2.0 | 7,491 | 5,123 | 12,614 |

For full dataset details, access instructions, and license information, see **[docs/dataset/DATASET_OVERVIEW.md](docs/dataset/DATASET_OVERVIEW.md)**.

---

## Documentation Index

| Document | Description |
|---|---|
| [Project Overview](docs/PROJECT_OVERVIEW.md) | Goals, timeline, team roles, success criteria |
| [Problem Statement](docs/PROBLEM_STATEMENT.md) | Research context and motivation |
| [Project Scope](docs/PROJECT_SCOPE.md) | In-scope / out-of-scope features and constraints |
| [Requirements](docs/REQUIREMENTS.md) | Master requirements index |
| [Functional Requirements](docs/FUNCTIONAL_REQUIREMENTS.md) | Detailed FR-001 to FR-015 |
| [Non-Functional Requirements](docs/NON_FUNCTIONAL_REQUIREMENTS.md) | Performance, security, usability specs |
| [Installation Guide](docs/INSTALLATION_GUIDE.md) | Step-by-step setup for all platforms |
| [System Architecture](docs/SYSTEM_ARCHITECTURE.md) | Architecture diagrams and component descriptions |
| [API Documentation](docs/API_DOCUMENTATION.md) | Flask route reference |
| [ELA Documentation](docs/ELA_DOCUMENTATION.md) | Error Level Analysis theory and implementation |
| [Model Documentation](docs/MODEL_DOCUMENTATION.md) | CNN and MobileNetV2 architecture details |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Coding standards, contribution workflow |
| [User Guide](docs/USER_GUIDE.md) | End-user instructions |
| [Testing Strategy](docs/TESTING_STRATEGY.md) | Test plans and coverage targets |
| [Known Limitations](docs/KNOWN_LIMITATIONS.md) | Current limitations and disclaimers |
| [Dataset Overview](docs/dataset/DATASET_OVERVIEW.md) | CASIA dataset details and access |
| [Colab Training Guide](docs/colab/COLAB_GUIDE.md) | Step-by-step Google Colab training instructions |
| [Collaboration Guide](docs/collaboration/COLLABORATION_GUIDE.md) | Three-person team workflow and Git conventions |

---

## Contributing

This is a university semester project. If you are a team member:

1. Create a feature branch from `main`: `git checkout -b feature/your-feature`
2. Write tests for any new functionality.
3. Ensure `pytest tests/ -v` passes before opening a pull request.
4. Follow the coding standards in [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md).
5. Submit a pull request and request a review from at least one team member.

For detailed contribution guidelines, see [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md).

---

## License

This project is released under the **MIT License**. See [`LICENSE`](LICENSE) for the full text.

The **CASIA dataset** is licensed for **academic and research use only**. You must cite the original authors (Dong et al.) in any publication. See [docs/dataset/DATASET_OVERVIEW.md](docs/dataset/DATASET_OVERVIEW.md) for citation details.

---

*University Semester Project — Artificial Intelligence Course, 5th Semester*
