# Project Timeline & Milestone Schedule (4–6 Weeks)

## 1. High-Level 6-Week Master Schedule

```mermaid
gantt
    title Image Manipulation Detection System Implementation Schedule
    dateFormat  YYYY-MM-DD
    section Week 1: Foundation
    Documentation & Architecture Review     :active, w1_1, 2026-11-09, 3d
    Environment & Dependency Setup          :w1_2, 2026-11-11, 2d
    Dataset Acquisition & Exploration       :w1_3, 2026-11-12, 4d
    section Week 2: Data & ELA
    Dataset Preparation & Split Scripts     :w2_1, 2026-11-16, 4d
    ELA Generator Implementation & Tests    :w2_2, 2026-11-18, 4d
    section Week 3: Custom CNN
    Custom CNN Model Architecture           :w3_1, 2026-11-23, 2d
    Custom CNN Training on Colab            :w3_2, 2026-11-25, 4d
    Custom CNN Evaluation                   :w3_3, 2026-11-28, 2d
    section Week 4: MobileNet & Backend
    MobileNetV2 Fine-Tuning                 :w4_1, 2026-11-30, 4d
    Model Comparison & Selection            :w4_2, 2026-12-03, 2d
    Flask Backend & Service Layer           :w4_3, 2026-12-01, 5d
    section Week 5: Frontend & Tests
    Bootstrap 5 Web Interface              :w5_1, 2026-12-07, 4d
    PDF Report Generation Service           :w5_2, 2026-12-09, 3d
    Full End-to-End Integration Testing     :w5_3, 2026-12-11, 3d
    section Week 6: Polish & Submission
    UAT & Bug Fixing                        :w6_1, 2026-12-14, 3d
    Final Report & Documentation Review     :w6_2, 2026-12-16, 3d
    Final University Presentation           :w6_3, 2026-12-18, 2d
```

---

## 2. Weekly Deliverables Breakdown

### Week 1: Project Setup, Dataset Acquisition & Exploration
- **Objectives:** Establish development repository, confirm Python 3.11 environment, inspect CASIA mirrors, and run exploratory data analysis (EDA).
- **Key Deliverable:** Verified dataset inventory and environment verification pass.

### Week 2: Dataset Preparation & Error Level Analysis (ELA)
- **Objectives:** Build `scripts/prepare_dataset.py`, generate group-aware 70/15/15 splits, and implement the core `ELAGenerator` class.
- **Key Deliverable:** Clean `data/metadata/*.csv` catalogs and verified ELA unit tests (`test_ela.py`).

### Week 3: Custom CNN Architecture & Baseline Training
- **Objectives:** Implement 4-block ConvNet in `src/models/cnn_model.py`, set up training loops with EarlyStopping and ModelCheckpointing on Google Colab.
- **Key Deliverable:** Checkpointed `cnn_model.keras` weights and training history plots.

### Week 4: MobileNetV2 Transfer Learning & Flask Backend Integration
- **Objectives:** Adapt MobileNetV2 with two-phase fine-tuning, compare models, and implement Flask application routes (`main_routes`, `detection_routes`).
- **Key Deliverable:** Checkpointed `mobilenet_model.keras` weights and functional `/analyze` backend route.

### Week 5: Frontend Interface, PDF Export & Integration Testing
- **Objectives:** Wire Bootstrap 5 UI templates (`index.html`, `result.html`), implement PDF report service with `fpdf2`, and execute pytest integration suite.
- **Key Deliverable:** Fully operational web application with live inference and downloadable PDF reports.

### Week 6: Quality Assurance, Documentation & University Submission
- **Objectives:** Conduct cross-browser testing, verify disclaimer coverage, finalize academic project reports, and prepare presentation slide decks.
- **Key Deliverable:** Final academic project submission and live demonstration.
