# Project Scope: Image Manipulation Detection System Using Deep Learning

**Document Type:** Project Scope Definition
**Version:** 1.0
**Last Updated:** November 2026

---

## 1. Scope Overview

This document formally defines the boundaries of the **Image Manipulation Detection System** semester project. It specifies which features will be built, which are explicitly excluded, the constraints the team operates under, and the assumptions that underpin planning decisions.

The system is a **Flask-based web application** that accepts uploaded images and produces a binary classification result (Authentic / Tampered) using deep learning models trained on the CASIA forgery detection dataset. It includes an Error Level Analysis (ELA) visualisation and a downloadable PDF summary report. The system is designed for **preliminary, non-authoritative screening** in an academic context.

---

## 2. In-Scope Features

The following features are committed to for the final project submission. Priority levels are assigned to guide development ordering.

| ID | Feature | Description | Priority |
|---|---|---|---|
| F-01 | Image Upload Interface | Drag-and-drop and file-picker upload on the home page | High |
| F-02 | File Format Validation | Accept only JPG, JPEG, PNG; reject all other MIME types using magic byte inspection | High |
| F-03 | File Size Enforcement | Reject uploads exceeding 16 MB; return user-friendly error message | High |
| F-04 | Secure Filename Handling | Sanitise uploaded filenames using `werkzeug.utils.secure_filename`; use UUID-based internal names | High |
| F-05 | Image Preprocessing Pipeline | Resize, normalise pixel values, and prepare image tensors for model inference | High |
| F-06 | Custom CNN Classification | Run inference using the trained custom CNN model; return class label and softmax probabilities | High |
| F-07 | MobileNetV2 Classification | Run inference using the trained MobileNetV2 fine-tuned model | High |
| F-08 | Confidence Score Display | Show per-class probability as a percentage and progress bar in the results view | High |
| F-09 | ELA Generation | Compute Error Level Analysis difference image from the uploaded file | High |
| F-10 | ELA Visualisation | Display amplified ELA output as a colour-mapped image alongside the original | High |
| F-11 | Results Dashboard | Single-page results view combining prediction, confidence, and ELA side by side | High |
| F-12 | PDF Report Download | Generate and serve a PDF summary report (image thumbnail, prediction, confidence, ELA) | High |
| F-13 | Image Preview | Show a thumbnail of the uploaded image before analysis begins | Medium |
| F-14 | Error Handling UI | User-friendly error pages for invalid files, server errors, and timeout conditions | High |
| F-15 | Temporary File Cleanup | Automatically delete uploaded files and ELA artefacts at the end of each session | High |
| F-16 | Model Selection (Optional) | Allow user to choose between CNN and MobileNetV2 from the upload form | Medium |
| F-17 | Grad-CAM Visualisation (Stretch) | Generate class activation maps to show which image regions influenced the prediction | Low |
| F-18 | Analysis History (Stretch) | Display a session-scoped list of previously analysed images and their results | Low |
| F-19 | Model Comparison Dashboard (Stretch) | Side-by-side display of CNN vs MobileNetV2 results for the same image | Low |
| F-20 | About / Documentation Page | Static web page explaining the system, its limitations, and how to interpret results | Medium |

---

## 3. Out-of-Scope Features

The following features are **explicitly excluded** from this project. They will not be implemented, partially implemented, or stubbed out.

| Excluded Feature | Reason for Exclusion |
|---|---|
| **User authentication and login system** | Adds significant complexity (session management, password hashing, account recovery) disproportionate to a 4–6 week academic project |
| **Persistent user database** | No user data is stored; there is no need for a relational or document database beyond optional in-memory session history |
| **Payment or subscription system** | The system is free, open-source, and academic; no commercial functionality is required |
| **Cloud hosting and deployment pipeline** | Infrastructure provisioning (AWS, GCP, Azure) and CI/CD pipeline setup are out of scope; the app runs locally |
| **Real-time video analysis** | Video forensics requires frame extraction, temporal analysis, and far greater computational resources than available within scope |
| **Audio or document forensics** | The system is image-only; audio deepfake detection and PDF forensics are separate research areas |
| **RAW, TIFF, BMP, WebP, HEIC format support** | CASIA dataset is JPEG-centric; ELA is most reliable on JPEG images; added format support increases complexity |
| **Pixel-level forgery mask output** | Region localisation (producing a segmentation mask of tampered pixels) is a significantly harder task beyond binary classification |
| **Admin dashboard** | No administrative interface, user management, or analytics dashboard will be built |
| **Multi-language / internationalisation (i18n)** | UI will be in English only |
| **API rate limiting and authentication** | The Flask API is intended for local/classroom use, not public deployment where rate limiting would be essential |
| **Mobile app (iOS/Android)** | The responsive Bootstrap UI covers mobile browsers; a native app is not in scope |
| **Automated retraining pipeline** | Model retraining in response to new data or user feedback is not implemented |
| **Professional forensic certification output** | The system will not produce output suitable for legal, journalistic, or certified forensic use |

