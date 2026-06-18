import pytest
import requests
from tests.conftest import BASE_URL, unique_user, register, login, register_and_login, auth_headers


class TestSignup:

    def test_valid_signup_returns_200(self):
        r = register(unique_user())
        assert r.status_code == 200
        assert r.json().get("message") == "success"

    def test_username_exactly_8_chars_is_accepted(self):
        r = register("exactly8")
        assert r.status_code == 200

    def test_username_7_chars_returns_400(self):
        r = register("short12")
        assert r.status_code == 400

    def test_username_1_char_returns_400(self):
        r = register("a")
        assert r.status_code == 400

    def test_empty_username_returns_400(self):
        r = requests.post(f"{BASE_URL}/signup", json={"username": "", "password": "Password123"})
        assert r.status_code == 400

    def test_missing_password_field_returns_400(self):
        r = requests.post(f"{BASE_URL}/signup", json={"username": unique_user()})
        assert r.status_code == 400

    def test_missing_username_field_returns_400(self):
        r = requests.post(f"{BASE_URL}/signup", json={"password": "Password123"})
        assert r.status_code == 400

    def test_no_body_returns_400_or_415(self):
        r = requests.post(f"{BASE_URL}/signup")
        assert r.status_code in (400, 415)

    def test_empty_body_returns_400(self):
        r = requests.post(f"{BASE_URL}/signup", json={})
        assert r.status_code == 400

    def test_special_chars_in_username_returns_400(self):
        r = requests.post(f"{BASE_URL}/signup", json={"username": "user@name!!", "password": "Password123"})
        assert r.status_code == 400

    def test_slash_in_username_returns_400(self):
        r = requests.post(f"{BASE_URL}/signup", json={"username": "user/name1", "password": "Password123"})
        assert r.status_code == 400

    def test_path_traversal_in_username_returns_400(self):
        r = requests.post(f"{BASE_URL}/signup", json={"username": "../../etc/passwd", "password": "Password123"})
        assert r.status_code == 400

    def test_dot_dot_username_returns_400(self):
        r = requests.post(f"{BASE_URL}/signup", json={"username": "../../../../root", "password": "Password123"})
        assert r.status_code == 400

    def test_duplicate_username_returns_409(self):
        username = unique_user()
        register(username)
        r = register(username)
        assert r.status_code == 409

    def test_duplicate_username_does_not_overwrite_password(self):
        username = unique_user()
        register(username, password="OriginalPass1")
        register(username, password="HackerPass123")
        r = login(username, password="OriginalPass1")
        assert r.status_code == 200

    def test_integer_password_returns_400(self):
        r = requests.post(f"{BASE_URL}/signup", json={"username": unique_user(), "password": 12345678})
        assert r.status_code == 400

    def test_null_password_returns_400(self):
        r = requests.post(f"{BASE_URL}/signup", json={"username": unique_user(), "password": None})
        assert r.status_code == 400

    def test_password_is_stored_hashed_not_plaintext(self):
        username = unique_user()
        register(username, "PlainPassword1")
        user_file = (
            __import__("pathlib").Path(__file__).resolve().parent.parent.parent
            / "data" / "Users" / f"{username}.json"
        )
        import json
        stored = json.loads(user_file.read_text())
        assert stored["password"] != "PlainPassword1"
        assert stored["password"].startswith("$2b$")


class TestLogin:

    def test_valid_login_returns_token_and_refresh_token(self):
        username = unique_user()
        register(username)
        r = login(username)
        assert r.status_code == 200
        body = r.json()
        assert "token" in body
        assert "refresh_token" in body

    def test_token_is_a_non_empty_string(self):
        username = unique_user()
        register(username)
        r = login(username)
        token = r.json().get("token", "")
        assert isinstance(token, str) and len(token) > 10

    def test_wrong_password_returns_400(self):
        username = unique_user()
        register(username, "CorrectPass1")
        r = login(username, "WrongPass123")
        assert r.status_code == 400

    def test_nonexistent_user_returns_400(self):
        r = login("userdoesnotexistxyz")
        assert r.status_code == 400

    def test_wrong_password_error_message_is_generic(self):
        # Should not reveal whether username exists or password is wrong
        username = unique_user()
        register(username, "CorrectPass1")
        r_wrong_pass = login(username, "WrongPass123")
        r_no_user = login("userdoesnotexistxyz")
        assert r_wrong_pass.json().get("message") == r_no_user.json().get("message")

    def test_missing_password_field_returns_400(self):
        r = requests.post(f"{BASE_URL}/login", json={"username": "someuser12"})
        assert r.status_code == 400

    def test_missing_username_field_returns_400(self):
        r = requests.post(f"{BASE_URL}/login", json={"password": "Password123"})
        assert r.status_code == 400

    def test_no_body_returns_400_or_415(self):
        r = requests.post(f"{BASE_URL}/login")
        assert r.status_code in (400, 415)

    def test_empty_body_returns_400(self):
        r = requests.post(f"{BASE_URL}/login", json={})
        assert r.status_code == 400

    def test_path_traversal_login_attempt_returns_400(self):
        r = requests.post(f"{BASE_URL}/login", json={"username": "../../etc/passwd", "password": "Password123"})
        assert r.status_code == 400

    def test_two_logins_produce_different_tokens(self):
        username = unique_user()
        register(username)
        token1 = login(username).json()["token"]
        token2 = login(username).json()["token"]
        assert token1 != token2


class TestRefreshToken:

    def test_valid_refresh_token_returns_new_access_token(self):
        username = unique_user()
        tokens = register_and_login(username)
        r = requests.post(
            f"{BASE_URL}/refresh_token",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
        )
        assert r.status_code == 200
        assert "token" in r.json()

    def test_new_token_from_refresh_grants_access(self):
        username = unique_user()
        tokens = register_and_login(username)
        new_token = requests.post(
            f"{BASE_URL}/refresh_token",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
        ).json()["token"]
        r = requests.get(f"{BASE_URL}/get_all_book", headers=auth_headers(new_token))
        assert r.status_code == 200

    def test_access_token_cannot_be_used_as_refresh_token(self):
        username = unique_user()
        tokens = register_and_login(username)
        r = requests.post(
            f"{BASE_URL}/refresh_token",
            headers={"Authorization": f"Bearer {tokens['token']}"},
        )
        assert r.status_code in (401, 422)

    def test_no_token_returns_401(self):
        r = requests.post(f"{BASE_URL}/refresh_token")
        assert r.status_code in (401, 422)

    def test_malformed_token_returns_401(self):
        r = requests.post(
            f"{BASE_URL}/refresh_token",
            headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
        )
        assert r.status_code in (401, 422)
