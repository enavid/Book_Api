import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from app import auth, books
from app.extensions import db

# Load JWT_SECRET_KEY (and other config) from a local .env; real env vars still win, so CI/tests keep control.
load_dotenv(Path(__file__).resolve().parent / '.env')

app = Flask(__name__)
books_bp = books.books_bp
auth_bp = auth.auth_bp
jwt_manager = JWTManager(app)

secret = os.environ.get('JWT_SECRET_KEY')
BASE_DIR = Path(__file__).resolve().parent
# Forward slashes in the SQLite URL via as_posix() so the path parses on Windows too.
default_sqlite = f"sqlite:///{(BASE_DIR / 'data' / 'app.db').as_posix()}"
# DATABASE_URL overrides the DB (tests use test_app.db, prod can use Postgres); falls back to local SQLite.
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

# Serve the OpenAPI spec at /openapi.json and the Swagger UI at /docs (assets bundled, works offline).
from flask_swagger_ui import get_swaggerui_blueprint

from app.openapi import API_URL, SWAGGER_URL, openapi_bp

app.register_blueprint(openapi_bp)
app.register_blueprint(
    get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': 'Book API'})
)
if __name__ == '__main__':
    # USE_RELOADER=0 runs a single process so terminate() stops it cleanly (no orphan on port 5000, esp. Windows).
    use_reloader = os.environ.get('USE_RELOADER', '1') != '0'
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=use_reloader)
