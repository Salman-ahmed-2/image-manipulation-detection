# [ISSUE #12] Flask Application Factory, Route Blueprints & API Endpoints

## 📌 Issue Metadata
- **Milestone:** M4 — Full Web Application & Reports
- **Phase:** Phase 5 (Model Serving & Backend)
- **Estimated Effort:** 4–5 hours
- **Labels:** `backend`, `flask`, `blueprints`, `routes`, `api`
- **Dependencies:** Issue #1 (`config.py`), Issue #10 (`model_loader.py`), Issue #11 (`detection_service.py`)
- **Blocks:** Issue #13 (Report Service), Issue #15 (Frontend Layout), Issue #16 (Results Dashboard)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a Senior Web Application Developer.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/application/BACKEND_DOCUMENTATION.md`
> 2. `docs/application/API_DOCUMENTATION.md`
> 3. `docs/application/UPLOAD_WORKFLOW.md`
> 4. `AGENTS.md` (Strict rules: App factory pattern in `app.py`, Blueprints in `web/routes/`, routes contain NO business logic, load models on startup only).

---

## 🎯 Objective & Context
Implement the Flask application factory in `app.py`, development entry point `run.py`, and route Blueprints under `web/routes/`. The web layer handles HTTP routing, multipart form uploads, template rendering, and RESTful JSON endpoints (`GET /health`, `POST /analyze`, `GET /report/<session_id>`) while delegating all business operations to `src/services/`. Author API integration tests in `tests/test_api.py`.

---

## 📋 Technical Requirements

### 1. Application Factory (`app.py`)
- Implement `create_app(config_class=Config) -> Flask`:
  - Initialize Flask application instance.
  - Load configuration from `Config`.
  - Call `Config.init_app(app)` to ensure directory structures exist.
  - Call `ModelLoader.load_all_models()` to cache models into memory at server startup.
  - Register Blueprints:
    - `main_bp` from `web/routes/main_routes.py`
    - `detection_bp` from `web/routes/detection_routes.py`
  - Register custom HTTP error handlers:
    - `400`: Render `error.html` with message "Bad Request / Invalid File".
    - `413`: Render `error.html` with message "Uploaded file exceeds 16MB limit".
    - `500`: Render `error.html` with message "Internal Server Error".

### 2. Entry Point (`run.py`)
- Standard CLI entry point:
  ```python
  from app import create_app
  import os

  app = create_app()

  if __name__ == "__main__":
      port = int(os.environ.get("PORT", 5000))
      app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
  ```

### 3. Main Routes Blueprint (`web/routes/main_routes.py`)
- Mounted at root `/`:
  - `GET /`: Renders `index.html` (Home upload page).
  - `GET /about`: Renders `about.html` (Forensics explanation, ELA theory, team info).
  - `GET /health`: Returns JSON with server status, model loading state, and uptime.

### 4. Detection Routes Blueprint (`web/routes/detection_routes.py`)
- Mounted at root `/`:
  - `POST /analyze`:
    - Ingests `request.files.get("image")` and optional `request.form.get("model")`.
    - Generates or retrieves unique `session_id` from Flask session.
    - Calls `DetectionService().analyze_image(file, session_id, model_choice)`.
    - If request header `Accept: application/json` is present: return JSON result.
    - Otherwise: store results in session and render `result.html` (or redirect).
  - `GET /report/<session_id>`: Placeholder route for PDF report streaming (delegates to Issue #13).
  - `GET /static/temp/<session_id>/<filename>`: Secure endpoint to serve transient session images for browser display.

### 5. Integration Tests (`tests/test_api.py`)
- Use Flask test client (`app.test_client()`).
- Test `GET /` returns HTTP 200.
- Test `GET /about` returns HTTP 200.
- Test `GET /health` returns HTTP 200 with JSON `status: healthy`.
- Test `POST /analyze` without file returns HTTP 400.
- Test `POST /analyze` with non-image file returns HTTP 400.
- Test `POST /analyze` with valid synthetic image returns HTTP 200 / redirect.

---

## 📂 Target Files
- `app.py`
- `run.py`
- `web/routes/main_routes.py`
- `web/routes/detection_routes.py`
- `tests/test_api.py`

---

## 🧪 Verification & Testing
```bash
pytest tests/test_api.py -v
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] Flask app initializes via factory pattern with all Blueprints registered.
- [ ] Deep learning models are loaded once at startup, not per request.
- [ ] JSON and HTML response flows are handled cleanly on `/analyze`.
- [ ] `pytest tests/test_api.py` passes 100%.
