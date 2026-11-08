# ADR-001: Technology Stack Selection

## Context & Problem Statement
The team must select an implementation technology stack for a 4–6 week university semester project developing an AI-based Image Manipulation Detection web application. The stack must support rapid development, native deep learning model serving, image manipulation forensics, and responsive web presentation without enterprise infrastructure overhead.

## Considered Options
1. **Flask (Python 3.11) + TensorFlow/Keras + Bootstrap 5** (Selected)
2. **FastAPI (Python 3.11) + PyTorch + React SPA**
3. **Django (Python 3.11) + TensorFlow + Vanilla HTML/CSS**
4. **Streamlit (Python 3.11) + PyTorch**

## Decision Outcome
**Chosen Option:** **Option 1: Flask (Python 3.11) + TensorFlow/Keras + Bootstrap 5**

### Positive Consequences:
- **Zero Build Step:** Bootstrap 5 served via CDN eliminates Node.js/npm dependencies, Webpack build overhead, and frontend compilation errors.
- **Native ML Ecosystem:** Python 3.11 seamlessly links Pillow, OpenCV, NumPy, and TensorFlow.
- **Lightweight Architecture:** Flask Blueprints provide clean modular separation without Django's heavyweight database migrations and ORM baggage.
- **Keras High-Level API:** TensorFlow/Keras provides out-of-the-box MobileNetV2 pretrained backbones with minimal boilerplate.

### Negative Consequences:
- Flask runs synchronously by default; worker threads require careful memory management during model inference.
- Bootstrap 5 requires server-rendered Jinja2 templates rather than dynamic client-side SPA state transitions.

## Status
**ACCEPTED** (2026-11-08)
