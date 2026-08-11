# Integration-only fixtures: spin up a real Flask server against an isolated test DB; loaded only for integration runs.
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
    # Delete a leftover test DB; try/except because Windows locks open files and raises on unlink.
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
    # Single-process server (no reloader child) so terminate() stops it cleanly on every OS, Windows included.
    env["USE_RELOADER"] = "0"
    # Point the whole stack at an isolated throwaway DB (issue #46) so tests never touch data/app.db.
    env["DATABASE_URL"] = "sqlite:///" + TEST_DB.as_posix()

    # Build the schema in the fresh test DB before the server starts, else every DB write 500s (issue #42).
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