---

## 4. Constraints

### 4.1 Time Constraint

| Constraint | Detail |
|---|---|
| Total project duration | 4–6 weeks from project brief to submission |
| Weekly team meeting cadence | Minimum 2 meetings per week (planning + review) |
| Submission deadline | Fixed by course schedule; no extensions assumed |

### 4.2 Team Constraint

| Constraint | Detail |
|---|---|
| Team size | 4 members |
| All members are students | No prior professional experience in production ML deployment assumed |
| Part-time commitment | Team members balance coursework across multiple subjects simultaneously |

### 4.3 Hardware Constraint

| Constraint | Detail |
|---|---|
| Development hardware | Standard student laptops (8–16 GB RAM, CPU-only training is slow) |
| GPU access | Google Colab (free tier) used for model training; T4/V100 GPU available for limited hours |
| Local inference | Inference at request time must run on CPU within 10 seconds for a single image |
| Storage | CASIA v2.0 is ~5 GB; local SSD space required; dataset not stored in Git |

### 4.4 Software Constraint

| Constraint | Detail |
|---|---|
| Python version | 3.11 (pinned in `.python-version` and `requirements.txt`) |
| TensorFlow version | 2.x; must be compatible with Python 3.11 and local CUDA version |
| Operating system | Linux primary; macOS and Windows supported via virtual environment |

---

## 5. Assumptions

1. **Dataset availability:** The CASIA v1.0 and v2.0 datasets can be downloaded by all team members from the official source (forensics.idealtest.org) or a community mirror (Kaggle / HuggingFace). Dataset access is not guaranteed by the institution.
2. **Ground-truth masks:** Binary ground-truth masks from the `namtpham` GitHub repositories are available and correctly aligned with the CASIA images after applying the rename/correction logs.
3. **Google Colab access:** Each team member has a Google account and can use Google Colab for GPU-accelerated model training, subject to free-tier session limits.
4. **Pre-trained MobileNetV2 weights:** ImageNet pretrained weights for MobileNetV2 are downloadable via the Keras Applications API without restriction.
5. **Flask development server is sufficient:** For demonstration and submission purposes, the Flask built-in development server is acceptable. A production WSGI server (gunicorn/uWSGI) is not required.
6. **Single-user concurrent access:** The application is assumed to serve one user at a time for academic demonstration. No load balancing or concurrency management is required.
7. **ELA reliability on CASIA images:** Because CASIA images are primarily JPEG, ELA will be a valid and demonstrable technique on the dataset images.

---

## 6. Dependencies

### 6.1 External Dependencies

| Dependency | Type | Risk | Mitigation |
|---|---|---|---|
| CASIA dataset access | External data source | Medium — official site may be slow or require registration | Use community mirrors (Kaggle, HuggingFace); document fallback |
| MobileNetV2 pretrained weights | Internet download (Keras API) | Low — widely cached, rarely unavailable | Pre-download and store locally in `artifacts/models/` |
| Google Colab GPU quota | Cloud compute resource | Medium — free tier has session time limits | Train in batches; checkpoint models frequently; consider Kaggle Notebooks as fallback |
| PyPI package availability | Internet (pip) | Low | Pin all versions in `requirements.txt`; use `pip freeze` for exact reproducibility |

### 6.2 Internal Dependencies

| Component | Depends On |
|---|---|
| `detection_routes.py` | `detection_service.py`, `ela_service.py`, `report_service.py` |
| `detection_service.py` | `model_loader.py`, `predictor.py`, `image_normalizer.py` |
| `ela_service.py` | `ela_generator.py` |
| `report_service.py` | Prediction result dict + ELA image path |
| `train_cnn.py` / `train_mobilenet.py` | `dataset_loader.py`, `augmentation.py`, `cnn_model.py` / `mobilenet_model.py` |

---

## 7. Boundaries — What This System Will NOT Claim or Guarantee

> [!CAUTION]
> These boundaries must be communicated clearly in the user interface and in any project presentation.

| Boundary | Explanation |
|---|---|
| **Will NOT guarantee detection accuracy on arbitrary images** | Model performance is characterised on CASIA test splits. Performance on images from other sources, cameras, or compression pipelines may differ significantly. |
| **Will NOT localise the tampered region** | The system outputs a binary image-level label. It does not produce bounding boxes, segmentation masks, or region-level forgery indicators. |
| **Will NOT detect all manipulation types** | The models are trained on splicing and copy-move forgeries. AI-generated imagery (GANs, diffusion models), retouching, lighting manipulation, and colour grading alterations are not reliably detected. |
| **Will NOT serve as legal evidence** | Output is NOT admissible as forensic evidence in legal proceedings, journalism, or professional verification workflows. |
| **Will NOT protect against adversarial examples** | The system has not been hardened against adversarial attacks. A sophisticated actor can craft images that deliberately fool the model. |
| **Will NOT retain user images after session ends** | Uploaded images and intermediate files are deleted at session close. The system makes no guarantees about data retention or recovery. |
