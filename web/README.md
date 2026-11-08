# Web Presentation Layer (`web/`)

This directory houses the Flask application routes, Jinja2 presentation templates, and static CSS/JavaScript client assets.

## Directory Layout

```
web/
├── routes/                    # HTTP route controllers (No ML business logic here)
│   ├── detection_routes.py    # POST /analyze, GET /report/<session_id>
│   └── main_routes.py         # GET /, GET /about, GET /health
│
├── static/                    # Frontend client assets
│   ├── css/
│   │   └── style.css          # Custom Bootstrap 5 overrides and ELA styling
│   └── js/
│       └── main.js            # Drag-and-drop, client validation, loading spinner
│
└── templates/                 # Jinja2 HTML templates
    ├── about.html             # Project background, ELA theory, and team info
    ├── base.html              # Core layout shell with navbar, footer, disclaimers
    ├── error.html             # Structured user error view (400, 413, 500)
    ├── index.html             # File upload landing page with dropzone
    └── result.html            # Forensic dashboard with side-by-side ELA display
```

## Architectural Guidelines
1. **Separation of Concerns:** Route handlers in `web/routes/` are strictly limited to receiving request parameters, delegating to `src/services/`, and rendering templates or returning JSON responses.
2. **CDN Strategy:** Bootstrap 5.3 is loaded via CDN in `base.html`, eliminating the need for Node.js build pipelines.
