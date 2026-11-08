# Sequence Diagrams

## 1. Complete Analysis & Report Generation Flow
This sequence diagram details the synchronous call hierarchy and message exchanges between the User Browser, Flask Route Layer, File Validator, Preprocessing Pipeline, Machine Learning Predictor, ELA Generator, and Report Generation Service.

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser
    participant Routes as web/routes/detection_routes.py
    participant Validator as src/utils/file_validator.py
    participant Preproc as src/preprocessing/image_loader.py
    participant Predictor as src/models/predictor.py
    participant Model as Keras Model (In-Memory)
    participant ELA as src/preprocessing/ela_generator.py
    participant Report as src/services/report_service.py

    User->>Routes: POST /analyze (multipart/form-data: image, model_choice)
    activate Routes

    Routes->>Validator: validate_upload(request.files['image'])
    activate Validator
    Validator->>Validator: Check extension, magic bytes, file size
    alt Validation Failure
        Validator-->>Routes: raise ValidationError("Invalid image header")
        Routes-->>User: HTTP 400 Bad Request (render error.html)
    else Validation Success
        Validator->>Validator: secure_filename() + assign UUID
        Validator-->>Routes: save to temp/uploads/<session_id>/orig.jpg
        deactivate Validator
    end

    par Machine Learning Inference
        Routes->>Preproc: load_and_preprocess("orig.jpg", target_size=(224,224))
        activate Preproc
        Preproc->>Preproc: Convert RGB, resize bicubic, normalize tensor
        Preproc-->>Routes: normalized_tensor (1, 224, 224, 3)
        deactivate Preproc

        Routes->>Predictor: predict(normalized_tensor, model_name)
        activate Predictor
        Predictor->>Model: forward_pass(normalized_tensor)
        activate Model
        Model-->>Predictor: raw_probability P in [0.0, 1.0]
        deactivate Model
        Predictor->>Predictor: compute_verdict_and_confidence(P)
        Predictor-->>Routes: dict(label="Potentially Manipulated", confidence=93.4)
        deactivate Predictor
    and Error Level Analysis Generation
        Routes->>ELA: generate_ela("orig.jpg", quality=90, scale=10)
        activate ELA
        ELA->>ELA: Recompress JPEG -> diff -> scale 10x -> save PNG
        ELA-->>Routes: "temp/uploads/<session_id>/ela.png"
        deactivate ELA
    end

    Routes->>Routes: Store results in session dictionary
    Routes-->>User: HTTP 200 OK (render result.html with metrics & ELA)
    deactivate Routes

    opt User Requests PDF Report
        User->>Routes: GET /report/<session_id>
        activate Routes
        Routes->>Report: generate_pdf_report(session_data, orig_path, ela_path)
        activate Report
        Report->>Report: Assemble FPDF canvas, inject photos, format disclaimers
        Report-->>Routes: pdf_byte_buffer
        deactivate Report
        Routes-->>User: HTTP 200 Stream (attachment; filename="forensic_report.pdf")
        Routes->>Validator: purge_session_temp_dir(session_id)
        deactivate Routes
    end
```
