"""
Unit test for User.summary() (used by GET /me).

summary() returns the small dict the /me endpoint sends:

    {"username": <str>, "book_count": <int>}

It is tested directly against an isolated, per-test SQLite database (see
tests/unit/conftest.py) — no HTTP server, no touching data/app.db. The fixture
releases and deletes the temp DB file, so it is Windows-safe (Windows locks
open files; the fixture disposes the engine before deleting).

Contract the model must satisfy (app/models.py, class User):

    def summary(self) -> dict:
        return {"username": self.username, "book_count": len(self.books)}

NOTE (TDD): expected to FAIL until User.summary() exists.
"""
from app.models import Book, User


def _book(owner, book_id):
    return Book(
        book_id=book_id,
        book_name="B",
        book_content="C",
        writer="W",
        published_year=2020,
        rating=3,
        genre="G",
        created_at="2024-01-01",
        owner=owner,
    )


class TestUserSummary:

    def test_returns_username_and_zero_count_for_new_user(self, session):
        user = User(username="freshuser1", password="x")
        session.add(user)
        session.commit()
        assert user.summary() == {"username": "freshuser1", "book_count": 0}

    def test_book_count_matches_owned_books(self, session):
        user = User(username="counteruser", password="x")
        session.add(user)
        session.add(_book(user, 9001))
        session.add(_book(user, 9002))
        session.commit()
        assert user.summary() == {"username": "counteruser", "book_count": 2}

    def test_summary_never_includes_password(self, session):
        user = User(username="secretuser", password="supersecrethash")
        session.add(user)
        session.commit()
        assert "password" not in user.summary()
