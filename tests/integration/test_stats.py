"""Integration tests for GET /stats: per-user total_books, average_rating, distinct_genres. TDD: red until implemented."""
import requests

from tests.conftest import (
    BASE_URL,
    auth_headers,
    make_book,
    register_and_login,
    unique_book_id,
    unique_user,
)


class TestStatsAuth:

    def test_requires_authentication(self):
        assert requests.get(f"{BASE_URL}/stats").status_code in (401, 422)


class TestStatsContent:

    def test_new_user_has_empty_stats(self):
        h = auth_headers(register_and_login(unique_user())["token"])
        body = requests.get(f"{BASE_URL}/stats", headers=h).json()
        assert body["total_books"] == 0
        assert body["average_rating"] is None
        assert body["distinct_genres"] == 0

    def test_stats_reflect_added_books(self):
        h = auth_headers(register_and_login(unique_user())["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id(), genre="Alpha", rating=4), headers=h)
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id(), genre="Alpha", rating=5), headers=h)
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id(), genre="Beta", rating=3), headers=h)
        body = requests.get(f"{BASE_URL}/stats", headers=h).json()
        assert body["total_books"] == 3
        assert body["average_rating"] == 4.0        # (4 + 5 + 3) / 3
        assert body["distinct_genres"] == 2         # Alpha, Beta

    def test_average_rating_is_rounded_to_two_decimals(self):
        h = auth_headers(register_and_login(unique_user())["token"])
        for rating in (4, 4, 5):
            requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id(), rating=rating), headers=h)
        body = requests.get(f"{BASE_URL}/stats", headers=h).json()
        assert body["average_rating"] == 4.33       # 13/3 = 4.333... -> 4.33

    def test_stats_are_per_user(self):
        # Another user's books must not affect my stats.
        other = auth_headers(register_and_login(unique_user())["token"])
        requests.post(f"{BASE_URL}/add_book", json=make_book(unique_book_id(), rating=5), headers=other)
        me = auth_headers(register_and_login(unique_user())["token"])
        body = requests.get(f"{BASE_URL}/stats", headers=me).json()
        assert body["total_books"] == 0
