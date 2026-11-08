# Image Manipulation Detection System Using Deep Learning

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?logo=flask&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-FF6F00?logo=tensorflow&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Academic%20Project-blue)

A deep-learning–powered web application that performs **preliminary image authenticity screening** by detecting common manipulation techniques — including copy-move and splicing forgeries — using a custom CNN, MobileNetV2 transfer learning, and Error Level Analysis (ELA) visualization.

> **Disclaimer:** This system is a university semester project intended for educational and research purposes. It provides a preliminary indication of potential manipulation and should **not** be used as conclusive forensic evidence or professional certification.

---

## Key Features

- 📤 **Image Upload** — Drag-and-drop or file-picker upload for JPG/JPEG/PNG images (up to 16 MB)
- 🔍 **Dual-Model Detection** — Custom CNN and MobileNetV2 models trained on CASIA v1.0 and v2.0 datasets
- 📊 **Confidence Scoring** — Per-class probability breakdown displayed alongside each prediction
- 🎨 **ELA Visualization** — Error Level Analysis heat-map generated and overlaid on the original image
- 📋 **Results Dashboard** — Unified view of prediction, confidence, and ELA side-by-side
- 📄 **PDF Report Download** — Downloadable summary report of the full analysis session
- ⚡ **Privacy-First** — No permanent storage of user images; temporary files deleted after session ends
- 🌐 **Responsive UI** — Bootstrap 5 frontend, works on desktop and mobile browsers

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.11, Flask 2.x, Werkzeug |
| **Machine Learning** | TensorFlow 2.x, Keras, scikit-learn |
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

# 5. (Optional) Download and prepare the CASIA dataset
#    See docs/dataset/DATASET_OVERVIEW.md for dataset access instructions
python scripts/prepare_dataset.py

# 6. (Optional) Train models
#    Pre-trained weights should be placed in artifacts/models/
python scripts/train.py --model cnn
python scripts/train.py --model mobilenet

# 7. Launch the development server
python run.py
```

The application will be available at **http://127.0.0.1:5000** by default.

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
4. Optionally select the detection model (CNN or MobileNetV2).
5. Click **Analyse**.
6. View the prediction label (**Authentic** / **Tampered**), confidence score, and ELA visualisation.
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
