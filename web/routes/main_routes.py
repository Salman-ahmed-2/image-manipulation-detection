"""Blueprint for the home, about, and health-check routes."""

from __future__ import annotations

from time import monotonic
from typing import Any

from flask import Blueprint, current_app, jsonify, render_template, session

from config import Config
from src.models.model_loader import ModelLoader
from src.utils.file_validator import cleanup_session_directory

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index() -> str:
    """Render the image-upload home page.

    Returns:
        The rendered home page.
    """
    session_id = session.get("session_id")
    if isinstance(session_id, str):
        cleanup_session_directory(session_id)
    session.pop("session_id", None)
    session.pop("analysis_result", None)
    return render_template("index.html")


@main_bp.get("/about")
def about() -> str:
    """Render the project information page.

    Returns:
        The rendered about page.
    """
    return render_template("about.html")


@main_bp.get("/health")
def health() -> Any:
    """Return application health, model state, and uptime as JSON.

    Returns:
        A JSON response describing the application runtime state.
    """
    model_names = tuple(
        name for name in Config.EVALUATION_MODEL_CHOICES if name != "both"
    )
    models_loaded = {
        name: ModelLoader.get_model(name) is not None for name in model_names
    }
    started_at = current_app.extensions.get("started_at", monotonic())
    return jsonify(
        {
            "status": "healthy",
            "models_loaded": models_loaded,
            "active_model": current_app.config.get("ACTIVE_MODEL", Config.ACTIVE_MODEL),
            "uptime_seconds": max(0, int(monotonic() - started_at)),
        }
    )
