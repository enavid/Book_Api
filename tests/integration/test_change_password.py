"""Integration tests for POST /change_password. TDD: red until implemented."""
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
