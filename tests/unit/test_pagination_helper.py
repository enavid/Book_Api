"""
Unit test for the pagination_meta() helper in app/books.py.

The helper turns a Flask-SQLAlchemy Pagination object into the small dict the
API returns under the "pagination" key. It only READS attributes, so we feed it
a lightweight stand-in (types.SimpleNamespace) instead of hitting a real
database — this keeps the test fast, server-free, and OS-independent.

Contract the endpoint code must satisfy:

    def pagination_meta(pagination):
        return {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        }

NOTE (TDD): expected to FAIL until pagination_meta() exists in app/books.py.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from types import SimpleNamespace

import app.books as books


def _fake_pagination(page, per_page, total, pages):
    # Flask-SQLAlchemy's Pagination exposes exactly these attribute names.
    return SimpleNamespace(page=page, per_page=per_page, total=total, pages=pages)


class TestPaginationMeta:

    def test_maps_all_four_fields(self):
        meta = books.pagination_meta(_fake_pagination(2, 5, 12, 3))
        assert meta == {"page": 2, "per_page": 5, "total": 12, "total_pages": 3}

    def test_public_key_is_total_pages_not_pages(self):
        # The API exposes "total_pages"; the ORM attribute is "pages". The
        # helper must translate the name so the response stays UI-friendly.
        meta = books.pagination_meta(_fake_pagination(1, 10, 0, 0))
        assert "total_pages" in meta and "pages" not in meta

    def test_single_full_page(self):
        meta = books.pagination_meta(_fake_pagination(1, 10, 4, 1))
        assert meta["total"] == 4
        assert meta["total_pages"] == 1
