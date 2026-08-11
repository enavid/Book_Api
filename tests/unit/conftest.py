"""
Unit-test database fixtures (issue #46).

These fixtures give each test its own **isolated, throwaway database** so the
model/ORM layer can be tested in-process, with no running HTTP server and no
touching of the real ``data/app.db`` development database.

Design notes
------------
* A brand-new temporary SQLite file is created per test and deleted at the end.
  A file (rather than ``sqlite:///:memory:``) is used on purpose: Flask-SQLAlchemy
  hands out connections from a pool, and an in-memory SQLite database lives only
  inside a single connection, so a pooled second connection would see an empty
  schema. A temp file is shared by every connection and is just as disposable.
* ``db`` is the shared SQLAlchemy instance from ``app.extensions``; the models in
  ``app.models`` are already registered on it at import time, so
  ``db.create_all()`` builds the ``users`` and ``books`` tables from the models.
"""
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
    # Forward slashes in the SQLite URL so the path parses on every OS. On
    # Windows a raw path is "C:\...\x.db" (backslashes), which SQLAlchemy can
    # misparse; as_posix() gives "C:/.../x.db".
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
