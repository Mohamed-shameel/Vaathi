# Vaathi — AI Study Buddy

## Run locally

1. Install dependencies with `python -m pip install -r requirements.txt`.
2. Copy `.env.example` to `.env` and set the credentials you want to use.
3. Start the app with `python app.py` and open http://127.0.0.1:5000.

The home page can load without external services. Chat responses require an
OpenAI API key; MongoDB is used to save conversation history.

## Project layout

- `app.py` — local and Gunicorn entry point
- `vaathi/` — application factory, routes, database access, templates, and static assets
- `requirements.txt` — Python dependencies
- `Procfile` and `runtime.txt` — deployment configuration
