"""
Integration tests for POST /change_password (new endpoint).

Lets an authenticated user change their password. Body:
    {"old_password": "...", "new_password": "..."}

Rules:
- Requires a valid access token.
- The old password must match the stored hash, otherwise the change is rejected
  and the password stays the same.
- On success the new password logs in and the old one no longer does.

HTTP-only -> Windows-safe.

NOTE (TDD): expected to FAIL until POST /change_password is implemented.
"""
import requests

from tests.conftest import (
    BASE_URL,
    auth_headers,
    login,
    register_and_login,
    unique_user,
)


class TestChangePasswordAuth:

    def test_requires_authentication(self):
        r = requests.post(
            f"{BASE_URL}/change_password",
            json={"old_password": "OldPass123", "new_password": "NewPass456"},
        )
        assert r.status_code in (401, 422)


class TestChangePassword:

    def test_successful_change_switches_the_password(self):
        username = unique_user()
        tokens = register_and_login(username, "OldPass123")
        r = requests.post(
            f"{BASE_URL}/change_password",
            json={"old_password": "OldPass123", "new_password": "NewPass456"},
            headers=auth_headers(tokens["token"]),
        )
        assert r.status_code == 200
        # Old password must stop working; new one must work.
        assert login(username, "OldPass123").status_code == 400
        assert login(username, "NewPass456").status_code == 200

    def test_wrong_old_password_is_rejected_and_password_unchanged(self):
        username = unique_user()
        tokens = register_and_login(username, "OldPass123")
        r = requests.post(
            f"{BASE_URL}/change_password",
            json={"old_password": "WrongOld1", "new_password": "NewPass456"},
            headers=auth_headers(tokens["token"]),
        )
        assert r.status_code in (400, 403)
        # The original password must still work.
        assert login(username, "OldPass123").status_code == 200

    def test_missing_new_password_returns_400(self):
        tokens = register_and_login(unique_user(), "OldPass123")
        r = requests.post(
            f"{BASE_URL}/change_password",
            json={"old_password": "OldPass123"},
            headers=auth_headers(tokens["token"]),
        )
        assert r.status_code == 400

    def test_response_does_not_leak_the_password(self):
        username = unique_user()
        tokens = register_and_login(username, "OldPass123")
        r = requests.post(
            f"{BASE_URL}/change_password",
            json={"old_password": "OldPass123", "new_password": "NewPass456"},
            headers=auth_headers(tokens["token"]),
        )
        body = r.json()
        assert "password" not in body
        assert "new_password" not in body
