"""OpenAPI 3.0 spec (served at /openapi.json) and Swagger UI wiring (at /docs) for the Book API."""
from flask import Blueprint, jsonify

SWAGGER_URL = "/docs"          # where the interactive UI is mounted
API_URL = "/openapi.json"      # where the UI fetches the spec from


# --- reusable pieces -------------------------------------------------------

_BEARER = [{"bearerAuth": []}]

_MESSAGE_SCHEMA = {
    "type": "object",
    "properties": {"message": {"type": "string"}},
}


spec = {
    "openapi": "3.0.3",
    "info": {
        "title": "Book API",
        "version": "1.0.0",
        "description": (
            "A small book-library REST API (a learning project). "
            "Authentication uses JWT: call POST /login, then send the access "
            "token as `Authorization: Bearer <token>` on protected endpoints."
        ),
    },
    "servers": [{"url": "/"}],
    "tags": [
        {"name": "Auth", "description": "Sign up, log in, tokens, profile"},
        {"name": "Books", "description": "Create, read, update, delete and search books"},
    ],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        },
        "schemas": {
            "Credentials": {
                "type": "object",
                "required": ["username", "password"],
                "properties": {
                    "username": {"type": "string", "example": "aliceuser"},
                    "password": {"type": "string", "example": "Password123"},
                },
            },
            "TokenResponse": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "example": "success"},
                    "token": {"type": "string"},
                    "refresh_token": {"type": "string"},
                },
            },
            "MeResponse": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "example": "aliceuser"},
                    "book_count": {"type": "integer", "example": 3},
                },
            },
            "BookInput": {
                "type": "object",
                "required": [
                    "book_name", "book_content", "book_id", "writer",
                    "published_year", "rating", "genre", "created_at",
                ],
                "properties": {
                    "book_name": {"type": "string", "example": "Clean Code"},
                    "book_content": {"type": "string", "example": "A handbook of agile software craftsmanship."},
                    "book_id": {"type": "integer", "example": 101},
                    "writer": {"type": "string", "example": "Robert C. Martin"},
                    "published_year": {"type": "integer", "example": 2008},
                    "rating": {"type": "integer", "minimum": 0, "maximum": 5, "example": 5},
                    "genre": {"type": "string", "example": "Programming"},
                    "created_at": {"type": "string", "example": "2024-01-01"},
                },
            },
            "Book": {
                "type": "object",
                "properties": {
                    "book_name": {"type": "string"},
                    "book_content": {"type": "string"},
                    "book_id": {"type": "integer"},
                    "writer": {"type": "string"},
                    "published_year": {"type": "integer"},
                    "rating": {"type": "integer"},
                    "genre": {"type": "string"},
                    "created_at": {"type": "string"},
                    "added_at": {"type": "string", "example": "2024-01-01"},
                    "added_by": {"type": "string", "example": "aliceuser"},
                },
            },
            "Pagination": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "example": 1},
                    "per_page": {"type": "integer", "example": 10},
                    "total": {"type": "integer", "example": 42},
                    "total_pages": {"type": "integer", "example": 5},
                },
            },
            "BookList": {
                "type": "object",
                "properties": {
                    "book": {"type": "array", "items": {"$ref": "#/components/schemas/Book"}},
                    "pagination": {"$ref": "#/components/schemas/Pagination"},
                },
            },
            "Message": _MESSAGE_SCHEMA,
        },
    },
    "paths": {
        "/signup": {
            "post": {
                "tags": ["Auth"],
                "summary": "Register a new user",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Credentials"}}},
                },
                "responses": {
                    "200": {"description": "Created", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Message"}}}},
                    "400": {"description": "Invalid input"},
                    "409": {"description": "Username already exists"},
                },
            }
        },
        "/login": {
            "post": {
                "tags": ["Auth"],
                "summary": "Log in and receive access + refresh tokens",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Credentials"}}},
                },
                "responses": {
                    "200": {"description": "Success", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/TokenResponse"}}}},
                    "400": {"description": "Bad credentials or invalid input"},
                },
            }
        },
        "/refresh_token": {
            "post": {
                "tags": ["Auth"],
                "summary": "Exchange a refresh token for a new access token",
                "description": "Send the REFRESH token in the Authorization header.",
                "security": _BEARER,
                "responses": {
                    "200": {"description": "New access token", "content": {"application/json": {"schema": {"type": "object", "properties": {"token": {"type": "string"}}}}}},
                    "401": {"description": "Missing or invalid refresh token"},
                    "422": {"description": "Wrong token type"},
                },
            }
        },
        "/me": {
            "get": {
                "tags": ["Auth"],
                "summary": "Get the current user's profile",
                "security": _BEARER,
                "responses": {
                    "200": {"description": "Profile", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MeResponse"}}}},
                    "401": {"description": "Not authenticated"},
                },
            }
        },
        "/get_all_book": {
            "get": {
                "tags": ["Books"],
                "summary": "List all books (paginated)",
                "security": _BEARER,
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "per_page", "in": "query", "schema": {"type": "integer", "default": 10}},
                ],
                "responses": {
                    "200": {"description": "A page of books", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/BookList"}}}},
                    "401": {"description": "Not authenticated"},
                },
            }
        },
        "/my_books": {
            "get": {
                "tags": ["Books"],
                "summary": "List only the current user's books (paginated)",
                "security": _BEARER,
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "per_page", "in": "query", "schema": {"type": "integer", "default": 10}},
                ],
                "responses": {
                    "200": {"description": "A page of the caller's books", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/BookList"}}}},
                    "401": {"description": "Not authenticated"},
                },
            }
        },
        "/add_book": {
            "post": {
                "tags": ["Books"],
                "summary": "Add a new book",
                "security": _BEARER,
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/BookInput"}}},
                },
                "responses": {
                    "201": {"description": "Created"},
                    "400": {"description": "Invalid input or duplicate book_id"},
                    "401": {"description": "Not authenticated"},
                },
            }
        },
        "/get_book/{book_id}": {
            "get": {
                "tags": ["Books"],
                "summary": "Get a single book by id",
                "security": _BEARER,
                "parameters": [
                    {"name": "book_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                ],
                "responses": {
                    "200": {"description": "The book", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Book"}}}},
                    "404": {"description": "Not found"},
                    "401": {"description": "Not authenticated"},
                },
            }
        },
        "/update_book/{book_id}": {
            "post": {
                "tags": ["Books"],
                "summary": "Update a book you own",
                "security": _BEARER,
                "parameters": [
                    {"name": "book_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/BookInput"}}},
                },
                "responses": {
                    "200": {"description": "Updated"},
                    "400": {"description": "Invalid input"},
                    "403": {"description": "Not the owner"},
                    "404": {"description": "Not found"},
                    "401": {"description": "Not authenticated"},
                },
            }
        },
        "/delete_book/{book_id}": {
            "delete": {
                "tags": ["Books"],
                "summary": "Delete a book you own",
                "security": _BEARER,
                "parameters": [
                    {"name": "book_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                ],
                "responses": {
                    "200": {"description": "Deleted"},
                    "403": {"description": "Not the owner"},
                    "404": {"description": "Not found"},
                    "401": {"description": "Not authenticated"},
                },
            }
        },
        "/search": {
            "post": {
                "tags": ["Books"],
                "summary": "Search books by name, genre or writer",
                "description": "Provide at least one of the fields; matching is case-insensitive and partial.",
                "security": _BEARER,
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "book_name": {"type": "string"},
                            "genre": {"type": "string"},
                            "writer": {"type": "string"},
                        },
                    }}},
                },
                "responses": {
                    "200": {"description": "Matching books", "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Book"}}}}},
                    "400": {"description": "No search field provided"},
                    "401": {"description": "Not authenticated"},
                },
            }
        },
    },
}


openapi_bp = Blueprint("openapi", __name__)


@openapi_bp.route(API_URL)
def openapi_json():
    """Serve the OpenAPI spec as JSON for the Swagger UI to consume."""
    return jsonify(spec)
