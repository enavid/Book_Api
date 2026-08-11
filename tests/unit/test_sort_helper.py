"""
Unit test for the resolve_sort() helper in app/books.py (used by the sorting
feature on GET /get_all_book).

resolve_sort() maps a client-supplied ?sort= value to a real Book column, using
an allow-list. This matters for security: without an allow-list a client could
try to sort by an arbitrary attribute. Unknown / missing keys must fall back to
a safe default (book_id).

Comparing with `is` works because a mapped column attribute (e.g. Book.rating)
is the same object every time it is accessed on the class.

Contract the endpoint code must satisfy:

    SORT_COLUMNS = {
        "book_id": Book.book_id,
        "rating": Book.rating,
        "published_year": Book.published_year,
        "book_name": Book.book_name,
    }
    def resolve_sort(sort_key):
        return SORT_COLUMNS.get(sort_key, Book.book_id)

NOTE (TDD): expected to FAIL until resolve_sort() exists in app/books.py.
"""
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
