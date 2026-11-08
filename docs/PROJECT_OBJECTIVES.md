# Project Objectives: Image Manipulation Detection System

## 1. Primary Objective
The primary objective of this project is to architect, develop, evaluate, and deliver a production-ready, web-based software application capable of performing preliminary authenticity screening on digital photographs. The system leverages deep learning classification architectures alongside Error Level Analysis (ELA) to provide actionable verdicts (Authentic vs. Potentially Manipulated) with accompanying confidence metrics within an intuitive user experience.

## 2. Secondary Objectives
Beyond the primary detection capability, the project encompasses several supporting objectives:
1. **Interactive Forensic Exploration:** Enable end-users to visually cross-examine an uploaded photograph against an algorithmically generated Error Level Analysis (ELA) map side-by-side.
2. **Transparent Evidentiary Reporting:** Provide an on-demand, downloadable PDF diagnostic report containing input metadata, prediction confidence, visual forensic maps, and standard evidentiary disclaimers.
3. **Data Privacy and Ephemeral State:** Guarantee user confidentiality by implementing strict session-scoped temporary file handling, ensuring uploaded user media is automatically purged upon session completion with zero permanent database persistence.
4. **Accessible Engineering:** Deliver a lightweight, standards-compliant interface using HTML5, CSS3, JavaScript, and Bootstrap 5 that runs without requiring specialized client hardware or proprietary software plugins.

## 3. Technical Objectives
From a software engineering and infrastructure standpoint, the project will achieve:
- **Modular Architecture:** Construct a decoupled architecture under `src/` separating data ingestion (`src/data/`), image preprocessing (`src/preprocessing/`), neural architectures (`src/models/`), business logic (`src/services/`), and utility handlers (`src/utils/`).
- **Robust Image Processing Pipeline:** Build deterministic pipelines for sanitizing file inputs, validating magic-byte headers, resizing to model input dimensions (224x224x3), normalizing tensors, and generating enhanced JPEG compression residual maps.
- **RESTful Application Server:** Deploy a Python 3.11 + Flask application utilizing Blueprints for route isolation (`main_routes`, `detection_routes`) and uniform JSON error-handling.
- **Unit and Integration Verification:** Establish a test suite using `pytest` covering file validation, preprocessing boundary conditions, ELA mathematical invariants, model inference stubs, and endpoint response codes.

## 4. Research and Machine Learning Objectives
- **Benchmark Dataset Curation:** Systematically ingest, sanitize, deduplicate, and split the CASIA v1.0 (1,721 images) and CASIA v2.0 (12,614 images) forensic datasets using group-aware splitting to prevent source-image data leakage.
- **Dual-Model Comparative Evaluation:** 
  - Train a Custom Convolutional Neural Network (4 Conv-Pool blocks, Dropout regularization) from scratch on forensic artifacts.
  - Fine-tune a Pretrained MobileNetV2 architecture leveraging ImageNet representations adapted with a specialized binary classification head.
- **Comprehensive Evaluation Protocol:** Measure and contrast both networks across Accuracy, Precision, Recall (minimizing false negatives), F1-Score, ROC-AUC, training convergence rate, inference latency (CPU/GPU), and parameter disk footprints.

## 5. Educational and Pedagogical Objectives
As a 4-person university semester project scheduled over a 4–6 week lifecycle, the team aims to:
- Master full-lifecycle AI/ML system development from academic research papers to containerized web deployment.
- Learn strict version control practices (Git feature-branching, conventional commits, pull-request peer reviews).
- Acquire professional software architecture discipline (Architectural Decision Records, defensive programming, Google-style docstrings).

## 6. SMART Objectives Matrix

| ID | Specific Goal | Measurable Metric | Achievable Rationale | Relevant Purpose | Time-Bound Target |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SO-01** | Dataset Ingestion & Verification | Ingest 12,614 CASIA v2 & 1,721 CASIA v1 files; output 3 verified metadata CSVs | Standard Python scripts + Pandas metadata generation | Critical ground truth for supervised training | Week 2, Day 3 |
| **SO-02** | ELA Pipeline Implementation | Generate ELA difference visualization for JPEG and PNG inputs with < 2.0s latency | Pillow difference and enhancement routines | Visual interpretability module | Week 2, Day 5 |
| **SO-03** | Custom CNN Training | Train Custom CNN on CASIA splits achieving stable convergence without catastrophic overfitting | Colab T4 GPU compute runtime | Core baseline forensic classifier | Week 3, Day 7 |
| **SO-04** | MobileNetV2 Fine-Tuning | Fine-tune 2-phase MobileNetV2 classifier comparing feature extraction vs. top-layer unfrozen | Transfer learning on pre-trained ImageNet weights | Lightweight transfer learning benchmark | Week 4, Day 4 |
| **SO-05** | Flask Service Layer Integration | Build `/analyze` endpoint processing validation, inference, and ELA in < 5.0s | Flask application factory + pre-loaded Keras model in memory | Connects frontend to ML engine | Week 4, Day 7 |
| **SO-06** | Interactive Web UI & PDF Export | Bootstrap 5 dashboard with side-by-side display and automated PDF report download | Jinja2 templates + fpdf2/ReportLab PDF rendering | Complete user-facing deliverables | Week 5, Day 5 |
| **SO-07** | Test Suite & Quality Assurance | Achieve > 80% code coverage across `src/` modules using pytest | Unit tests with synthetic PIL test fixtures | System stability and regression prevention | Week 5, Day 7 |
