"""
Integration tests for GET /genres (new endpoint).

/genres returns the distinct list of genres currently present in the database,
sorted alphabetically. The UI uses it to populate a "filter by genre" dropdown.

Response shape (200):
    {"genres": ["Fiction", "Programming", ...]}

The test DB is shared, so these tests assert membership / no-duplicates / sorted
(never an exact full list).

HTTP-only -> Windows-safe.

NOTE (TDD): expected to FAIL until GET /genres is implemented.
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
    return "genre" + uuid.uuid4().hex[:10]


class TestGenres:

    def test_requires_authentication(self):
        assert requests.get(f"{BASE_URL}/genres").status_code in (401, 422)

    def test_returns_a_list_under_genres_key(self):
        r = requests.get(f"{BASE_URL}/genres", headers=_auth())
        assert r.status_code == 200
        assert isinstance(r.json()["genres"], list)

    def test_added_genre_appears_in_the_list(self):
        h = _auth()
        genre = _tag()
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id(), genre=genre), headers=h)
        assert genre in requests.get(f"{BASE_URL}/genres", headers=h).json()["genres"]

    def test_genre_is_not_duplicated(self):
        h = _auth()
        genre = _tag()
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id(), genre=genre), headers=h)
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id(), genre=genre), headers=h)
        genres = requests.get(f"{BASE_URL}/genres", headers=h).json()["genres"]
        assert genres.count(genre) == 1

    def test_genres_are_sorted(self):
        genres = requests.get(f"{BASE_URL}/genres", headers=_auth()).json()["genres"]
        assert genres == sorted(genres)
