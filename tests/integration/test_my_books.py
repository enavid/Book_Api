"""
Integration tests for GET /my_books (new endpoint).

/my_books returns ONLY the books owned by the currently authenticated user,
paginated exactly like /get_all_book. It is the "My Library" feed the UI needs:
/get_all_book returns every user's books and cannot be used for that.

Response shape (200):

    {
      "book": [ {book...}, ... ],           # only the caller's books
      "pagination": {"page", "per_page", "total", "total_pages"}
    }

HTTP-only tests (requests against the conftest server) -> OS-independent, so
they run identically on Windows.

NOTE (TDD): expected to FAIL until GET /my_books is implemented.
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


class TestMyBooksAuth:

    def test_requires_authentication(self):
        assert requests.get(f"{BASE_URL}/my_books").status_code in (401, 422)

    def test_invalid_token_returns_401(self):
        r = requests.get(f"{BASE_URL}/my_books", headers={"Authorization": "Bearer nope.nope.nope"})
        assert r.status_code in (401, 422)


class TestMyBooksContent:

    def test_returns_book_key_as_list(self):
        tokens = register_and_login(unique_user())
        r = requests.get(f"{BASE_URL}/my_books", headers=auth_headers(tokens["token"]))
        assert r.status_code == 200
        assert isinstance(r.json()["book"], list)

    def test_new_user_has_no_books(self):
        tokens = register_and_login(unique_user())
        r = requests.get(f"{BASE_URL}/my_books", headers=auth_headers(tokens["token"]))
        assert r.json()["book"] == []

    def test_returns_only_callers_books(self):
        # Alice adds 2 books, Bob adds 1. Each must see only their own.
        alice = register_and_login(unique_user())
        ah = auth_headers(alice["token"])
        bob = register_and_login(unique_user())
        bh = auth_headers(bob["token"])
        a1, a2, b1 = unique_book_id(), unique_book_id(), unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(a1), headers=ah)
        requests.post(f"{BASE_URL}/add_book", json=make_book(a2), headers=ah)
        requests.post(f"{BASE_URL}/add_book", json=make_book(b1), headers=bh)

        alice_ids = {b["book_id"] for b in requests.get(f"{BASE_URL}/my_books?per_page=1000", headers=ah).json()["book"]}
        bob_ids = {b["book_id"] for b in requests.get(f"{BASE_URL}/my_books?per_page=1000", headers=bh).json()["book"]}
        assert alice_ids == {a1, a2}
        assert bob_ids == {b1}

    def test_added_by_is_always_the_caller(self):
        username = unique_user()
        tokens = register_and_login(username)
        h = auth_headers(tokens["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id()), headers=h)
        books = requests.get(f"{BASE_URL}/my_books?per_page=1000", headers=h).json()["book"]
        assert books and all(b["added_by"] == username for b in books)


class TestMyBooksPagination:

    def _seed(self, headers, n):
        for _ in range(n):
            requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id()), headers=headers)

    def test_per_page_limits_items(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        self._seed(h, 3)
        r = requests.get(f"{BASE_URL}/my_books?page=1&per_page=2", headers=h)
        assert len(r.json()["book"]) == 2

    def test_per_page_zero_returns_empty_list(self):
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        self._seed(h, 1)
        r = requests.get(f"{BASE_URL}/my_books?per_page=0", headers=h)
        assert r.json()["book"] == []

    def test_pagination_meta_matches_owned_total(self):
        # A fresh user owns exactly the books they added, so their total is exact
        # (unlike /get_all_book, which is shared across the whole test session).
        tokens = register_and_login(unique_user())
        h = auth_headers(tokens["token"])
        self._seed(h, 3)
        meta = requests.get(f"{BASE_URL}/my_books?page=1&per_page=2", headers=h).json()["pagination"]
        assert meta["total"] == 3
        assert meta["per_page"] == 2
        assert meta["page"] == 1
        assert meta["total_pages"] == math.ceil(3 / 2)
