"""Integration tests that users/books persist in the DB (not JSON) against an isolated test DB (issues #43/#44/#46)."""
import sqlite3

import requests

from tests.conftest import (
    BASE_URL,
    auth_headers,
    make_book,
    register,
    register_and_login,
    unique_book_id,
    unique_user,
)

# The server/database machinery (including TEST_DB and USERS_DIR) lives in the
# integration-only conftest, so import those from there.
from tests.integration.conftest import TEST_DB, USERS_DIR

# The integration server uses an isolated throwaway DB (issue #46); assertions read that same file, never data/app.db.


def _query(db_path, sql, params=()):
    con = sqlite3.connect(str(db_path))
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()


class TestUserPersistence:
    """Issue #43: signup/login use the users table, not data/Users/*.json."""

    def test_signup_creates_a_users_row(self):
        username = unique_user()
        register(username)
        rows = _query(TEST_DB, "SELECT username FROM users WHERE username = ?", (username,))
        assert rows, f"no users row created for {username}"

    def test_signup_does_not_create_a_json_user_file(self):
        username = unique_user()
        register(username)
        assert not (USERS_DIR / f"{username}.json").exists(), (
            "signup still wrote a JSON user file — file storage not removed"
        )

    def test_password_is_stored_as_bcrypt_hash_in_db(self):
        username = unique_user()
        register(username, "PlainPassword1")
        rows = _query(TEST_DB, "SELECT password FROM users WHERE username = ?", (username,))
        assert rows, "user not found in db"
        stored = rows[0][0]
        assert stored != "PlainPassword1"
        assert stored.startswith("$2b$")


class TestBookPersistence:
    """Issue #44: book endpoints read/write the books table, not the JSON file."""

    def test_added_book_creates_a_books_row(self):
        tokens = register_and_login(unique_user())
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid, book_name="DB Row Book"),
                      headers=auth_headers(tokens["token"]))
        rows = _query(TEST_DB, "SELECT book_name FROM books WHERE book_id = ?", (bid,))
        assert rows and rows[0][0] == "DB Row Book"

    def test_book_owner_id_links_to_the_users_table(self):
        username = unique_user()
        tokens = register_and_login(username)
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid),
                      headers=auth_headers(tokens["token"]))
        rows = _query(
            TEST_DB,
            "SELECT u.username FROM books b JOIN users u ON b.owner_id = u.id "
            "WHERE b.book_id = ?",
            (bid,),
        )
        assert rows and rows[0][0] == username

    def test_deleting_a_book_removes_the_row(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid), headers=h)
        requests.delete(f"{BASE_URL}/delete_book/{bid}", headers=h)
        rows = _query(TEST_DB, "SELECT 1 FROM books WHERE book_id = ?", (bid,))
        assert rows == []


class TestTestDatabaseIsolation:
    """Issue #46: integration tests use a separate test DB (data/test_app.db via DATABASE_URL), never the developer's data/app.db."""

    def test_integration_server_uses_isolated_test_database(self):
        assert TEST_DB.exists(), (
            "the isolated data/test_app.db was not created; the server is not "
            "honouring DATABASE_URL (issue #40/#46)"
        )
