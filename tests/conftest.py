import os
import subprocess
import time
import uuid
from pathlib import Path

import pytest
import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
USERS_DIR = DATA_DIR / "Users"
BOOK_LOADER = DATA_DIR / "Book_Loader.json"
BASE_URL = "http://localhost:5000"
TEST_JWT_SECRET = "integration-test-secret-key-very-long-and-secure"


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

    proc = subprocess.Popen(
        ["python3", "main.py"],
        cwd=str(PROJECT_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not _wait_for_server():
        proc.terminate()
        raise RuntimeError("Flask server did not start — check that port 5000 is free")

    yield BASE_URL

    proc.terminate()
    proc.wait()

    BOOK_LOADER.write_text(original_books)
    for f in USERS_DIR.glob("*.json"):
        f.unlink()


def unique_user():
    return f"testuser_{uuid.uuid4().hex[:8]}"


def unique_book_id():
    return int(uuid.uuid4().int % 900_000) + 100_000


def register(username, password="Password123"):
    return requests.post(f"{BASE_URL}/signup", json={"username": username, "password": password})


def login(username, password="Password123"):
    return requests.post(f"{BASE_URL}/login", json={"username": username, "password": password})


def register_and_login(username, password="Password123"):
    register(username, password)
    r = login(username, password)
    return r.json()


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def make_book(book_id, **overrides):
    book = {
        "book_name": f"Test Book {book_id}",
        "book_content": "This is the content of the test book.",
        "book_id": book_id,
        "writer": "Test Author",
        "published_year": 2024,
        "rating": 4,
        "genre": "Fiction",
        "created_at": "2024-01-01",
    }
    book.update(overrides)
    return book
