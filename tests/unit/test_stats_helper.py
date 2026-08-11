"""Unit test for book_stats() in app/books.py. TDD: red until it exists."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from types import SimpleNamespace

import app.books as books


def _book(rating, genre):
    return SimpleNamespace(rating=rating, genre=genre)


class TestBookStats:

    def test_empty_list_gives_zero_and_none(self):
        assert books.book_stats([]) == {
            "total_books": 0,
            "average_rating": None,
            "distinct_genres": 0,
        }

    def test_counts_average_and_distinct_genres(self):
        stats = books.book_stats([_book(4, "A"), _book(5, "A"), _book(3, "B")])
        assert stats["total_books"] == 3
        assert stats["average_rating"] == 4.0
        assert stats["distinct_genres"] == 2

    def test_average_is_rounded_to_two_decimals(self):
        stats = books.book_stats([_book(4, "A"), _book(4, "A"), _book(5, "A")])
        assert stats["average_rating"] == 4.33
        assert stats["distinct_genres"] == 1
