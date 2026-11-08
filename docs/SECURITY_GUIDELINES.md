# Security & Reliability Guidelines

## 1. Security Overview
The **Image Manipulation Detection System** is designed with security, privacy, and defensive engineering principles appropriate for an academic AI/ML web application processing untrusted user input files.

---

## 2. Secure File Upload Strategy

### 2.1 File Size Enforcement
- Maximum upload request body is capped at **16 Megabytes** (`Config.MAX_CONTENT_LENGTH = 16 * 1024 * 1024`).
- Web server WSGI layer (Werkzeug) drops oversized requests before buffering to disk, throwing HTTP `413 Request Entity Too Large`.

### 2.2 Extension Whitelist Validation
- Only the following lowercase extensions are accepted: `.jpg`, `.jpeg`, `.png`.
- Requests with missing extensions, double extensions (`image.php.jpg`), or unlisted formats are rejected immediately with HTTP `400 Bad Request`.

### 2.3 Binary Magic-Byte Inspection
File extensions are untrusted metadata. To prevent executable payload injection or polyglot file attacks, the file validator checks binary header magic bytes:
- **JPEG Signature:** Starts with `FF D8 FF`
- **PNG Signature:** Starts with `89 50 4E 47 0D 0A 1A 0A`
- If magic bytes do not match expected image headers, the file is rejected with `ValidationError("Invalid image signature")`.

### 2.4 Path Traversal Defense & Filename Sanitization
- User-supplied filenames are never used directly as filesystem paths.
- Filenames are sanitized via `werkzeug.utils.secure_filename()`.
- A UUID4 prefix is attached to guarantee uniqueness and prevent directory traversal exploits (`../../etc/passwd`):
  ```python
  safe_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
  ```

---

## 3. Data Privacy and Ephemeral State

### 3.1 Zero Permanent Storage Policy
- No user-uploaded image is permanently retained on disk.
- No database persistence layer is attached to the application.
- User files exist exclusively in isolated session temporary directories:
  `temp/uploads/<session_id>/`

### 3.2 Automated Session Purge
- Session directories are cleaned up in three scenarios:
  1. Immediately upon the user downloading their PDF analysis report.
  2. When the user clicks "Analyze Another Image".
  3. Via scheduled sweep script (`scripts/cleanup.py`) that purges temporary directories older than 30 minutes.

---

## 4. Deep Learning Model Security

### 4.1 Model Weight Integrity
- Pretrained `.keras` / `.h5` model weights are stored in read-only local directories (`artifacts/models/`).
- Models are loaded once at server initialization.
- No endpoint allows dynamic model loading, code serialization, or remote weight fetching.

### 4.2 Resource Exhaustion Defense (DoS Mitigation)
- Image dimensions are capped before processing.
- PIL decompression bomb protection is maintained (`Image.MAX_IMAGE_PIXELS = 50_000_000`) to prevent ZIP/image bomb attacks that could exhaust system RAM.

---

## 5. Defensive Exception Architecture

| Exception Class | Trigger Condition | HTTP Status | Log Severity |
| :--- | :--- | :--- | :--- |
| `ValidationError` | Missing file, bad extension, invalid magic bytes | 400 Bad Request | Warning |
| `PayloadTooLargeError` | File size exceeds 16 MB | 413 Payload Too Large | Warning |
| `ImageCorruptError` | Truncated byte stream, decoding failure | 400 Bad Request | Warning |
| `ModelInferenceError` | Tensor shape mismatch, out of memory | 500 Internal Error | Error |
| `ReportGenerationError`| Font missing, PDF write error | 500 Internal Error | Error |
