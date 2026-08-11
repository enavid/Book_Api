"""
Integration tests for the API documentation (Swagger / OpenAPI).

Verifies that GET /openapi.json serves a valid OpenAPI 3 spec listing every
implemented endpoint, and that GET /docs serves the interactive Swagger UI.

HTTP-only -> Windows-safe.
"""
import requests

from tests.conftest import BASE_URL

# Every endpoint that is currently implemented and must appear in the spec.
EXPECTED_PATHS = {
    "/signup",
    "/login",
    "/refresh_token",
    "/me",
    "/get_all_book",
    "/my_books",
    "/add_book",
    "/get_book/{book_id}",
    "/update_book/{book_id}",
    "/delete_book/{book_id}",
    "/search",
}


class TestOpenApiSpec:

    def test_openapi_json_is_served(self):
        r = requests.get(f"{BASE_URL}/openapi.json")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("Content-Type", "")

    def test_spec_is_openapi_3(self):
        spec = requests.get(f"{BASE_URL}/openapi.json").json()
        assert spec["openapi"].startswith("3.")
        assert spec["info"]["title"] == "Book API"

    def test_spec_lists_every_implemented_endpoint(self):
        spec = requests.get(f"{BASE_URL}/openapi.json").json()
        assert EXPECTED_PATHS <= set(spec["paths"].keys())

    def test_spec_declares_jwt_bearer_security(self):
        spec = requests.get(f"{BASE_URL}/openapi.json").json()
        schemes = spec["components"]["securitySchemes"]
        assert schemes["bearerAuth"]["scheme"] == "bearer"
        assert schemes["bearerAuth"]["bearerFormat"] == "JWT"


class TestSwaggerUi:

    def test_docs_page_is_served(self):
        r = requests.get(f"{BASE_URL}/docs/")
        assert r.status_code == 200
        assert "swagger-ui" in r.text.lower()
