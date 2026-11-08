# Documentation Index

This directory contains all project documentation for the **Image Manipulation Detection System Using Deep Learning**. Documents are organised by topic. If you are new to the project, start with the **Start Here** section below.

---

## 🚀 Start Here

| Document | Why Read It |
|---|---|
| **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** | High-level description of the project: what it is, who it is for, and what it delivers. Read this first. |
| **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** | Step-by-step instructions for setting up the development environment on Linux, macOS, and Windows. |
| **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** | Coding standards, branch workflow, naming conventions, and contribution process for team members. |

---

## Root-Level Documents

| File | Description |
|---|---|
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | Complete project overview: problem, objectives, timeline, team roles, and success criteria. |
| [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) | Research background and motivation — why image manipulation detection matters and what gap this project addresses. |
| [PROJECT_OBJECTIVES.md](PROJECT_OBJECTIVES.md) | Primary, secondary, technical, research, and SMART objectives with measurable success metrics. |
| [PROJECT_SCOPE.md](PROJECT_SCOPE.md) | Detailed in-scope and out-of-scope feature list, project constraints, assumptions, and boundaries. |
| [REQUIREMENTS.md](REQUIREMENTS.md) | Master requirements index: summary tables of all functional (FR) and non-functional (NFR) requirements. |
| [FUNCTIONAL_REQUIREMENTS.md](FUNCTIONAL_REQUIREMENTS.md) | Detailed specification for FR-001 through FR-015 (upload, validation, preprocessing, detection, reporting). |
| [NON_FUNCTIONAL_REQUIREMENTS.md](NON_FUNCTIONAL_REQUIREMENTS.md) | Detailed specification for NFR-001 through NFR-010 (performance, security, usability, privacy). |
| [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) | Full environment setup: Python 3.11, virtual environment, dependencies, model weights, and first run. |
| [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) | System architecture narrative describing the layered design and component responsibilities. |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Complete Flask route reference with request/response schemas and example cURL calls. |
| [ELA_DOCUMENTATION.md](ELA_DOCUMENTATION.md) | Theory and implementation of Error Level Analysis: how it works, what it reveals, and its limitations. |
| [MODEL_DOCUMENTATION.md](MODEL_DOCUMENTATION.md) | Architecture diagrams and training details for the custom CNN and MobileNetV2 models. |
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | Coding conventions, Git workflow, docstring standards, and test-writing guidelines for contributors. |
| [USER_GUIDE.md](USER_GUIDE.md) | End-user instructions for uploading images, interpreting results, and downloading PDF reports. |
| [TESTING_STRATEGY.md](TESTING_STRATEGY.md) | Testing philosophy, test categories, coverage targets, and instructions for running pytest. |
| [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) | Honest statement of current limitations: ELA reliability, model generalisation, and disclaimer language. |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Solutions to common setup and runtime errors (dependency conflicts, CUDA issues, model load failures). |
| [SECURITY_GUIDELINES.md](SECURITY_GUIDELINES.md) | Security considerations for file uploads, filename handling, and temporary file management. |
| [DATABASE_DESIGN.md](DATABASE_DESIGN.md) | (If applicable) Design of any persistent storage for analysis history. |
| [DATA_FLOW.md](DATA_FLOW.md) | End-to-end data flow from image upload through preprocessing, prediction, and result display. |
| [DATASET_DOCUMENTATION.md](DATASET_DOCUMENTATION.md) | Additional CASIA dataset documentation covering labelling conventions and preprocessing decisions. |

---

## `dataset/` — Dataset Documentation

| File | Description |
|---|---|
| [dataset/DATASET_OVERVIEW.md](dataset/DATASET_OVERVIEW.md) | Comprehensive overview of CASIA v1.0 and v2.0: image counts, categories, file naming conventions, access links, ground-truth masks, and citation requirements. |

---

## `architecture/` — Architecture Diagrams

| File | Description |
|---|---|
| [architecture/system_architecture.md](architecture/system_architecture.md) | Full system architecture diagram showing Flask, src layers, and ML pipeline. |
| [architecture/component_diagram.md](architecture/component_diagram.md) | Component-level breakdown of the backend modules and their dependencies. |
| [architecture/workflow_diagram.md](architecture/workflow_diagram.md) | Step-by-step workflow diagram from image upload to result display. |

---

## `decisions/` — Architecture Decision Records (ADRs)

Architecture Decision Records document *why* specific technical choices were made, capturing context and trade-offs for future reference.

| File | Description |
|---|---|
| [decisions/ADR-001-technology-stack.md](decisions/ADR-001-technology-stack.md) | Rationale for choosing Python/Flask over Django or FastAPI; TensorFlow over PyTorch. |
| [decisions/ADR-002-dataset-selection.md](decisions/ADR-002-dataset-selection.md) | Justification for using CASIA v1.0 and v2.0 over other forensic image datasets. |
| [decisions/ADR-003-model-selection.md](decisions/ADR-003-model-selection.md) | Trade-off analysis of custom CNN vs MobileNetV2 transfer learning for this task. |
| [decisions/ADR-004-ela-implementation.md](decisions/ADR-004-ela-implementation.md) | Design decisions around the ELA pipeline: quality factor, amplification, and colour-mapping. |

---

## `progress/` — Project Progress Tracking

| File | Description |
|---|---|
| [progress/TASK_TRACKER.md](progress/TASK_TRACKER.md) | Active task board: to-do, in-progress, and completed items per sprint/week. |
| [progress/DEVELOPMENT_LOG.md](progress/DEVELOPMENT_LOG.md) | Chronological log of development decisions, blockers, and resolutions. |
| [progress/CHANGELOG.md](progress/CHANGELOG.md) | Version-by-version record of changes following Keep a Changelog conventions. |

---

> [!TIP]
> All documentation is written in GitHub Flavored Markdown. Mermaid diagram blocks in the architecture documents render natively on GitHub and in VS Code with the Mermaid extension.

> [!NOTE]
> Documents marked **[PROPOSED]** or **[PENDING DECISION]** contain content that has not yet been finalised by the team and should be reviewed before submission.
