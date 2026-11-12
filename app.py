"""Flask application factory for the image manipulation detection system."""

from __future__ import annotations

from time import monotonic
from typing import Type

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException

from config import Config
from src.models.model_loader import ModelLoader
from src.utils.logger import get_logger
from web.routes.detection_routes import detection_bp
from web.routes.main_routes import main_bp

logger = get_logger(__name__)


def create_app(config_class: Type[Config] = Config) -> Flask:
    """Create, configure, and return the Flask application.

    Args:
        config_class: Configuration class used by the application.
            Defaults to ``Config``.

    Returns:
        A configured Flask application with registered routes and error handlers.
    """
    app = Flask(
        __name__,
        template_folder=str(Config.BASE_DIR / "web" / "templates"),
        static_folder=str(Config.BASE_DIR / "web" / "static"),
    )
    app.config.from_object(config_class)
    config_class.init_app(app)
    app.extensions["started_at"] = monotonic()

    ModelLoader.load_all_models()

    app.register_blueprint(main_bp)
    app.register_blueprint(detection_bp)
    _register_error_handlers(app)
    logger.info("Flask application initialized.")
    return app


def _register_error_handlers(app: Flask) -> None:
    """Register user-facing handlers for common HTTP errors.

    Args:
        app: Flask application receiving the handlers.
    """

    @app.errorhandler(400)
    def bad_request(error: HTTPException) -> tuple[str, int]:
        """Render the invalid-request page.

        Args:
            error: The HTTP exception raised for the request.

        Returns:
            The rendered error page and HTTP 400 status.
        """
        del error
        return (
            render_template(
                "error.html",
                error_code=400,
                error_title="Bad Request",
                error_message="Bad Request / Invalid File",
            ),
            400,
        )

    @app.errorhandler(413)
    def request_entity_too_large(error: HTTPException) -> tuple[str, int]:
        """Render the upload-size-limit error page.

        Args:
            error: The HTTP exception raised for the request.

        Returns:
            The rendered error page and HTTP 413 status.
        """
        del error
        return (
            render_template(
                "error.html",
                error_code=413,
                error_title="File Too Large",
                error_message="Uploaded file exceeds 16MB limit",
            ),
            413,
        )

    @app.errorhandler(500)
    def internal_server_error(error: HTTPException) -> tuple[str, int]:
        """Render the internal-server-error page.

        Args:
            error: The HTTP exception raised for the request.

        Returns:
            The rendered error page and HTTP 500 status.
        """
        del error
        return (
            render_template(
                "error.html",
                error_code=500,
                error_title="Internal Server Error",
                error_message="Internal Server Error",
            ),
            500,
        )
