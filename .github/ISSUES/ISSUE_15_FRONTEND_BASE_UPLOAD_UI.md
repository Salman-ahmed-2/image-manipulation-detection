# [ISSUE #15] Responsive Bootstrap 5 Base Layout & Image Upload Interface

## 📌 Issue Metadata
- **Milestone:** M4 — Full Web Application & Reports
- **Phase:** Phase 7 (Frontend Presentation Layer)
- **Estimated Effort:** 4–5 hours
- **Labels:** `frontend`, `bootstrap5`, `html5`, `javascript`, `ui-ux`
- **Dependencies:** Issue #1 (`config.py`), Issue #12 (`app.py`, `web/routes/`)
- **Blocks:** Issue #16 (Results Dashboard), Issue #17 (System Testing)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a Frontend Developer & UI/UX Designer.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/application/FRONTEND_DOCUMENTATION.md`
> 2. `docs/USER_GUIDE.md`
> 3. `AGENTS.md` (Strict rules: Bootstrap 5.3 CDN, vanilla JavaScript, mobile-responsive layout, no Node.js/npm build steps).

---

## 🎯 Objective & Context
Implement the client presentation shell under `web/templates/` and `web/static/`. Create the shared master layout (`base.html`), the main upload landing page with an interactive drag-and-drop dropzone (`index.html`), the project background and ELA theory page (`about.html`), and the structured error display view (`error.html`). Add custom styling in `style.css` and client-side image preview/validation in `main.js`.

---

## 📋 Technical Requirements

### 1. Base Layout (`web/templates/base.html`)
- Loads Bootstrap 5.3 CDN (CSS & JS bundle) and Bootstrap Icons.
- **Navbar:** Brand logo/title ("Image Forensic Scanner"), links to Home (`/`), About (`/about`), and GitHub repo.
- **Main Container:** Jinja2 block `{% block content %}{% endblock %}` with responsive padding.
- **Footer:** University semester project notice, copyright, team names, and short forensic disclaimer.

### 2. Upload Landing Page (`web/templates/index.html`)
- Extends `base.html`.
- **Hero Section:** Clear title and 2-sentence explanation of preliminary authenticity screening.
- **Interactive Upload Card:**
  - Drag-and-drop dropzone with file picker fallback.
  - Client-side format badge (`.jpg`, `.jpeg`, `.png`, Max 16 MB).
  - Instant image preview container (hidden until file is chosen).
  - Optional model selection dropdown (default: "MobileNetV2 (Recommended)", alternate: "Custom CNN").
  - Prominent "Analyze Image" button.
  - Loading spinner overlay ("Analyzing image forensic signals...") activated upon submission.
- **Methodology Cards (3 Columns):**
  - Card 1: Deep Learning Classification (Feature learning).
  - Card 2: Error Level Analysis (JPEG compression error).
  - Card 3: Downloadable PDF Reports (Shareable findings).

### 3. About & Educational Page (`web/templates/about.html`)
- Comprehensive overview of digital image tampering (copy-move vs splicing).
- Deep-dive into ELA theory with guidance on false positives (edges, text) and false negatives.
- Clear statement on why the tool is for preliminary screening rather than judicial certification.
- 4-person student team credits.

### 4. Structured Error Page (`web/templates/error.html`)
- Renders error code (`400`, `413`, `500`) with friendly explanation and a "Return to Upload" button.

### 5. Static Assets (`web/static/css/style.css` & `web/static/js/main.js`)
- `style.css`: Clean modern typography, custom drag-hover dropzone border animation, responsive media queries.
- `main.js`:
  - Dragover / dragleave / drop event listeners.
  - Client-side extension validation and size check before form submit.
  - `FileReader` preview generation displaying image immediately upon selection.
  - Disables submit button and reveals loading spinner upon form submission.

---

## 📂 Target Files
- `web/templates/base.html`
- `web/templates/index.html`
- `web/templates/about.html`
- `web/templates/error.html`
- `web/static/css/style.css`
- `web/static/js/main.js`

---

## 🧪 Verification & Testing
```bash
# Verify templates render cleanly with Jinja2 environment
python3 -c "
from app import create_app
app = create_app()
with app.test_client() as client:
    r1 = client.get('/')
    r2 = client.get('/about')
    assert r1.status_code == 200
    assert r2.status_code == 200
    print('Frontend templates rendered successfully!')
"
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] Bootstrap 5.3 UI renders cleanly across desktop (1920x1080) and mobile (375px) viewports.
- [ ] Drag-and-drop dropzone provides live image preview prior to submission.
- [ ] Client validation catches oversized or unsupported files before upload.
- [ ] Loading spinner appears smoothly when analysis is submitted.
