# Frontend Documentation

## Image Manipulation Detection System — Frontend

---

## Table of Contents

1. [Frontend Overview](#1-frontend-overview)
2. [Technology Stack](#2-technology-stack)
3. [Page Descriptions](#3-page-descriptions)
4. [Bootstrap Components Used](#4-bootstrap-components-used)
5. [Upload UX Flow](#5-upload-ux-flow)
6. [JavaScript Functionality](#6-javascript-functionality-mainjs)
7. [CSS Customizations](#7-css-customizations-stylecss)
8. [Responsive Design Notes](#8-responsive-design-notes)
9. [Accessibility Notes](#9-accessibility-notes)
10. [Template Variables](#10-template-variables-jinja2)

---

## 1. Frontend Overview

The frontend of the Image Manipulation Detection System is a **server-rendered multi-page application** built with Flask's Jinja2 templating engine. There is intentionally no JavaScript framework — all UI rendering is performed server-side, with vanilla JavaScript used only for progressive enhancement (upload UX, preview, loading states).

The user interface guides users through three primary actions:

1. **Upload** an image for analysis
2. **View** the analysis results (prediction, confidence, ELA visualization)
3. **Download** a PDF forensics report

All pages share a common `base.html` layout and follow a consistent Bootstrap 5 visual language.

---

## 2. Technology Stack

| Technology | Version | Role |
|---|---|---|
| **HTML5** | — | Semantic page structure, form elements |
| **CSS3** | — | Custom styling on top of Bootstrap |
| **Bootstrap** | 5.3.x | Component library, grid, utilities |
| **Vanilla JavaScript** | ES2020 | Client-side UX enhancements |
| **Jinja2** | (bundled with Flask) | Server-side HTML templating |

### Why No React / Vue / Angular?

This is a deliberate architectural choice for a student research project:

- **Simplicity**: The UI does not require complex state management or real-time data updates. The analysis result is a single server response.
- **No build toolchain**: There is no need for `npm`, `webpack`, or `babel`. The project can be run with `python app.py`.
- **Faster onboarding**: All four team members can contribute to the UI without needing JavaScript framework expertise.
- **SEO / accessibility by default**: Server-rendered HTML is accessible out of the box without additional hydration concerns.

> [!NOTE]
> Bootstrap 5 is loaded via CDN in `base.html`. No local npm install of Bootstrap is required. The project does not use Bootstrap's JavaScript bundle for anything critical — all interactive behavior is in `main.js`.

---

## 3. Page Descriptions

### 3.1 `base.html` — Base Template

**Location:** `web/templates/base.html`

The base template defines the shared HTML skeleton inherited by all other pages via Jinja2's `{% extends %}` / `{% block %}` mechanism.

**Structure:**

```
<!DOCTYPE html>
<html lang="en">
  <head>
    <!-- Meta tags, title block, Bootstrap CSS CDN, style.css link -->
  </head>
  <body>
    <!-- Navbar (Bootstrap navbar component) -->
    {% block content %}{% endblock %}
    <!-- Footer -->
    <!-- Bootstrap JS CDN, main.js -->
  </body>
</html>
```

**Navbar contents:**
- Brand logo/text: "Image Forensics" (links to `/`)
- Navigation links: Home (`/`), About (`/about`)
- Responsive hamburger collapse on mobile

**Footer contents:**
- Project name and academic context
- Disclaimer: "For research and educational purposes only."
- Team name / semester

**Jinja2 Blocks defined in `base.html`:**

| Block Name | Purpose |
|---|---|
| `title` | Page `<title>` tag content |
| `extra_head` | Additional `<link>` or `<meta>` tags per-page |
| `content` | Main page body content |
| `extra_scripts` | Additional `<script>` tags per-page |

---

### 3.2 `index.html` — Home / Upload Page

**Location:** `web/templates/index.html`
**Route:** `GET /`

The landing page and primary entry point. Presents the image upload interface.

**Page sections:**

1. **Hero Section**
   - Headline: "Detect Image Manipulation with Deep Learning"
   - Brief description of the system's purpose
   - Anchors to the upload form

2. **Upload Card**
   - Bootstrap `card` component containing the upload form
   - `<form method="POST" action="/analyze" enctype="multipart/form-data">`
   - **Drag-and-drop zone**: A styled `<div>` that acts as a drop target, with an inner `<input type="file" accept=".jpg,.jpeg,.png">` hidden beneath
   - **Image preview area**: A hidden `<img>` that shows the selected image before upload (populated by `main.js`)
   - **File metadata display**: Shows selected filename and file size
   - **Model selector**: A `<select>` dropdown with options `cnn` and `mobilenet` (default: `mobilenet`)
   - **Submit button**: "Analyze Image" with a loading spinner (hidden by default, shown on submit)

3. **How It Works Section**
   - Three Bootstrap cards in a grid row explaining:
     1. Upload your image
     2. AI analysis runs (CNN / MobileNetV2 + ELA)
     3. Download your forensic report

4. **Supported Formats Notice**
   - Bootstrap `alert-info` listing JPG, JPEG, PNG and the 16 MB size limit

**Flash message display:**
- If Flask flashes an error (e.g., invalid file type), it appears as a Bootstrap `alert-danger` dismissible alert at the top of the content block.

---

### 3.3 `result.html` — Analysis Results Page

**Location:** `web/templates/result.html`
**Route:** Rendered after `POST /analyze` succeeds (redirect to results display)

Displays the complete forensic analysis output.

**Page sections:**

1. **Result Header**
   - Page title: "Analysis Complete"
   - Timestamp of analysis

2. **Prediction Badge**
   - Large Bootstrap badge:
     - `badge bg-success` → "✓ Authentic" (when prediction is authentic)
     - `badge bg-danger` → "⚠ Potentially Manipulated" (when prediction indicates manipulation)
   - Rendered using Jinja2 conditional: `{% if prediction == 'authentic' %}`

3. **Confidence Score**
   - Text display: "Model Confidence: XX.X%"
   - Bootstrap `progress` bar filled to the confidence percentage
   - Color classes: `bg-success` (≥ 70%), `bg-warning` (50–69%), `bg-danger` (< 50%)

4. **Image Comparison Panel**
   - Side-by-side display using Bootstrap grid (`col-md-6` each):
     - **Left**: Original uploaded image with caption
     - **Right**: ELA visualization image with caption and tooltip explaining ELA
   - On mobile: stacked vertically

5. **Model Info**
   - Which model was used (CNN or MobileNetV2)
   - Brief description of the model

6. **ELA Disclaimer**
   - Bootstrap `alert-warning` with the disclaimer text explaining ELA is an investigative aid, not definitive proof.

7. **Actions Row**
   - "Download PDF Report" button → `GET /report/<session_id>`
   - "Analyze Another Image" button → `GET /`

---

### 3.4 `about.html` — About Page

**Location:** `web/templates/about.html`
**Route:** `GET /about`

Provides project context, methodology explanation, and team information.

**Page sections:**

1. **Project Description**
   - What the system does, academic context, semester/course info
   
2. **Methodology**
   - How ELA works (Error Level Analysis — recompresses JPEG to detect inconsistencies)
   - How CNN detects manipulation patterns
   - How MobileNetV2 is used (transfer learning on ImageNet weights, fine-tuned)

3. **ELA Disclaimer** (prominent `alert-warning`)
   > ELA is a forensic aid, not definitive proof. Many legitimate operations (resizing, format conversion, re-saving) can produce similar ELA artifacts. This tool is for educational and preliminary screening purposes only.

4. **Dataset Information**
   - Brief mention of CASIA v1/v2 dataset used for training
   
5. **Team Section**
   - Four team member cards (Bootstrap `card` grid), showing name and role

6. **Technologies Used**
   - List of key libraries/frameworks

---

### 3.5 `error.html` — Error Page

**Location:** `web/templates/error.html`
**Route:** Rendered by Flask error handlers (400, 413, 500, 404)

A clean, friendly error display page.

**Page sections:**

1. **Error Icon** — Large Bootstrap icon or emoji indicating error type
2. **Error Code** — The HTTP error code (e.g., 413)
3. **Error Title** — Human-readable title (e.g., "File Too Large")
4. **Error Message** — Descriptive explanation passed from the error handler
5. **Action Button** — "Go Back" or "Return to Home"

**Jinja2 variables received:**

| Variable | Type | Description |
|---|---|---|
| `error_code` | `int` | HTTP status code |
| `error_title` | `str` | Short title for the error |
| `error_message` | `str` | Detailed error description |

---

## 4. Bootstrap Components Used

| Component | Used On | Purpose |
|---|---|---|
| **Navbar** | `base.html` | Site-wide navigation with responsive collapse |
| **Card** | `index.html`, `about.html` | Upload form container, "How it works" items, team profiles |
| **Badge** | `result.html` | Prediction result label (Authentic / Manipulated) |
| **Progress Bar** | `result.html` | Visual confidence score display |
| **Alert** | `index.html`, `result.html`, `about.html` | Flash messages, disclaimers, format notices |
| **Modal** | `index.html` | (Optional) enlarged image preview on click |
| **Spinner** | `index.html` | Loading indicator during form submission |
| **Grid** (`row`/`col`) | All pages | Responsive layout system |
| **Button** | All pages | Form submission, download, navigation |
| **Form Controls** | `index.html` | File input, model selector dropdown |
| **Table** | `about.html` | Technologies list |
| **Tooltip** | `result.html` | ELA explanation on hover |

> [!TIP]
> Bootstrap tooltips require `data-bs-toggle="tooltip"` attribute on the element and a one-line JS initialization: `const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]'); [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el));` — this is included in `main.js`.

---

## 5. Upload UX Flow

The upload flow is designed for clarity and fault-tolerance. Each step is described below.

### Step-by-Step Flow

```
1. User lands on index.html
       ↓
2. User selects file (drag-drop OR click to browse)
       ↓
3. main.js: client-side type check (jpg/jpeg/png)
   → If invalid type: show inline error, block submit
       ↓
4. main.js: show image preview
   main.js: display filename and file size
       ↓
5. User clicks "Analyze Image"
       ↓
6. main.js: show loading spinner, disable submit button
       ↓
7. Browser submits multipart/form-data POST to /analyze
       ↓
8. Server validates (file presence, extension, magic bytes, size)
   → On error: redirect back to / with flashed error message
       ↓
9. Server preprocesses image → runs ML prediction → generates ELA
       ↓
10. Server saves temp results to session, renders result.html
        ↓
11. User views results (prediction badge, confidence bar, ELA image)
        ↓
12. User clicks "Download PDF Report"
        ↓
13. Browser requests GET /report/<session_id>
        ↓
14. Server generates PDF, streams it, schedules temp file cleanup
```

### Drag-and-Drop Implementation

The drag-and-drop zone is a `<div id="dropZone">` with the following behavior managed by `main.js`:

- `dragover` event: adds CSS class `drag-over` to highlight the zone
- `dragleave` event: removes the highlight class
- `drop` event: extracts the file from `event.dataTransfer.files[0]`, assigns it to the hidden file `<input>`, then triggers the preview and validation logic

---

## 6. JavaScript Functionality (`main.js`)

**Location:** `web/static/js/main.js`

`main.js` is a single vanilla JavaScript file. It runs after DOM load and enhances the upload form UX. All logic is defensive — the form will work even if JavaScript is disabled (server-side validation is authoritative).

### 6.1 File Type Client-Side Check

```javascript
const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png'];

function validateFileType(file) {
    if (!ALLOWED_TYPES.includes(file.type)) {
        showInlineError('Only JPG, JPEG, and PNG files are accepted.');
        return false;
    }
    return true;
}
```

> [!IMPORTANT]
> Client-side type checking uses `file.type` (MIME type reported by the browser). This is a UX convenience only. The server always performs authoritative validation using file magic bytes and extension whitelisting via `werkzeug.utils.secure_filename`. Never rely solely on client-side validation.

### 6.2 File Size Display

When a file is selected, the file size is read from `file.size` (bytes) and displayed in a human-readable format:

```javascript
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}
```

A visual indicator warns the user if the file exceeds 16 MB (the server limit), displayed as an orange warning before submission — the server will still reject it, but this prevents a wasted round-trip.

### 6.3 Image Preview Before Upload

```javascript
function showPreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewImg = document.getElementById('imagePreview');
        previewImg.src = e.target.result;
        previewImg.classList.remove('d-none');
    };
    reader.readAsDataURL(file);
}
```

The preview `<img>` is hidden by default (`d-none` class) and revealed with the loaded image. This gives users confidence they selected the correct file before submitting.

### 6.4 Loading State Management

On form submit, `main.js` does the following to prevent double-submission and indicate progress:

```javascript
uploadForm.addEventListener('submit', function(e) {
    if (!currentFile || !validateFileType(currentFile)) {
        e.preventDefault();
        return;
    }
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing...';
    loadingOverlay.classList.remove('d-none');
});
```

The loading overlay is a semi-transparent Bootstrap spinner panel that covers the upload card. It is dismissed automatically when the browser navigates to the results page.

### 6.5 Bootstrap Tooltip Initialization

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el));
});
```

### 6.6 Inline Error Display

```javascript
function showInlineError(message) {
    const errorDiv = document.getElementById('uploadError');
    errorDiv.textContent = message;
    errorDiv.classList.remove('d-none');
}

function clearInlineError() {
    const errorDiv = document.getElementById('uploadError');
    errorDiv.classList.add('d-none');
    errorDiv.textContent = '';
}
```

---

## 7. CSS Customizations (`style.css`)

**Location:** `web/static/css/style.css`

`style.css` is loaded after Bootstrap's CSS. It overrides Bootstrap defaults and adds project-specific styles.

### Key Custom Rules

#### Drop Zone Styling

```css
#dropZone {
    border: 2px dashed #6c757d;
    border-radius: 8px;
    padding: 2.5rem;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s ease, background-color 0.2s ease;
}

#dropZone.drag-over {
    border-color: #0d6efd;
    background-color: #e8f0fe;
}

#dropZone:hover {
    border-color: #0d6efd;
}
```

#### ELA Side-by-Side Display

The original and ELA images are displayed in equal-width containers with a fixed height to ensure alignment regardless of image dimensions:

```css
.ela-comparison-container {
    display: flex;
    gap: 1rem;
}

.ela-comparison-container .image-panel {
    flex: 1;
    min-width: 0;
}

.ela-comparison-container img {
    width: 100%;
    height: 300px;
    object-fit: contain;
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
}

@media (max-width: 767px) {
    .ela-comparison-container {
        flex-direction: column;
    }
}
```

#### Prediction Badge Override

```css
.prediction-badge {
    font-size: 1.4rem;
    padding: 0.6em 1.2em;
    border-radius: 50px;
}
```

#### Navbar Brand

```css
.navbar-brand {
    font-weight: 700;
    letter-spacing: 0.5px;
}
```

#### Footer

```css
footer {
    background-color: #212529;
    color: #adb5bd;
    padding: 1.5rem 0;
    font-size: 0.875rem;
}
```

#### Loading Overlay

```css
#loadingOverlay {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(255, 255, 255, 0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}
```

---

## 8. Responsive Design Notes

The UI is built mobile-first using Bootstrap 5's responsive grid. Key responsive behaviors:

| Breakpoint | Behavior |
|---|---|
| `xs` (< 576px) | Single column layout; upload card full-width |
| `sm` (≥ 576px) | Slight padding added to cards |
| `md` (≥ 768px) | "How It Works" grid: 3 columns; ELA side-by-side |
| `lg` (≥ 992px) | Navbar links fully visible (no hamburger) |
| `xl` (≥ 1200px) | Max content width constrained via Bootstrap `container` |

The ELA comparison panel uses `flex-direction: column` on small screens and `flex-direction: row` on `md+` screens, controlled via the custom CSS media query in `style.css`.

The navbar uses Bootstrap's built-in `navbar-expand-lg` class, collapsing to a hamburger menu on screens narrower than 992px.

---

## 9. Accessibility Notes

| Feature | Implementation |
|---|---|
| **Semantic HTML** | `<main>`, `<nav>`, `<footer>`, `<section>`, `<article>` used correctly |
| **Alt text** | All `<img>` tags include descriptive `alt` attributes (e.g., `alt="Original uploaded image"`, `alt="ELA visualization of uploaded image"`) |
| **Form labels** | Every `<input>` and `<select>` has an associated `<label>` |
| **ARIA roles** | `role="alert"` on flash message divs; `aria-live="polite"` on dynamic content areas |
| **Focus management** | Submit button focus is maintained; loading overlay does not trap keyboard focus |
| **Color contrast** | Bootstrap 5 defaults meet WCAG AA; custom colors checked against 4.5:1 ratio |
| **Keyboard navigation** | Drag-and-drop zone is reachable via keyboard (`tabindex="0"`, `Enter`/`Space` triggers file dialog) |
| **Screen reader** | Spinner has `role="status"` and visually hidden text "Loading..." |

---

## 10. Template Variables (Jinja2)

Variables passed from Flask route handlers to each template via `render_template()`.

### `index.html`

| Variable | Type | Source | Description |
|---|---|---|---|
| *(none required)* | — | — | Page renders statically; flash messages handled by `get_flashed_messages()` in template |

### `result.html`

| Variable | Type | Source | Description |
|---|---|---|---|
| `prediction` | `str` | ML predictor | `'authentic'` or `'manipulated'` |
| `confidence` | `float` | ML predictor | Confidence score 0.0–1.0 (displayed as %) |
| `confidence_pct` | `int` | Route handler | `int(confidence * 100)` — for progress bar width |
| `model_used` | `str` | Config / request | `'CNN'` or `'MobileNetV2'` |
| `original_image_url` | `str` | Route handler | Relative URL to temp-served original image |
| `ela_image_url` | `str` | ELA generator | Relative URL to temp-served ELA image |
| `session_id` | `str` | Flask session | UUID for linking to report download |
| `timestamp` | `str` | Route handler | ISO format datetime string of analysis |

### `about.html`

| Variable | Type | Source | Description |
|---|---|---|---|
| *(none required)* | — | — | Page is static content |

### `error.html`

| Variable | Type | Source | Description |
|---|---|---|---|
| `error_code` | `int` | Error handler | HTTP status code (400, 413, 500, etc.) |
| `error_title` | `str` | Error handler | Short human-readable error name |
| `error_message` | `str` | Error handler | Full description of what went wrong |

### `base.html` (available on all pages)

| Variable | Type | Source | Description |
|---|---|---|---|
| `request` | Flask `Request` | Flask global | Used to highlight active navbar link via `request.endpoint` |
