# [ISSUE #16] Forensic Results Dashboard with Side-by-Side ELA Visualizer

## 📌 Issue Metadata
- **Milestone:** M4 — Full Web Application & Reports
- **Phase:** Phase 7 (Frontend Presentation Layer)
- **Estimated Effort:** 4–5 hours
- **Labels:** `frontend`, `dashboard`, `ela-visualizer`, `bootstrap5`, `ux`
- **Dependencies:** Issue #12 (`web/routes/`), Issue #13 (`report_service.py`), Issue #15 (`base.html`)
- **Blocks:** Issue #17 (System Testing)

---

## 🤖 AI Prompt Directive
> **Instructions for AI Coding Agent:**
> You are acting as a Senior UI/UX & Forensic Visualization Developer.
> Before writing code, you **MUST read the following authoritative documentation**:
> 1. `docs/application/FRONTEND_DOCUMENTATION.md`
> 2. `docs/image_forensics/ELA_OVERVIEW.md`
> 3. `docs/USER_GUIDE.md`
> 4. `AGENTS.md` (Strict rules: Display side-by-side images, show verdict badge and confidence bar, prominent disclaimer box required, download PDF button).

---

## 🎯 Objective & Context
Implement the forensic analysis results dashboard in `web/templates/result.html`. After an image is analyzed, this view displays the classification verdict badge (Authentic vs. Potentially Manipulated), a calibrated confidence meter, technical metadata cards, a synchronized side-by-side comparison between the original photo and the 10x amplified ELA visualization map, the mandatory legal disclaimer, and a one-click "Download PDF Report" action.

---

## 📋 Technical Requirements

### 1. Results View (`web/templates/result.html`)
- Extends `base.html`.
- **Top Verdict Banner:**
  - If Authentic (`verdict_code == 0`):
    - Green badge: `🟢 Authentic Image` (`bg-success`).
    - Subtitle: *"The deep learning model detected minimal statistical evidence of manipulation."*
  - If Potentially Manipulated (`verdict_code == 1`):
    - Red/Orange badge: `🔴 Potentially Manipulated` (`bg-danger` or `bg-warning`).
    - Subtitle: *"The deep learning model identified anomalous compression or structural tampering traces."*
- **Confidence Meter:**
  - Bootstrap 5 progress bar showing percentage (e.g. `94.2%`).
  - Styled dynamically based on verdict class.
- **Side-by-Side Visual Forensic Studio:**
  - Two responsive columns (`col-lg-6` on desktop, stacked on mobile):
    - **Card Left: Original Uploaded Image:**
      - High-resolution display in constrained card viewport with zoom/pan inspect toggle.
      - Caption: *"Original Ingested Photograph"*.
    - **Card Right: Error Level Analysis (ELA) Map:**
      - Inverted / amplified visualization showing compression residual differences.
      - Caption: *"Error Level Analysis (10x Contrast Scale)"*.
- **Technical Metadata Card:**
  - 4-column badge metrics: Input Dimensions, Colorspace (RGB), Model Architecture Used, Latency.
- **Mandatory Forensic Disclaimer Box (Alert Warning):**
  - Displays `Config.ELA_DISCLAIMER`:
    > *"ELA visualization is an investigative aid. Bright regions indicate potential compression inconsistencies and do not constitute definitive proof of digital manipulation."*
- **Action Toolbar:**
  - Button 1: **"Download PDF Report"** (Links to `GET /report/{{ session_id }}` with download icon).
  - Button 2: **"Analyze Another Image"** (Returns to `GET /` with reset icon).

### 2. Client JavaScript Enhancements (`web/static/js/main.js` - Results Module)
- Optional synchronized image pan/hover or side-by-side split slider (before/after slider) allowing users to visually slide the ELA map over the original photo.

---

## 📂 Target Files
- `web/templates/result.html`
- `web/static/css/style.css` (enhanced)
- `web/static/js/main.js` (enhanced)

---

## 🧪 Verification & Testing
```bash
# Verify result template renders with mock dictionary
python3 -c "
from app import create_app
from flask import render_template
app = create_app()
with app.test_request_context():
    html = render_template('result.html', results={
        'session_id': 'test-session',
        'verdict_label': 'Potentially Manipulated',
        'verdict_code': 1,
        'confidence': 93.4,
        'model_used': 'mobilenet_v2',
        'original_image_path': '/static/temp/test/orig.jpg',
        'ela_image_path': '/static/temp/test/ela.png',
        'disclaimer': 'ELA is an investigative aid.'
    })
    assert 'Potentially Manipulated' in html
    assert 'Download PDF Report' in html
    print('Result dashboard template validated successfully!')
"
```

---

## ✅ Acceptance Criteria (Definition of Done)
- [ ] Verdict badge, confidence progress meter, and model metadata render accurately.
- [ ] Original image and ELA visualization are displayed side-by-side on desktop and stack cleanly on mobile.
- [ ] Prominent disclaimer alert is visibly rendered on the page.
- [ ] "Download PDF Report" button triggers `/report/<session_id>` file download.
