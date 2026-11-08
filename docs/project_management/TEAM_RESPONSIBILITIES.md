# Team Responsibilities & RACI Governance Matrix

## 1. 4-Person Student Team Organization

| Team Member | Primary Role | Core Ownership | Secondary Support |
| :--- | :--- | :--- | :--- |
| **Member 1 (Lead)** | Machine Learning Engineer | Model architectures (CNN, MobileNetV2), training pipelines, evaluation metrics | Preprocessing optimization |
| **Member 2** | Backend & Systems Engineer | Flask app factory, service layer (`detection_service`, `report_service`), API routing | Model deployment & loading |
| **Member 3** | Data & Forensics Engineer | CASIA ingestion, group-aware splitting, ELA recompression algorithms, data quality | Data augmentation |
| **Member 4** | Frontend & QA Engineer | Bootstrap 5 UI, Jinja2 templates, JavaScript upload UX, pytest test suites | Documentation & presentation |

---

## 2. RACI Responsibility Assignment Matrix

- **R (Responsible):** The role directly authoring the code or asset.
- **A (Accountable):** The individual with final approval authority.
- **C (Consulted):** Team members providing technical input or reviews.
- **I (Informed):** Team members updated on progress and changes.

| Deliverable / Module | ML Engineer (M1) | Backend Dev (M2) | Data/Forensics (M3) | Frontend/QA (M4) |
| :--- | :---: | :---: | :---: | :---: |
| **System Architecture & ADRs** | C | A | C | I |
| **Dataset Acquisition & Ingestion** | C | I | R / A | I |
| **Group-Aware Splitting Pipeline** | C | I | R / A | I |
| **ELA Algorithm Implementation** | C | C | R / A | I |
| **Custom CNN Model Training** | R / A | I | C | I |
| **MobileNetV2 Fine-Tuning** | R / A | C | I | I |
| **Flask Route & Service Layer** | C | R / A | I | C |
| **Bootstrap 5 UI & Templates** | I | C | I | R / A |
| **PDF Report Service (`fpdf2`)** | I | R / A | I | C |
| **Automated Testing Suite (pytest)**| C | C | C | R / A |
| **Project Documentation & Review**| C | C | C | R / A |
