# app/models.py
from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(60), nullable=False)

    books: Mapped[list["Book"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    def summary(self) -> dict:
        return {"username": self.username, "book_count": len(self.books)}


class Book(db.Model):
    __tablename__ = "books"

    book_id: Mapped[int] = mapped_column(primary_key=True)
    book_name: Mapped[str] = mapped_column(String(200), nullable=False)
    book_content: Mapped[str] = mapped_column(Text, nullable=False)
    writer: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    published_year: Mapped[int] = mapped_column(nullable=False)
    rating: Mapped[int] = mapped_column(nullable=False)
    genre: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    created_at: Mapped[str] = mapped_column(String(20), nullable=False)
    added_at: Mapped[date] = mapped_column(default=date.today, nullable=False)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship(back_populates="books")

    def to_dict(self) -> dict:
        return {
            "book_name": self.book_name,
            "book_content": self.book_content,
            "book_id": self.book_id,
            "writer": self.writer,
            "published_year": self.published_year,
            "rating": self.rating,
            "genre": self.genre,
            "created_at": self.created_at,
            "added_at": self.added_at.strftime("%Y-%m-%d"),
            "added_by": self.owner.username,
        }
