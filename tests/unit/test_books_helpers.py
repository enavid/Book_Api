"""Unit tests for app/books.py helpers: error_response and is_owner (no HTTP server)."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from flask import Flask

import app.books as books


@pytest.fixture
def app_ctx():
    app = Flask(__name__)
    with app.app_context():
        yield app


class TestErrorResponse:
    """error_response must always return {"message": ...} plus the status code."""

    def test_returns_message_body_and_status_code(self, app_ctx):
        resp, code = books.error_response("not found", 404)
        assert code == 404
        assert resp.get_json() == {"message": "not found"}

    def test_always_uses_the_message_key(self, app_ctx):
        resp, _ = books.error_response("anything", 400)
        assert "message" in resp.get_json()
        assert "error" not in resp.get_json()

    def test_preserves_arbitrary_status_codes(self, app_ctx):
        for code in (400, 401, 403, 404, 409):
            _, returned = books.error_response("x", code)
            assert returned == code


class TestIsOwner:
    """is_owner checks a book dict's 'added_by' against a username via .get(), so it never crashes on a missing key (issues #21/#33)."""

    ALICE_BOOK = {"book_id": 1, "added_by": "alice"}
    BOB_BOOK = {"book_id": 2, "added_by": "bob"}

    def test_true_when_owner_matches(self):
        assert books.is_owner(self.ALICE_BOOK, "alice") is True

    def test_false_when_owner_differs(self):
        assert books.is_owner(self.ALICE_BOOK, "bob") is False

    def test_false_for_unknown_username(self):
        assert books.is_owner(self.BOB_BOOK, "carol") is False

    def test_false_when_entry_has_no_added_by(self):
        # A malformed entry without 'added_by' is simply not owned by anyone,
        # rather than raising — .get() returns None, which never equals a name.
        assert books.is_owner({"book_id": 3}, "alice") is False


# NOTE: old TestLoadSaveBooks removed (tested the deleted JSON file-storage layer); persistence now covered by test_database.py.
