# Project Overview: Image Manipulation Detection System Using Deep Learning

**Document Type:** Project Overview
**Course:** Artificial Intelligence (5th Semester)
**Status:** Active Development
**Last Updated:** November 2026

---

## 1. Project Title and Category

| Field | Value |
|---|---|
| **Project Title** | Image Manipulation Detection System Using Deep Learning |
| **Category** | Applied AI / Computer Vision / Digital Forensics |
| **Type** | University Semester Project — Web Application with ML Backend |
| **Academic Level** | Undergraduate, 5th Semester |
| **Team Size** | 4 members |
| **Timeline** | 4–6 weeks |

---

## 2. Problem Statement

The proliferation of sophisticated image editing software — from professional tools such as Adobe Photoshop to AI-based generators like DALL-E and Stable Diffusion — has made digital image manipulation trivially accessible to anyone with a consumer device. This democratisation of editing capability, while creatively empowering, presents a serious threat to the information ecosystem. Manipulated images are routinely weaponised in misinformation campaigns, spread unchecked across social media platforms, and have caused demonstrable harm in contexts ranging from political elections to public health emergencies. Journalists and fact-checkers are under increasing pressure to verify the authenticity of visual evidence quickly and reliably, yet professional forensic tools remain expensive, inaccessible, or require domain expertise to interpret. The need for an accessible, open, and explainable preliminary screening tool — one that can flag potentially tampered images without requiring specialist training — has never been more acute.

---

## 3. Project Objectives

1. **Build a functional web application** that accepts user-uploaded images and returns an authenticity prediction (Authentic / Tampered) with an associated confidence score.
2. **Train and integrate two classification models** — a custom Convolutional Neural Network (CNN) and a MobileNetV2 transfer-learning model — both trained on the CASIA v1.0 and v2.0 image forgery datasets.
3. **Implement Error Level Analysis (ELA)** as a visual forensic aid that highlights regions of an image that may have been digitally altered, presented alongside the model's prediction.
4. **Generate downloadable PDF analysis reports** summarising the prediction result, confidence score, and ELA visualisation for a given uploaded image.
5. **Design a clean, responsive, and intuitive user interface** using Bootstrap 5 that works across desktop and mobile browsers.
6. **Evaluate model performance** on held-out test data, reporting accuracy, precision, recall, F1-score, and ROC-AUC.
7. **Document the system thoroughly** so that future students or contributors can understand, extend, and replicate the work.

---

## 4. Scope

### In Scope / Out of Scope

| Feature | In Scope | Out of Scope |
|---|---|---|
| JPG/JPEG/PNG image upload via web UI | ✅ | |
| File size limit enforcement (16 MB max) | ✅ | |
| File format validation (magic bytes) | ✅ | |
| Custom CNN binary classifier (Authentic/Tampered) | ✅ | |
| MobileNetV2 binary classifier | ✅ | |
| Prediction confidence score display | ✅ | |
| ELA generation and overlay visualisation | ✅ | |
| Results dashboard (prediction + ELA side by side) | ✅ | |
| PDF report download | ✅ | |
| Grad-CAM visualisation (optional / stretch goal) | ✅ [PROPOSED] | |
| Analysis history / session log | ✅ [PROPOSED] | |
| Model comparison dashboard | ✅ [PROPOSED] | |
| User authentication / login system | | ❌ |
| Database of past user analyses | | ❌ |
| Payment or subscription system | | ❌ |
| Cloud hosting / deployment pipeline | | ❌ |
| Real-time video analysis | | ❌ |
| Audio or document forensics | | ❌ |
| Support for RAW, TIFF, BMP, WebP, HEIC formats | | ❌ |
| Copy-move region localisation (pixel-level mask) | | ❌ |
| Professional forensic certification | | ❌ |
| Multi-language UI | | ❌ |

---

## 5. Target Users

| User Type | Description | Use Case |
|---|---|---|
| **Journalist / Fact-Checker** | Media professional verifying images submitted with news stories | Quick preliminary screening before investing time in deeper verification |
| **Academic Researcher** | Student or academic studying digital forensics or AI | Exploring ELA output and model behaviour as a learning tool |
| **Computer Science Student** | Undergraduate learning about deep learning and image processing | Running the system locally to study the codebase, retrain models, or extend features |
| **General Public User** | Curious individual who encountered a suspicious image online | Low-friction first-pass check to decide whether further investigation is warranted |

---

## 6. Expected Deliverables

| Deliverable | Description | Status |
|---|---|---|
| **Web Application** | Flask-based web app with upload, analyse, and result views | In Development |
| **Trained CNN Model** | Custom CNN trained on CASIA v1.0/v2.0, saved as `.keras` | In Development |
| **Trained MobileNetV2 Model** | Fine-tuned MobileNetV2 transfer learning model | In Development |
| **ELA Visualisation Module** | Python module generating ELA difference images with amplification | In Development |
| **PDF Report Generator** | ReportLab/WeasyPrint module producing per-analysis PDF summaries | In Development |
| **Jupyter Notebooks** | Six exploratory and experimental notebooks (EDA, preprocessing, training, evaluation) | In Development |
| **Test Suite** | pytest suite covering API, ELA, file validation, models, preprocessing | In Development |
| **Full Documentation** | All documents under `docs/` covering requirements, architecture, and guides | In Development |

