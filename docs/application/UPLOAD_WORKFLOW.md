# Image Upload Workflow & Lifecycle Specification

## 1. Upload Processing Pipeline
The upload pipeline provides defense-in-depth across client, WSGI network layer, validation utilities, and ephemeral disk storage.

```mermaid
flowchart TD
    User["User selects image.jpg (3.2MB)"] --> UI["Client JavaScript File Check"]
    UI -->|Valid .jpg < 16MB| Send["POST /analyze (multipart/form-data)"]
    Send --> WSGI["Werkzeug WSGI Layer"]
    
    WSGI --> CheckLen{"Request Content-Length <= 16MB?"}
    CheckLen -->|No| HTTP413["Throw HTTP 413: Payload Too Large"]
    CheckLen -->|Yes| ParsePart["Parse multipart boundaries"]
    
    ParsePart --> ValFn["src/utils/file_validator.py"]
    ValFn --> ExtCheck{"Extension in {jpg, jpeg, png}?"}
    ExtCheck -->|No| HTTP400_Ext["Throw HTTP 400: Invalid Extension"]
    ExtCheck -->|Yes| MagicCheck{"Magic Bytes Match JPEG/PNG Header?"}
    MagicCheck -->|No| HTTP400_Magic["Throw HTTP 400: Spoofed Header Signature"]
    MagicCheck -->|Yes| Sanitize["Sanitize filename via secure_filename()"]
    
    Sanitize --> MakeDir["Create temp/uploads/<session_id>/"]
    MakeDir --> WriteDisk["Write file: <uuid>_orig.jpg"]
    WriteDisk --> Svc["Forward path to DetectionService"]
```

---

## 2. Directory Layout & Isolation
Every upload request is isolated into an independent session directory:
```
temp/uploads/
└── 7c9e6679-7425-40de-944b-e07fc1f90ae7/
    ├── orig_sample.jpg
    └── ela_sample.png
```
This guarantees zero cross-talk between concurrent user requests and allows atomic directory removal upon completion.
