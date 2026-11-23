"""Application factory for Vaathi."""

import logging
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS


def create_app():
    """Build and configure the Flask application."""
    load_dotenv()

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") or "vaathi-local-development-key"
    app.permanent_session_lifetime = timedelta(hours=24)
    CORS(app)
    logging.basicConfig(level=logging.INFO)

    from .routes import register_routes

    register_routes(app)
    return app


app = create_app()