---

## 7. Technology Overview

| Component | Technology | Rationale |
|---|---|---|
| Web Framework | Flask 2.x | Lightweight, flexible, well-suited to ML model serving without boilerplate overhead |
| ML Framework | TensorFlow 2.x / Keras | Industry-standard, excellent Keras API, broad community support |
| Transfer Learning Base | MobileNetV2 (ImageNet weights) | Efficient, mobile-friendly architecture; pretrained weights accelerate convergence |
| Image Processing | OpenCV + Pillow | OpenCV for fast array operations; Pillow for JPEG quality-layer ELA manipulation |
| Data Handling | NumPy, Pandas | Standard scientific Python stack |
| Visualisation | Matplotlib | Training curves, confusion matrices, ELA colour maps |
| Frontend | Bootstrap 5 + Vanilla JS | Responsive grid, pre-built components, no heavy JS framework dependency |
| Report Generation | ReportLab / WeasyPrint | PDF generation from Python without external binaries |
| Testing | pytest + pytest-flask | Standard Python testing; flask test client for route testing |

---

## 8. Project Timeline Overview

| Week | Phase | Key Activities |
|---|---|---|
| **Week 1** | Planning & Setup | Requirements gathering, repository setup, environment configuration, dataset access |
| **Week 2** | Data Engineering | Dataset download and organisation, EDA notebooks, preprocessing pipeline, train/val/test split |
| **Week 3** | Model Development | ELA implementation, custom CNN architecture and training, baseline evaluation |
| **Week 4** | Transfer Learning | MobileNetV2 fine-tuning, Grad-CAM experiments, model comparison |
| **Week 5** | Web Application | Flask routes, templates, ELA visualisation integration, PDF report generation |
| **Week 6** | Testing & Docs | pytest suite, final model evaluation, full documentation, project submission |

---

## 9. Team Roles

| Role | Responsibilities | Skills Required |
|---|---|---|
| **ML Engineer** | Design and train CNN and MobileNetV2 models; implement model evaluation pipeline; manage `src/models/` and `src/training/` | TensorFlow/Keras, model fine-tuning, Python |
| **Backend Developer** | Build Flask application, routes, services, and API; integrate trained models into the prediction pipeline; implement PDF report generation | Flask, Python, REST APIs, file handling |
| **Frontend Developer** | Design and implement HTML/CSS/JS templates using Bootstrap 5; build upload interface and results dashboard; ensure mobile responsiveness | HTML, CSS, Bootstrap 5, JavaScript, Jinja2 |
| **Data Engineer** | Organise and validate the CASIA dataset; implement preprocessing pipeline (resizing, normalisation, augmentation); manage `src/data/` and `src/preprocessing/` | Python, Pandas, NumPy, OpenCV, Pillow |

> [!NOTE]
> In a team of four, roles may overlap. Each member is expected to contribute to testing and documentation for their own modules.

---

## 10. Success Criteria

The project is considered successful when **all** of the following criteria are met:

1. ✅ The web application starts without errors and is accessible at `http://localhost:5000`.
2. ✅ A user can upload a JPG or PNG image, receive a prediction, and view an ELA visualisation within **10 seconds**.
3. ✅ At least one trained model achieves **≥ 75% accuracy** on the CASIA test split (preliminary target; will be updated when training is complete).
4. ✅ The ELA visualisation is generated and displayed correctly for all supported file types.
5. ✅ A PDF report can be downloaded successfully for every completed analysis.
6. ✅ Invalid files (wrong format, over 16 MB, corrupted) are rejected with a clear, user-friendly error message.
7. ✅ The pytest test suite passes with **≥ 80% code coverage** across the `src/` package.
8. ✅ All documentation in `docs/` is complete and accurately reflects the implemented system.

---

## 11. Known Limitations and Disclaimers

> [!IMPORTANT]
> These limitations must be clearly communicated to any user of this system.

| Limitation | Detail |
|---|---|
| **ELA is not proof of tampering** | Error Level Analysis reveals JPEG compression artefacts, which *may* correlate with manipulation. It produces false positives on legitimately re-saved images and false negatives on sophisticated edits. ELA output is a visual aid, not conclusive evidence. |
| **Preliminary screening only** | The model's prediction is a probabilistic estimate, not a forensic determination. It should be treated as a first-pass flag, not a verdict. |
| **Training data bias** | Models are trained exclusively on CASIA v1.0 and v2.0, which contain primarily JPEG images at specific resolutions. Performance on images from different cameras, compression pipelines, or social media re-encoding may degrade. |
| **Copy-move detection accuracy** | Copy-move forgeries involving rotation, scaling, or blurring of the copied region are harder to detect. Detection accuracy varies by manipulation sophistication. |
| **No localisation output** | The system classifies the entire image as authentic or tampered but does **not** produce a pixel-level mask indicating which region was manipulated. |
| **Image quality dependency** | Heavily compressed, downscaled, or screenshot images may yield unreliable ELA output because prior compression history is unknown. |
| **Not for legal use** | Results from this system are unsuitable for use as evidence in legal, journalistic, or professional forensic contexts. |
