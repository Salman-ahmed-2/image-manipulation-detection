# Master Task Tracker & Implementation Backlog

## 1. Backlog Status Legend
- 📝 **PLANNED:** Specified in documentation, awaiting scheduled week.
- ⚙️ **IN PROGRESS:** Under active implementation by assigned engineer.
- ✅ **COMPLETED:** Implemented, tested, reviewed, and merged.
- 🛑 **BLOCKED:** Dependent on prerequisite task completion.

---

## 2. Core Implementation Tasks

| Task ID | Component / Area | Task Summary | Assignee | Target Week | Status |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **TSK-01** | Documentation | Author comprehensive documentation suite | All | Week 1 | ✅ COMPLETED |
| **TSK-02** | Environment | Initialize Python 3.11 virtual environment & dependencies | M2 | Week 1 | ✅ COMPLETED |
| **TSK-03** | Dataset Ingestion | Ingest CASIA v1.0 and v2.0 image collections | M3 | Week 1-2 | 📝 PLANNED |
| **TSK-04** | Dataset Scripts | Build `scripts/prepare_dataset.py` with GroupShuffleSplit | M3 | Week 2 | 📝 PLANNED |
| **TSK-05** | Image Forensics | Implement `src/preprocessing/ela_generator.py` (Pillow) | M3 | Week 2 | 📝 PLANNED |
| **TSK-06** | Preprocessing | Implement `image_loader`, `image_resizer`, `image_normalizer` | M3 | Week 2 | 📝 PLANNED |
| **TSK-07** | Custom CNN | Build 4-block ConvNet in `src/models/cnn_model.py` | M1 | Week 3 | 📝 PLANNED |
| **TSK-08** | Training Script | Implement `src/training/train_cnn.py` with callbacks | M1 | Week 3 | 📝 PLANNED |
| **TSK-09** | CNN Training | Execute Colab training runs & save `cnn_model.keras` | M1 | Week 3 | 📝 PLANNED |
| **TSK-10** | MobileNetV2 | Build transfer learning model in `mobilenet_model.py` | M1 | Week 4 | 📝 PLANNED |
| **TSK-11** | Fine-Tuning | Execute 2-phase fine-tuning on Colab GPU | M1 | Week 4 | 📝 PLANNED |
| **TSK-12** | Model Evaluation | Benchmark CNN vs MobileNetV2 using `scripts/evaluate.py` | M1 | Week 4 | 📝 PLANNED |
| **TSK-13** | Model Serving | Implement `src/models/model_loader.py` & `predictor.py` | M2 | Week 4 | 📝 PLANNED |
| **TSK-14** | Backend Routes | Implement `web/routes/detection_routes.py` (`/analyze`) | M2 | Week 4 | 📝 PLANNED |
| **TSK-15** | Detection Service | Build `src/services/detection_service.py` | M2 | Week 4 | 📝 PLANNED |
| **TSK-16** | Report Service | Build `src/services/report_service.py` using `fpdf2` | M2 | Week 5 | 📝 PLANNED |
| **TSK-17** | Frontend Templates| Code `index.html`, `result.html`, `about.html`, `base.html` | M4 | Week 5 | 📝 PLANNED |
| **TSK-18** | Client JavaScript | Build drag-and-drop & live preview in `web/static/js/` | M4 | Week 5 | 📝 PLANNED |
| **TSK-19** | Testing Suite | Author unit & integration tests under `tests/` | M4 | Week 5 | 📝 PLANNED |
| **TSK-20** | Cleanup Daemon | Implement temp directory purge in `scripts/cleanup.py` | M2 | Week 5 | 📝 PLANNED |
| **TSK-21** | Final Verification| End-to-end UAT, performance profiling, final submission | All | Week 6 | 📝 PLANNED |
