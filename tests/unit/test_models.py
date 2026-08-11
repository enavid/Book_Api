"""Unit tests for the SQLAlchemy models (User/Book) against an isolated per-test SQLite DB."""
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Book, User


def _make_user(username="aliceuser"):
    return User(username=username, password="$2b$12$examplehashvaluehere000000000000000000000000000000000")


def _make_book(owner, book_id=1, **overrides):
    fields = dict(
        book_id=book_id,
        book_name="Clean Code",
        book_content="A handbook of agile software craftsmanship.",
        writer="Robert C. Martin",
        published_year=2008,
        rating=5,
        genre="Programming",
        created_at="2024-01-01",
        owner=owner,
    )
    fields.update(overrides)
    return Book(**fields)


class TestUserModel:

    def test_user_row_persists_and_is_queryable(self, session):
        session.add(_make_user("aliceuser"))
        session.commit()
        found = session.scalar(db.select(User).filter_by(username="aliceuser"))
        assert found is not None
        assert found.id is not None  # auto-assigned primary key

    def test_username_must_be_unique(self, session):
        session.add(_make_user("dupuser01"))
        session.commit()
        session.add(_make_user("dupuser01"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_new_user_has_no_books(self, session):
        user = _make_user("lonelyuser")
        session.add(user)
        session.commit()
        assert user.books == []


class TestBookModel:

    def test_book_persists_with_owner(self, session):
        user = _make_user("owneruser")
        session.add(user)
        session.add(_make_book(user, book_id=101))
        session.commit()

        book = session.get(Book, 101)
        assert book is not None
        assert book.owner is user
        assert book.owner_id == user.id

    def test_owner_books_backref_lists_the_book(self, session):
        user = _make_user("writeruser")
        session.add(user)
        session.add(_make_book(user, book_id=201))
        session.commit()
        assert [b.book_id for b in user.books] == [201]

    def test_added_at_defaults_to_today(self, session):
        user = _make_user("todayuser")
        session.add(user)
        session.add(_make_book(user, book_id=301))
        session.commit()
        assert session.get(Book, 301).added_at == date.today()

    def test_cascade_delete_removes_owned_books(self, session):
        user = _make_user("cascadeuser")
        session.add(user)
        session.add(_make_book(user, book_id=401))
        session.add(_make_book(user, book_id=402))
        session.commit()

        session.delete(user)
        session.commit()

        # Deleting the owner must delete their books (cascade="all, delete-orphan").
        assert session.get(Book, 401) is None
        assert session.get(Book, 402) is None


class TestToDict:
    """to_dict() must reproduce the exact public API shape (backward-compat)."""

    EXPECTED_KEYS = {
        "book_name", "book_content", "book_id", "writer", "published_year",
        "rating", "genre", "created_at", "added_at", "added_by",
    }

    def test_to_dict_has_exactly_the_api_keys(self, session):
        user = _make_user("dictuser")
        session.add(user)
        book = _make_book(user, book_id=501)
        session.add(book)
        session.commit()
        assert set(book.to_dict().keys()) == self.EXPECTED_KEYS

    def test_to_dict_added_by_is_owner_username(self, session):
        user = _make_user("mapperuser")
        session.add(user)
        book = _make_book(user, book_id=502)
        session.add(book)
        session.commit()
        assert book.to_dict()["added_by"] == "mapperuser"

    def test_to_dict_added_at_is_iso_string(self, session):
        user = _make_user("isouser")
        session.add(user)
        book = _make_book(user, book_id=503)
        session.add(book)
        session.commit()
        assert book.to_dict()["added_at"] == date.today().strftime("%Y-%m-%d")

    def test_to_dict_preserves_non_ascii_text(self, session):
        # Persian/Unicode content must survive a round-trip through the DB.
        user = _make_user("unicodeuser")
        session.add(user)
        book = _make_book(
            user, book_id=504,
            book_name="کتاب فارسی", writer="نویسنده",
            book_content="متنِ نمونه با emoji 📚",
        )
        session.add(book)
        session.commit()
        d = session.get(Book, 504).to_dict()
        assert d["book_name"] == "کتاب فارسی"
        assert d["writer"] == "نویسنده"
        assert d["book_content"] == "متنِ نمونه با emoji 📚"
