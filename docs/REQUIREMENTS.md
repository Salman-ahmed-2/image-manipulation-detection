# Requirements Specification: Image Manipulation Detection System

## 1. Document Overview
This document consolidates the complete functional, non-functional, interface, and environmental requirements for the **Image Manipulation Detection System Using Deep Learning**. These requirements define the authoritative scope for academic evaluation and implementation by the engineering team.

---

## 2. Functional Requirements Summary

| Requirement ID | Module / Area | Description | Priority |
| :--- | :--- | :--- | :--- |
| **FR-001** | Input Ingestion | File upload interface supporting drag-and-drop and standard file-browser selection | High (Mandatory) |
| **FR-002** | Security & Validation | Client- and server-side file validation (format whitelist, MIME check, 16MB cap) | High (Mandatory) |
| **FR-003** | Image Preprocessing | Aspect-safe loading, RGB standardisation, resizing (224x224), tensor normalization | High (Mandatory) |
| **FR-004** | Custom CNN Classifier | Binary inference (Authentic vs. Potentially Manipulated) via trained Custom CNN | High (Mandatory) |
| **FR-005** | MobileNetV2 Classifier | Binary inference via fine-tuned MobileNetV2 transfer learning model | High (Mandatory) |
| **FR-006** | Confidence Reporting | Probability score calculation and calibrated percentage display | High (Mandatory) |
| **FR-007** | ELA Map Generation | Calculation of recompression residual differences with 10x brightness scaling | High (Mandatory) |
| **FR-008** | Forensic Visualizer | Synchronized side-by-side display of original uploaded image and ELA output | High (Mandatory) |
| **FR-009** | Diagnostic Dashboard | Responsive Bootstrap dashboard rendering verdict, badge, metrics, and ELA | High (Mandatory) |
| **FR-010** | PDF Report Generator | Downloadable multi-page PDF forensic report summarizing analysis and disclaimers | High (Mandatory) |
| **FR-011** | Model Switcher | Runtime or configuration toggle allowing selection of CNN or MobileNetV2 | Medium (Mandatory) |
| **FR-012** | Ephemeral File Cleanup | Session-scoped temporary storage purge upon report completion or timeout | High (Mandatory) |
| **FR-013** | Exception Handling | Structured user feedback on invalid payloads, corrupted images, or memory limits | High (Mandatory) |
| **FR-014** | Grad-CAM Interpretability| Heatmap localization highlighting salient CNN activation regions | Low (Optional) |
| **FR-015** | Comparative Benchmark View| Development dashboard contrasting CNN vs. MobileNetV2 side-by-side metrics | Low (Optional) |

---

## 3. Non-Functional Requirements Summary

| Requirement ID | Category | Metric / Specification | Priority |
| :--- | :--- | :--- | :--- |
| **NFR-001** | Performance (Latency) | End-to-end analysis (upload to dashboard render) < 5.0 seconds on standard CPU | High |
| **NFR-002** | Throughput & Memory | Single image processing memory overhead < 500MB RAM per worker thread | High |
| **NFR-003** | File Size Boundary | Maximum payload constraint of 16 megabytes (MB) strictly enforced by WSGI | High |
| **NFR-004** | File Format Whitelist | Strict acceptance restricted to JPEG (`.jpg`, `.jpeg`) and PNG (`.png`) | High |
| **NFR-005** | Data Privacy | Zero persistent database storage; all temp files purged within 30 minutes | Critical |
| **NFR-006** | Usability & Responsiveness| 100% responsive interface across desktop (1920x1080) and mobile (375x667) | Medium |
| **NFR-007** | Code Quality & Standards | Google Python docstrings, full PEP 8 conformance, typing annotations | High |
| **NFR-008** | Test Coverage | Minimum 80% line coverage across all `src/` modules verified via pytest | High |
| **NFR-009** | Portability | Runs deterministically on Linux, macOS, and Windows under Python 3.11 | High |
| **NFR-010** | Legal / Ethical Transparency| Mandatory forensic disclaimer attached to all web views and generated reports | Critical |

---

## 4. Hardware and Software Specifications

### 4.1 Minimum Development Environment
- **Operating System:** Linux (Ubuntu 22.04+ LTS recommended), macOS (12+), or Windows 11 with WSL2.
- **Python Runtime:** Python 3.11.x (CPython 64-bit).
- **CPU:** Quad-core x86_64 or Apple Silicon ARM processor.
- **System Memory (RAM):** 8 GB minimum (16 GB strongly recommended for dataset splitting).
- **Disk Storage:** 25 GB free disk space (to store CASIA v1/v2 raw and processed subsets).
- **Training Acceleration (Optional for Dev, Required for Training):** NVIDIA GPU with CUDA compute capability 7.0+ (T4, RTX 3060+) or Google Colab T4 GPU instance.

### 4.2 Production / Demonstration Host Environment
- **Runtime:** Single-node lightweight server or local workstation.
- **CPU:** Dual-core 2.0 GHz x86_64.
- **RAM:** 4 GB system memory.
- **Network:** Standard broadband HTTP/HTTPS (Port 5000 or 8080).
- **Model Ingestion:** Models loaded once into process RAM at initialization (~150MB memory footprint for MobileNetV2, ~35MB for Custom CNN).

---

## 5. External Dependencies and Interfaces
- **Deep Learning Framework:** TensorFlow 2.15+ / Keras 3.x.
- **Computer Vision & Image I/O:** Pillow (PIL) 10.x, OpenCV (headless) 4.8+.
- **Scientific Computing:** NumPy 1.24+, Pandas 2.1+, scikit-learn 1.3+.
- **Web Framework:** Flask 3.0+ with Werkzeug utilities.
- **PDF Generation Engine:** `fpdf2` 2.7+.
- **Frontend Assets:** Bootstrap 5.3 CDN (CSS & JS bundle), Bootstrap Icons.
