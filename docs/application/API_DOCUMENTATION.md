# RESTful Application Programming Interface (API) Documentation

## 1. API Architecture Overview
The web application exposes both HTML-rendered routes (for browser sessions) and structured JSON endpoints (for automated client interactions and health checks). All endpoints are managed through Flask Blueprints:
- `main_routes` (mounted at `/`): Home, about, and static views.
- `detection_routes` (mounted at `/`): File upload, model execution, and PDF report delivery.

---

## 2. Endpoint Specifications

### 2.1 GET `/health`
- **Description:** Verifies service health, loaded model status, and runtime environment.
- **Request Headers:** `Accept: application/json`
- **Response Format:** JSON
- **Success Response (HTTP 200 OK):**
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "models_loaded": {
      "cnn": true,
      "mobilenet": true
    },
    "active_model": "mobilenet",
    "uptime_seconds": 1245
  }
  ```

---

### 2.2 POST `/analyze`
- **Description:** Ingests an uploaded image, executes file validation, deep learning classification, and ELA map generation.
- **Request Format:** `multipart/form-data`
- **Parameters:**
  - `image` (file, required): Binary JPEG or PNG image stream (Max 16 MB).
  - `model` (string, optional): Target model architecture (`mobilenet` or `cnn`). Defaults to `Config.ACTIVE_MODEL`.
- **Browser Interaction:** When submitted from browser forms, responds with a 302 redirect or directly renders `result.html`.
- **API Client Interaction (JSON mode when `Accept: application/json` is sent):**
  - **Success Response (HTTP 200 OK):**
    ```json
    {
      "status": "success",
      "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "prediction": {
        "label": "Potentially Manipulated",
        "verdict_code": 1,
        "confidence": 93.42,
        "raw_probability": 0.9342,
        "model_used": "mobilenet_v2"
      },
      "artifacts": {
        "original_image_url": "/static/temp/a1b2c3d4/orig.jpg",
        "ela_image_url": "/static/temp/a1b2c3d4/ela.png"
      },
      "disclaimer": "ELA visualization is an investigative aid. Bright regions indicate potential compression inconsistencies and do not constitute definitive proof of digital manipulation."
    }
    ```
  - **Error Response (HTTP 400 Bad Request):**
    ```json
    {
      "status": "error",
      "error_code": "INVALID_FILE_TYPE",
      "message": "Only JPEG and PNG images are supported. File header did not match expected magic bytes."
    }
    ```
  - **Error Response (HTTP 413 Payload Too Large):**
    ```json
    {
      "status": "error",
      "error_code": "PAYLOAD_TOO_LARGE",
      "message": "Uploaded file exceeds the maximum permissible limit of 16 MB."
    }
    ```

---

### 2.3 GET `/report/<session_id>`
- **Description:** Compiles and streams a downloadable forensic PDF report for the specified session.
- **Parameters:**
  - `session_id` (string, required in path): Active UUID4 session identifier.
- **Response Format:** Binary stream
- **Response Headers:**
  - `Content-Type: application/pdf`
  - `Content-Disposition: attachment; filename="forensic_report_<session_id>.pdf"`
- **Error Response (HTTP 404 Not Found):**
  ```json
  {
    "status": "error",
    "error_code": "SESSION_EXPIRED",
    "message": "Session expired or files were already purged. Please re-run analysis."
  }
  ```
