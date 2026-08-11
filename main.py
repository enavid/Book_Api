import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from app import auth, books
from app.extensions import db

# Load variables from a local .env file (next to this file) into the
# environment. This lets JWT_SECRET_KEY (and any other config) be set once in
# a file instead of exported in the shell on every run — which matters on
# Windows, where `export VAR=...` is not a valid command. Real environment
# variables always win: load_dotenv does not override anything already set,
# so CI and the test harness keep full control.
load_dotenv(Path(__file__).resolve().parent / '.env')

app = Flask(__name__)
books_bp = books.books_bp
auth_bp = auth.auth_bp
jwt_manager = JWTManager(app)

secret = os.environ.get('JWT_SECRET_KEY')
BASE_DIR = Path(__file__).resolve().parent
# Use forward slashes in the SQLite URL. On Windows str(WindowsPath) yields
# backslashes ("sqlite:///C:\...\app.db"), which SQLAlchemy can misparse;
# as_posix() gives "C:/.../app.db", which works on every OS.
default_sqlite = f"sqlite:///{(BASE_DIR / 'data' / 'app.db').as_posix()}"
# The DB connection string is overridable via the DATABASE_URL env var, so tests
# (data/test_app.db) and production (e.g. PostgreSQL:
# postgresql+psycopg://user:password@host:5432/book_api) can point the same code
# at a different database. When it is unset, fall back to the local SQLite file.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_sqlite)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)
migrate = Migrate(app, db)

if not secret or len(secret) < 32:
    raise RuntimeError(
        'JWT_SECRET_KEY must be set and at least 32 characters. '
        'Create a .env file next to main.py (see .env.example) with a line like '
        'JWT_SECRET_KEY=your-long-random-secret-key, or set it in your shell '
        '(Windows PowerShell: $env:JWT_SECRET_KEY="..."; CMD: set JWT_SECRET_KEY=...; '
        'Linux/macOS: export JWT_SECRET_KEY=...).'
    )
app.config['JWT_SECRET_KEY'] = secret
CORS(app)
app.register_blueprint(books_bp)
app.register_blueprint(auth_bp)

# API documentation: serve the OpenAPI spec at /openapi.json and the interactive
# Swagger UI at /docs. The Swagger UI static assets ship with flask-swagger-ui,
# so the docs page works fully offline (no CDN needed).
from flask_swagger_ui import get_swaggerui_blueprint

from app.openapi import API_URL, SWAGGER_URL, openapi_bp

app.register_blueprint(openapi_bp)
app.register_blueprint(
    get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': 'Book API'})
)
if __name__ == '__main__':
    # The auto-reloader spawns a second process that actually holds the port.
    # For the test harness (and any scripted run) that makes a clean shutdown
    # unreliable — terminating the parent can leave an orphan holding port 5000,
    # which is especially likely on Windows. Set USE_RELOADER=0 to run a single
    # process that stops cleanly with a plain terminate().
    use_reloader = os.environ.get('USE_RELOADER', '1') != '0'
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=use_reloader)
