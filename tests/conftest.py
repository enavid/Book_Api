"""
Shared test helpers for BOTH unit and integration tests.

This module is intentionally lightweight: it holds only pure helper functions
and constants, and pulls in NO server/database machinery. That machinery lives
in tests/integration/conftest.py, so pytest loads it only when integration
tests are collected.

Why this split matters: the Flask-server fixture used to live here as a
session-scoped autouse fixture, which meant EVERY test run (including a pure
unit run like `make test-unit`) started the server and ran `flask db upgrade`.
If that upgrade failed for any reason, all 68 in-process unit tests errored out
even though they never touch the server. Unit tests now run fully in-process and
never trigger the server or the database.
"""
import uuid

import requests

BASE_URL = "http://localhost:5000"


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
