"""
Integration tests for filtering & sorting on GET /get_all_book.

New query params (all optional, combine with AND, and keep pagination):
    genre=<str>       only books whose genre matches (case-insensitive, exact)
    writer=<str>      only books whose writer matches (case-insensitive, exact)
    min_rating=<int>  only books with rating >= min_rating
    sort=<field>      one of: book_id | rating | published_year | book_name
    order=asc|desc    default asc

Because /get_all_book returns EVERY user's books and all tests share one DB,
each test tags its books with a unique random genre/writer so its assertions are
deterministic (only its own rows match the filter).

HTTP-only -> Windows-safe.

NOTE (TDD): expected to FAIL until filtering/sorting is implemented.
"""
import uuid

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


def _tag():
    # A unique genre/writer token so a filter isolates exactly this test's rows.
    return "tag" + uuid.uuid4().hex[:10]


class TestGenreFilter:

    def test_filters_by_genre(self):
        h = _auth()
        genre = _tag()
        wanted = [unique_book_id() for _ in range(3)]
        for bid in wanted:
            requests.post(f"{BASE_URL}/add_book", json=make_book(bid, genre=genre), headers=h)
        # A book with a different genre must NOT show up.
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id(), genre=_tag()), headers=h)

        r = requests.get(f"{BASE_URL}/get_all_book?genre={genre}&per_page=1000", headers=h)
        got = {b["book_id"] for b in r.json()["book"]}
        assert got == set(wanted)

    def test_genre_filter_is_case_insensitive(self):
        h = _auth()
        genre = _tag()
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid, genre=genre), headers=h)
        r = requests.get(f"{BASE_URL}/get_all_book?genre={genre.upper()}&per_page=1000", headers=h)
        got = {b["book_id"] for b in r.json()["book"]}
        assert got == {bid}


class TestWriterFilter:

    def test_filters_by_writer(self):
        h = _auth()
        writer = _tag()
        bid = unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(bid, writer=writer), headers=h)
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id(), writer=_tag()), headers=h)
        r = requests.get(f"{BASE_URL}/get_all_book?writer={writer}&per_page=1000", headers=h)
        got = {b["book_id"] for b in r.json()["book"]}
        assert got == {bid}


class TestMinRatingFilter:

    def test_min_rating_filters_out_lower_rated(self):
        h = _auth()
        genre = _tag()
        low, high = unique_book_id(), unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(low, genre=genre, rating=2), headers=h)
        requests.post(f"{BASE_URL}/add_book", json=make_book(high, genre=genre, rating=5), headers=h)
        r = requests.get(f"{BASE_URL}/get_all_book?genre={genre}&min_rating=3&per_page=1000", headers=h)
        got = {b["book_id"] for b in r.json()["book"]}
        assert got == {high}


class TestSorting:

    def _seed_three(self, h, genre):
        low, mid, high = unique_book_id(), unique_book_id(), unique_book_id()
        requests.post(f"{BASE_URL}/add_book", json=make_book(low, genre=genre, rating=1), headers=h)
        requests.post(f"{BASE_URL}/add_book", json=make_book(mid, genre=genre, rating=3), headers=h)
        requests.post(f"{BASE_URL}/add_book", json=make_book(high, genre=genre, rating=5), headers=h)
        return low, mid, high

    def test_sort_by_rating_desc(self):
        h = _auth()
        genre = _tag()
        _, _, high = self._seed_three(h, genre)
        books = requests.get(
            f"{BASE_URL}/get_all_book?genre={genre}&sort=rating&order=desc&per_page=1000",
            headers=h,
        ).json()["book"]
        ratings = [b["rating"] for b in books]
        assert ratings == sorted(ratings, reverse=True)
        assert books[0]["book_id"] == high

    def test_sort_by_rating_defaults_to_ascending(self):
        h = _auth()
        genre = _tag()
        low, _, _ = self._seed_three(h, genre)
        books = requests.get(
            f"{BASE_URL}/get_all_book?genre={genre}&sort=rating&per_page=1000",
            headers=h,
        ).json()["book"]
        ratings = [b["rating"] for b in books]
        assert ratings == sorted(ratings)
        assert books[0]["book_id"] == low

    def test_invalid_sort_field_does_not_error(self):
        # An unknown sort key must be ignored (fall back to default), not 500.
        r = requests.get(f"{BASE_URL}/get_all_book?sort=nonsense&per_page=5", headers=_auth())
        assert r.status_code == 200


class TestFiltersWithPaginationAndCompat:

    def test_no_filters_still_returns_ok(self):
        r = requests.get(f"{BASE_URL}/get_all_book", headers=_auth())
        assert r.status_code == 200
        assert isinstance(r.json()["book"], list)

    def test_pagination_total_reflects_the_filter(self):
        h = _auth()
        genre = _tag()
        for _ in range(3):
            requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id(), genre=genre), headers=h)
        body = requests.get(f"{BASE_URL}/get_all_book?genre={genre}&per_page=2", headers=h).json()
        assert body["pagination"]["total"] == 3
        assert body["pagination"]["total_pages"] == 2
