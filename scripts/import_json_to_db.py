"""
One-off migration of the legacy JSON data into the database (issue #45).

Reads:
    data/Users/*.json        -> users table
    data/Book_Loader.json    -> books table

Runs inside app.app_context() so db.session is usable outside any request.
Idempotent: running it again does not create duplicate rows.

Usage:
    python scripts/import_json_to_db.py
"""
import json
import sys
from pathlib import Path

# Running "python scripts/import_json_to_db.py" puts scripts/ (not the project
# root) on sys.path, so `import main` would fail. Add the project root first.
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import bcrypt

from app.extensions import db
from app.models import Book, User
from main import app

USERS_DIR = BASE_DIR / "data" / "Users"
BOOKS_FILE = BASE_DIR / "data" / "Book_Loader.json"


def _looks_hashed(password):
    """bcrypt hashes start with $2a$ / $2b$ / $2y$."""
    return isinstance(password, str) and password.startswith(("$2a$", "$2b$", "$2y$"))


def import_users():
    if not USERS_DIR.exists():
        return

    for file in sorted(USERS_DIR.glob("*.json")):
        with open(file, encoding="utf-8") as f:
            data = json.load(f)

        username = data.get("username") or file.stem
        # Skip users that already exist so re-runs are safe.
        if db.session.scalar(db.select(User).filter_by(username=username)):
            continue

        password = data.get("password", "")
        # Keep an already-hashed password as-is; hash a plaintext one so login
        # (which uses bcrypt.checkpw) keeps working.
        if not _looks_hashed(password):
            password = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt(12)
            ).decode("utf-8")

        db.session.add(User(username=username, password=password))

    db.session.commit()


def import_books():
    if not BOOKS_FILE.exists():
        return

    with open(BOOKS_FILE, encoding="utf-8") as f:
        raw = json.load(f)

    # Book_Loader.json is a dict keyed by book_id ({"1": {...}}); older exports
    # may be a plain list. Handle both.
    books = raw.values() if isinstance(raw, dict) else raw

    for data in books:
        book_id = data.get("book_id")
        if book_id is None:
            continue
        # Skip books already imported so re-runs are safe.
        if db.session.get(Book, book_id):
            continue

        # The owner is stored as a username in the "added_by" field.
        owner = db.session.scalar(
            db.select(User).filter_by(username=data.get("added_by"))
        )
        if owner is None:
            print(f"skip book {book_id}: unknown owner {data.get('added_by')!r}")
            continue

        db.session.add(
            Book(
                book_id=book_id,
                book_name=data["book_name"],
                book_content=data["book_content"],
                writer=data["writer"],
                published_year=data["published_year"],
                rating=data["rating"],
                genre=data["genre"],
                created_at=data.get("created_at", ""),
                owner=owner,
            )
        )

    db.session.commit()


def main():
    with app.app_context():
        db.create_all()
        import_users()
        import_books()
        print("import complete.")


if __name__ == "__main__":
    main()
