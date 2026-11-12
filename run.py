"""Development entry point for the Flask application."""

from __future__ import annotations

import os

from app import create_app
from config import Config

app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", Config.PORT))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
