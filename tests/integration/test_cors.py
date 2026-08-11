"""
Integration tests for CORS support.

A separate front-end (e.g. a React SPA served from another origin such as
http://localhost:5173) cannot call this API from the browser unless the server
sends CORS headers. After Flask-CORS is enabled, every response must carry an
Access-Control-Allow-Origin header, and a pre-flight OPTIONS request must
succeed.

HTTP-only -> identical behaviour on Windows and Linux.

NOTE (TDD): expected to FAIL until Flask-CORS is installed and enabled.
"""
import requests

from tests.conftest import BASE_URL, auth_headers, register_and_login, unique_user


class TestCorsHeaders:

    def test_response_has_allow_origin_header(self):
        tokens = register_and_login(unique_user())
        r = requests.get(
            f"{BASE_URL}/get_all_book",
            headers={**auth_headers(tokens["token"]), "Origin": "http://localhost:5173"},
        )
        assert "Access-Control-Allow-Origin" in r.headers

    def test_preflight_options_is_allowed(self):
        # Browsers send an OPTIONS pre-flight before a cross-origin POST.
        r = requests.options(
            f"{BASE_URL}/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert r.status_code in (200, 204)
        assert "Access-Control-Allow-Origin" in r.headers

    def test_allow_origin_wildcards_or_reflects_origin(self):
        r = requests.get(
            f"{BASE_URL}/get_all_book",
            headers={"Origin": "http://localhost:5173"},
        )
        allow = r.headers.get("Access-Control-Allow-Origin", "")
        assert allow in ("*", "http://localhost:5173")
