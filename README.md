# Book API

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Flask](https://img.shields.io/badge/Flask-black)
![Auth](https://img.shields.io/badge/Auth-JWT-green)
![License](https://img.shields.io/badge/License-MIT-orange)

A small REST API for managing a personal book library, built with Flask.
It offers JWT authentication, per-user book CRUD, search, filtering, and
interactive API docs. Data is stored in SQLite via SQLAlchemy.

## Features

- JWT auth (signup, login, refresh) with bcrypt password hashing
- Per-user book library: add, view, update, delete, search
- Pagination, filtering (genre / writer / rating) and sorting
- Interactive API docs (Swagger UI)
- SQLite + SQLAlchemy + Alembic migrations
- Full test suite (unit + integration) and lint, wired into CI

## Tech Stack

Flask · Flask-JWT-Extended · Flask-SQLAlchemy · Flask-Migrate · SQLite · Ruff · pytest

## Quick Start

```bash
# 1. Install dependencies into a virtualenv
make setup

# 2. Create your secret (JWT_SECRET_KEY must be >= 32 chars)
cp .env.example .env      # then edit .env and set a real value

# 3. Build the database schema
make db-upgrade

# 4. Run the server
make run
```

The API is now at `http://localhost:5000`, and the interactive docs at
`http://localhost:5000/docs`.

> No `make`? The same steps work manually: create a venv, `pip install -r
> requirements.txt`, set `JWT_SECRET_KEY`, run `flask --app main db upgrade`,
> then `python main.py`.

## API Endpoints

All `/book`-related endpoints require a `Authorization: Bearer <token>` header.

### Auth
| Method | Path              | Description                          |
|--------|-------------------|--------------------------------------|
| POST   | `/signup`         | Register a new user                  |
| POST   | `/login`          | Log in, get access + refresh tokens  |
| POST   | `/refresh_token`  | Get a new access token               |
| GET    | `/me`             | Current user's profile               |
| POST   | `/change_password`| Change the current user's password   |

### Books
| Method | Path                    | Description                                   |
|--------|-------------------------|-----------------------------------------------|
| GET    | `/get_all_book`         | List books (pagination, filter, sort)         |
| GET    | `/my_books`             | List only the current user's books            |
| GET    | `/get_book/<id>`        | Get one book                                  |
| POST   | `/add_book`             | Add a book                                    |
| POST   | `/update_book/<id>`     | Update a book you own                         |
| DELETE | `/delete_book/<id>`     | Delete a book you own                         |
| POST   | `/search`               | Search by name / genre / writer               |
| GET    | `/genres`               | Distinct list of genres                       |
| GET    | `/stats`                | Your library stats (count, avg rating, ...)   |

Full request/response schemas are documented in Swagger UI at `/docs`.

## Testing

```bash
make test          # full pipeline: lint -> unit -> integration
make lint          # ruff only
make test-unit     # in-process unit tests (fast, no server)
make test-integration
```

The same pipeline runs in CI on every push and pull request.

## Project Structure

```
app/            application code (routes, models, helpers, OpenAPI spec)
migrations/     Alembic database migrations
scripts/        one-off scripts (e.g. legacy JSON -> DB import)
tests/          unit/ and integration/ test suites
main.py         app entry point
Makefile        setup / run / test / lint tasks
```

## License

MIT
