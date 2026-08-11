"""
Integration tests for the pagination metadata added to GET /get_all_book.

The endpoint keeps its existing "book" list (backward-compatible) and now ALSO
returns a "pagination" object so the UI can render page controls:

    {
      "book": [...],
      "pagination": {"page", "per_page", "total", "total_pages"}
    }

/get_all_book returns EVERY user's books and all tests share one database, so
these tests assert structure and internal consistency (e.g. total_pages derived
from total and per_page) rather than absolute global counts.

HTTP-only -> Windows-safe.

NOTE (TDD): expected to FAIL until the "pagination" object is added.
"""
import math

import requests

from tests.conftest import (
    BASE_URL,
    auth_headers,
    make_book,
    register_and_login,
    unique_book_id,
    unique_user,
)


def _auth():
    return auth_headers(register_and_login(unique_user())["token"])


class TestPaginationMetaShape:

    def test_response_still_has_book_list(self):
        # Backward-compatibility: existing clients read body["book"].
        body = requests.get(f"{BASE_URL}/get_all_book", headers=_auth()).json()
        assert isinstance(body["book"], list)

    def test_response_has_pagination_object(self):
        body = requests.get(f"{BASE_URL}/get_all_book", headers=_auth()).json()
        assert set(body["pagination"]) == {"page", "per_page", "total", "total_pages"}


class TestPaginationMetaValues:

    def test_echoes_requested_page_and_per_page(self):
        body = requests.get(f"{BASE_URL}/get_all_book?page=2&per_page=3", headers=_auth()).json()
        assert body["pagination"]["page"] == 2
        assert body["pagination"]["per_page"] == 3

    def test_total_is_at_least_items_returned(self):
        h = _auth()
        for _ in range(3):
            requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id()), headers=h)
        body = requests.get(f"{BASE_URL}/get_all_book?page=1&per_page=100", headers=h).json()
        assert body["pagination"]["total"] >= len(body["book"])

    def test_total_pages_matches_total_and_per_page(self):
        body = requests.get(f"{BASE_URL}/get_all_book?page=1&per_page=5", headers=_auth()).json()
        meta = body["pagination"]
        assert meta["total_pages"] == math.ceil(meta["total"] / meta["per_page"])
