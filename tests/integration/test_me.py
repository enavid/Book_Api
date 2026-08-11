"""Integration tests for GET /me. TDD: red until implemented."""
import requests

from tests.conftest import (
    BASE_URL,
    auth_headers,
    make_book,
    register_and_login,
    unique_book_id,
    unique_user,
)


class TestMeAuth:

    def test_requires_authentication(self):
        assert requests.get(f"{BASE_URL}/me").status_code in (401, 422)

    def test_invalid_token_returns_401(self):
        r = requests.get(f"{BASE_URL}/me", headers={"Authorization": "Bearer not.a.jwt"})
        assert r.status_code in (401, 422)

    def test_refresh_token_is_not_accepted_as_access(self):
        # /me is protected by @jwt_required() (access only); a refresh token
        # must be rejected there.
        tokens = register_and_login(unique_user())
        r = requests.get(f"{BASE_URL}/me", headers=auth_headers(tokens["refresh_token"]))
        assert r.status_code in (401, 422)


class TestMeContent:

    def test_returns_caller_username(self):
        username = unique_user()
        tokens = register_and_login(username)
        r = requests.get(f"{BASE_URL}/me", headers=auth_headers(tokens["token"]))
        assert r.status_code == 200
        assert r.json()["username"] == username

    def test_does_not_leak_password(self):
        tokens = register_and_login(unique_user())
        body = requests.get(f"{BASE_URL}/me", headers=auth_headers(tokens["token"])).json()
        assert "password" not in body

    def test_book_count_starts_at_zero(self):
        tokens = register_and_login(unique_user())
        body = requests.get(f"{BASE_URL}/me", headers=auth_headers(tokens["token"])).json()
        assert body["book_count"] == 0

    def test_book_count_reflects_added_books(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id()), headers=h)
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id()), headers=h)
        body = requests.get(f"{BASE_URL}/me", headers=h).json()
        assert body["book_count"] == 2

    def test_book_count_is_per_user(self):
        # Another user's books must not inflate my count.
        other = register_and_login(unique_user())
        requests.post(
            f"{BASE_URL}/add_book",
            json=make_book(unique_book_id()),
            headers=auth_headers(other["token"]),
        )
        me = register_and_login(unique_user())
        body = requests.get(f"{BASE_URL}/me", headers=auth_headers(me["token"])).json()
        assert body["book_count"] == 0
