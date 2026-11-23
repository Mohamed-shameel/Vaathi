"""Compatibility entry point for local development and Gunicorn."""

from vaathi import app


if __name__ == "__main__":
    app.run(debug=True)
