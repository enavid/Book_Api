"""Unit tests for the token helpers in app/auth.py (make_token / make_refresh_token), no HTTP server."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, decode_token

import app.auth as auth


@pytest.fixture
def app_ctx():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "unit-test-secret-key-at-least-32-chars-long"
    JWTManager(app)
    with app.app_context():
        yield app


class TestMakeToken:

    def test_returns_non_empty_string(self, app_ctx):
        token = auth.make_token("alice")
        assert isinstance(token, str)
        assert len(token) > 10

    def test_identity_is_encoded_in_token(self, app_ctx):
        token = auth.make_token("alice")
        assert decode_token(token)["sub"] == "alice"

    def test_access_token_type_is_access(self, app_ctx):
        assert decode_token(auth.make_token("bob"))["type"] == "access"

    def test_different_identities_produce_different_tokens(self, app_ctx):
        assert auth.make_token("alice") != auth.make_token("bob")


class TestMakeRefreshToken:

    def test_returns_non_empty_string(self, app_ctx):
        token = auth.make_refresh_token("alice")
        assert isinstance(token, str) and len(token) > 10

    def test_refresh_token_type_is_refresh(self, app_ctx):
        assert decode_token(auth.make_refresh_token("alice"))["type"] == "refresh"

    def test_identity_is_encoded(self, app_ctx):
        assert decode_token(auth.make_refresh_token("carol"))["sub"] == "carol"

    def test_access_and_refresh_tokens_differ(self, app_ctx):
        assert auth.make_token("alice") != auth.make_refresh_token("alice")
