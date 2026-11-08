# Database Design & State Management Architecture

## 1. Architectural Decision: No Persistent Database
The **Image Manipulation Detection System** intentionally eliminates any relational (e.g. PostgreSQL, MySQL, SQLite) or NoSQL (e.g. MongoDB) database.

### 1.1 Rationale for Zero Database Architecture
1. **User Privacy & Forensic Ethics:** Forensic screening tools must minimize exposure to private user imagery. By avoiding persistent database storage, the application eliminates user data leak risks.
2. **Simplified University Scope:** Removing database setup, migrations, ORM layers, and connection pooling keeps the 4–6 week project focused on deep learning model performance, ELA algorithms, and clean UI delivery.
3. **Stateless Scalability:** Web requests are decoupled from database locks and connection limits. Each analysis execution runs independently.

---

## 2. In-Memory and Ephemeral State Management

### 2.1 Session-Scoped Temporary Storage
The application utilizes an ephemeral filesystem structure managed by Flask's secure client-side cookie session:

```
temp/
└── uploads/
    └── <session_id_uuid>/
        ├── <uuid>_original.jpg     # Validated user upload
        ├── <uuid>_ela.png          # Generated ELA difference visualization
        └── forensic_report.pdf     # Transient generated PDF report
```

### 2.2 Flask Session Lifecycle
- Upon first request, Flask generates a cryptographically signed cookie storing a unique `session_id` (UUID4).
- When `/analyze` is called, the uploaded image and ELA output are stored under `temp/uploads/<session_id>/`.
- The analysis result metadata (verdict, confidence score, model name, timestamp) is temporarily stored in Flask's signed session dictionary.
- When `/report/<session_id>` is invoked, the service loads the session metadata and stored image paths, streams the PDF, and schedules directory cleanup.

### 2.3 Cleanup Mechanism
A cleanup routine in `src/utils/file_validator.py` and `scripts/cleanup.py` monitors directory timestamps:
- Any directory inside `temp/uploads/` with a modified time older than 30 minutes (`Config.TEMP_FILE_EXPIRY = 1800`) is automatically purged.
