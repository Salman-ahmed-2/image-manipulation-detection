# Workflow Diagrams

## 1. Development & Experimentation Workflow
This workflow illustrates how the engineering team advances through dataset ingestion, model training, evaluation, and application packaging across the 6-week project lifecycle.

```mermaid
flowchart TD
    subgraph DataEngineering["Phase 1: Dataset Pipeline (Weeks 1-2)"]
        W1["Ingest Raw CASIA v1 & v2 Images"] --> W2["Scan & Parse Filename Tags (Au_, Tp_S_, Tp_D_)"]
        W2 --> W3["Filter Corrupt & Truncated Files"]
        W3 --> W4["Group-Aware Split (70% Train / 15% Val / 15% Test)"]
        W4 --> W5["Generate Metadata CSVs (Inventory, Labels, Splits)"]
    end

    subgraph ModelDevelopment["Phase 2: Deep Learning Experiments (Weeks 3-4)"]
        W5 --> M1["Custom CNN Pipeline (Train from Scratch)"]
        W5 --> M2["MobileNetV2 Pipeline (Transfer Learning)"]
        M1 --> M3["Hyperparameter Tuning & Callbacks (EarlyStopping, Checkpoint)"]
        M2 --> M4["Two-Stage Training: Feature Extraction -> Fine-Tuning"]
        M3 --> M5["Model Evaluation on Validation Split"]
        M4 --> M5
        M5 --> M6["Final Evaluation on Isolated Test Split"]
        M6 --> M7["Export Production Weights (.keras / .h5) to artifacts/models/"]
    end

    subgraph ForensicsEngineering["Phase 3: Image Forensics (Week 2)"]
        W1 --> E1["Design ELA Recompression Algorithm"]
        E1 --> E2["Calibrate JPEG Quality (90) & Enhancement Factor (10x)"]
        E2 --> E3["Integrate Pillow Differential Logic into src/preprocessing/"]
    end

    subgraph WebIntegration["Phase 4: Flask Web Integration (Weeks 4-5)"]
        M7 --> App["Flask Application Core (app.py)"]
        E3 --> App
        App --> Blueprints["Mount Routes (main_routes, detection_routes)"]
        Blueprints --> UI["Wire Bootstrap 5 UI & Templates"]
        UI --> PDF["Integrate FPDF Forensic PDF Report Service"]
    end

    subgraph QualityAssurance["Phase 5: Verification & Delivery (Weeks 5-6)"]
        App --> T1["Execute Unit & Integration Test Suites (pytest)"]
        T1 --> T2["Verify Performance (< 5s Latency, Zero Data Leakage)"]
        T2 --> T3["Deliver University Submission & Live Demo"]
    end
```

---

## 2. Server Startup & Request Lifecycle Workflow

```mermaid
flowchart LR
    Start(["flask run / python run.py"]) --> Cfg["Load config.py (Constants, Paths)"]
    Cfg --> LoadModels["Initialize model_loader.py (Load Keras Models to Process RAM)"]
    LoadModels --> VerifyWeights{"Model Weights Present?"}
    VerifyWeights -->|No| WarnStub["Log Warning: Run in Mock/Fallback Inference Mode"]
    VerifyWeights -->|Yes| ConfirmReady["Confirm Ready on Port 5000"]
    WarnStub --> ConfirmReady
    ConfirmReady --> Listen["Listen for HTTP Requests (Worker Pool)"]
```
