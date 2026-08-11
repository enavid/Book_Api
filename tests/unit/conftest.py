"""Unit-test fixtures: an isolated, throwaway SQLite database per test (issue #46), no server involved."""
import os
import tempfile
from pathlib import Path

import pytest
from flask import Flask

from app import models  # noqa: F401  (import registers User/Book on db.metadata)
from app.extensions import db


@pytest.fixture
def app():
    """A minimal Flask app bound to a fresh, empty SQLite file per test."""
    fd, db_path = tempfile.mkstemp(suffix=".db", prefix="test_book_api_")
    os.close(fd)

    flask_app = Flask(__name__)
    # Forward slashes in the SQLite URL via as_posix() so the path parses on every OS (Windows backslashes can misparse).
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(db_path).as_posix()}"
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(flask_app)
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()
        # Release the SQLite file from the connection pool so Windows (which
        # locks open files) can delete it below.
        db.engine.dispose()

    try:
        os.remove(db_path)
    except OSError:
        pass


@pytest.fixture
def session(app):
    """The active SQLAlchemy session for the isolated test database."""
    return db.session
