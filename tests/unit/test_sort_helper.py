"""Unit test for resolve_sort() in app/books.py, an allow-list mapping ?sort= to a column. TDD: red until it exists."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import app.books as books
from app.models import Book


class TestResolveSort:

    def test_known_fields_map_to_their_columns(self):
        assert books.resolve_sort("book_id") is Book.book_id
        assert books.resolve_sort("rating") is Book.rating
        assert books.resolve_sort("published_year") is Book.published_year
        assert books.resolve_sort("book_name") is Book.book_name

    def test_unknown_key_falls_back_to_book_id(self):
        assert books.resolve_sort("nonsense") is Book.book_id

    def test_none_falls_back_to_book_id(self):
        assert books.resolve_sort(None) is Book.book_id
