"""
Integration-only fixtures: spin up a REAL Flask server against an isolated,
throwaway SQLite database.

Because this conftest lives under tests/integration/, pytest loads it ONLY when
integration tests are collected. A pure unit run (e.g. `make test-unit`, or
pytest tests/unit/) never imports this file, so it never starts the server and
never runs `flask db upgrade` — which is exactly why a broken/absent server
setup can no longer make the in-process unit tests error out.

Cross-platform / Windows notes (all preserved from the original design):
* The SQLite URL uses forward slashes via Path.as_posix(): on Windows a raw
  path has backslashes ("sqlite:///C:\\...") which SQLAlchemy can misparse.
* The server runs single-process (USE_RELOADER=0) so proc.terminate() reliably
  stops it on every OS, including Windows, instead of leaving an orphan on 5000.
* The subprocess uses sys.executable + "-m flask" / "main.py", so it does not
  depend on a `flask`/`python` entry being on PATH (matters on Windows).
* Deleting a leftover test DB is wrapped in try/except OSError, because Windows
  locks open files and raises PermissionError rather than silently allowing the
  unlink.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

from tests.conftest import BASE_URL

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_DIR / "data"
TEST_DB = DATA_DIR / "test_app.db"
USERS_DIR = DATA_DIR / "Users"
BOOK_LOADER = DATA_DIR / "Book_Loader.json"
TEST_JWT_SECRET = "integration-test-secret-key-very-long-and-secure"


def _remove_test_db():
    # Delete a leftover test DB from a previous run. Wrapped in try/except
    # because on Windows a still-open SQLite file cannot be deleted (raises
    # PermissionError); swallowing it lets the run continue and the file gets
    # reused/rebuilt rather than crashing at import time.
    try:
        if TEST_DB.exists():
            TEST_DB.unlink()
    except OSError:
        pass


_remove_test_db()


def _wait_for_server(timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        try:
            r = requests.get(f"{BASE_URL}/get_all_book", timeout=1)
            if r.status_code in (200, 401, 422):
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


@pytest.fixture(scope="session", autouse=True)
def flask_server():
    USERS_DIR.mkdir(parents=True, exist_ok=True)

    original_books = BOOK_LOADER.read_text() if BOOK_LOADER.exists() else "{}"
    BOOK_LOADER.write_text("{}")
    for f in USERS_DIR.glob("*.json"):
        f.unlink()
    env = os.environ.copy()
    env["JWT_SECRET_KEY"] = TEST_JWT_SECRET
    # Run a single-process server (no auto-reloader child), so terminate()
    # below reliably stops it on every OS — Windows included — instead of
    # leaving an orphan holding port 5000.
    env["USE_RELOADER"] = "0"
    # Point the whole stack at an isolated throwaway DB (issue #46) so tests
    # never touch the developer's data/app.db.
    env["DATABASE_URL"] = "sqlite:///" + TEST_DB.as_posix()

    # Build the schema in the fresh test DB before the server starts. main.py
    # does not create tables on its own, so without this the server would come
    # up against an empty file and every DB write would 500 with "no such
    # table". `flask db upgrade` runs the migrations (issue #42) into test_app.db.
    upgrade = subprocess.run(
        [sys.executable, "-m", "flask", "--app", "main", "db", "upgrade"],
        cwd=str(PROJECT_DIR), env=env,
        capture_output=True, text=True,
    )
    if upgrade.returncode != 0:
        raise RuntimeError(
            "flask db upgrade failed while preparing the test database:\n"
            + upgrade.stderr[-1000:]
        )

    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=str(PROJECT_DIR), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    if not _wait_for_server():
        proc.terminate()
        raise RuntimeError("Flask server did not start — check that port 5000 is free")

    yield BASE_URL

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    BOOK_LOADER.write_text(original_books)
    for f in USERS_DIR.glob("*.json"):
        f.unlink()
