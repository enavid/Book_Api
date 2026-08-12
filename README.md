# Book API

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Flask](https://img.shields.io/badge/Flask-black)
![Auth](https://img.shields.io/badge/Auth-JWT-green)
![License](https://img.shields.io/badge/License-MIT-orange)

A small REST API for managing a personal book library, built with Flask.
It offers JWT authentication, per-user book CRUD, search, filtering, and
interactive API docs. Data is stored in SQLite via SQLAlchemy.

> 🇮🇷 نسخهٔ فارسی در [پایین همین صفحه](#راهنمای-فارسی) قرار دارد.

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

The API is now at `http://localhost:5000`.

> No `make`? The same steps work manually: create a venv, `pip install -r
> requirements.txt`, set `JWT_SECRET_KEY`, run `flask --app main db upgrade`,
> then `python main.py`.

## API Documentation (Swagger UI)

The project ships with **interactive API docs**. With the server running, open:

```
http://localhost:5000/docs
```

From this page you can read every endpoint, see request/response schemas, and
**call the API directly from the browser**. The raw OpenAPI spec is also served
as JSON at `http://localhost:5000/openapi.json`.

### Trying a protected endpoint

Most endpoints require a JWT. To use them from Swagger UI:

1. Expand **`POST /login`**, click **Try it out**, enter a username and password,
   and **Execute**. Copy the `token` from the response.
2. Click the green **Authorize** button at the top of the page.
3. Paste just the access token (Swagger adds the `Bearer` prefix for you) and
   click **Authorize**, then **Close**.
4. Now any endpoint you run will include your token. Try **`GET /me`** or
   **`GET /get_all_book`**.

> The Swagger UI assets are bundled with the app, so the docs page works fully
> offline (no internet / CDN required).

## API Endpoints

All book endpoints (and `/me`, `/change_password`, `/stats`) require an
`Authorization: Bearer <token>` header.

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

## Testing

```bash
make test          # full pipeline: lint -> unit -> integration
make lint          # ruff only
make test-unit     # in-process unit tests (fast, no server)
make test-integration
```

The same pipeline runs in CI on every push and pull request, followed by a
Docker image build.

## Docker

```bash
docker build -t book-api .
docker run -e JWT_SECRET_KEY=a-very-long-secret-key-min-32-chars -p 5000:5000 book-api
```

Then open the docs at `http://localhost:5000/docs`.

## Project Structure

```
app/            application code (routes, models, helpers, OpenAPI spec)
migrations/     Alembic database migrations
scripts/        one-off scripts (e.g. legacy JSON -> DB import)
tests/          unit/ and integration/ test suites
main.py         app entry point
Dockerfile      container image definition
Makefile        setup / run / test / lint tasks
```

## License

MIT

---

<a name="راهنمای-فارسی"></a>

# 🇮🇷 راهنمای فارسی

یک REST API کوچک برای مدیریت کتابخانهٔ شخصیِ کتاب، ساخته‌شده با Flask.
شاملِ احراز هویت با JWT، عملیاتِ CRUD روی کتاب‌ها (مخصوصِ هر کاربر)، جست‌وجو،
فیلتر، و مستنداتِ تعاملیِ API. داده‌ها در SQLite (از طریق SQLAlchemy) ذخیره می‌شوند.

## امکانات

- احراز هویت با JWT (ثبت‌نام، ورود، refresh) و هشِ رمز با bcrypt
- کتابخانهٔ مخصوصِ هر کاربر: افزودن، مشاهده، ویرایش، حذف، جست‌وجو
- صفحه‌بندی، فیلتر (ژانر / نویسنده / امتیاز) و مرتب‌سازی
- مستنداتِ تعاملیِ API (Swagger UI)
- SQLite به‌همراه SQLAlchemy و مهاجرت‌های Alembic
- مجموعه‌تستِ کامل (unit و integration) و lint، متصل به CI

## پشتهٔ فناوری

Flask · Flask-JWT-Extended · Flask-SQLAlchemy · Flask-Migrate · SQLite · Ruff · pytest

## شروع سریع

```bash
# ۱) نصب وابستگی‌ها در یک virtualenv
make setup

# ۲) ساختِ کلیدِ محرمانه (JWT_SECRET_KEY باید حداقل ۳۲ کاراکتر باشد)
cp .env.example .env      # سپس .env را باز کن و یک مقدار واقعی بگذار

# ۳) ساختِ اسکیمای دیتابیس
make db-upgrade

# ۴) اجرای سرور
make run
```

حالا API روی `http://localhost:5000` بالا است.

> `make` نداری؟ همین مراحل دستی هم کار می‌کند: یک venv بساز، `pip install -r
> requirements.txt` بزن، `JWT_SECRET_KEY` را ست کن، `flask --app main db upgrade`
> را اجرا کن و بعد `python main.py`.

## مستندات API (رابط Swagger)

پروژه یک صفحهٔ **مستنداتِ تعاملی** دارد. وقتی سرور در حال اجراست، این آدرس را باز کن:

```
http://localhost:5000/docs
```

از این صفحه می‌توانی همهٔ اندپوینت‌ها را ببینی، ساختارِ درخواست/پاسخ را بخوانی، و
**مستقیم از داخلِ مرورگر API را صدا بزنی**. خودِ specِ خامِ OpenAPI هم به‌صورت JSON
روی `http://localhost:5000/openapi.json` سرو می‌شود.

### امتحانِ یک اندپوینتِ محافظت‌شده

بیشتر اندپوینت‌ها به توکنِ JWT نیاز دارند. برای استفاده از آن‌ها در Swagger:

1. روی **`POST /login`** بزن، **Try it out** را انتخاب کن، نام کاربری و رمز را
   وارد و **Execute** کن. مقدارِ `token` را از پاسخ کپی کن.
2. دکمهٔ سبزِ **Authorize** در بالای صفحه را بزن.
3. فقط خودِ توکن را بچسبان (پیشوندِ `Bearer` را خودِ Swagger اضافه می‌کند)، بعد
   **Authorize** و سپس **Close** را بزن.
4. حالا هر اندپوینتی که اجرا کنی توکنت را همراه دارد. **`GET /me`** یا
   **`GET /get_all_book`** را امتحان کن.

> فایل‌های استاتیکِ Swagger همراهِ خودِ اپ می‌آیند، پس صفحهٔ مستندات کاملاً
> **آفلاین** کار می‌کند (نیازی به اینترنت یا CDN نیست).

## فهرست اندپوینت‌ها

همهٔ اندپوینت‌های کتاب (و `/me`، `/change_password`، `/stats`) به هدرِ
`Authorization: Bearer <token>` نیاز دارند.

### احراز هویت
| متد   | مسیر               | توضیح                               |
|--------|--------------------|--------------------------------------|
| POST   | `/signup`          | ثبت‌نامِ کاربر جدید                   |
| POST   | `/login`           | ورود و دریافتِ توکنِ access و refresh |
| POST   | `/refresh_token`   | دریافتِ توکنِ access جدید             |
| GET    | `/me`              | پروفایلِ کاربرِ فعلی                  |
| POST   | `/change_password` | تغییرِ رمزِ کاربرِ فعلی               |

### کتاب‌ها
| متد   | مسیر                    | توضیح                                    |
|--------|-------------------------|------------------------------------------|
| GET    | `/get_all_book`         | فهرستِ کتاب‌ها (صفحه‌بندی، فیلتر، مرتب‌سازی) |
| GET    | `/my_books`             | فقط کتاب‌های کاربرِ فعلی                  |
| GET    | `/get_book/<id>`        | گرفتنِ یک کتاب                            |
| POST   | `/add_book`             | افزودنِ کتاب                             |
| POST   | `/update_book/<id>`     | ویرایشِ کتابی که مالکش هستی               |
| DELETE | `/delete_book/<id>`     | حذفِ کتابی که مالکش هستی                  |
| POST   | `/search`               | جست‌وجو بر اساسِ نام / ژانر / نویسنده     |
| GET    | `/genres`               | فهرستِ یکتای ژانرها                       |
| GET    | `/stats`                | آمارِ کتابخانه‌ات (تعداد، میانگینِ امتیاز) |

## تست‌ها

```bash
make test          # کلِ پایپ‌لاین: lint -> unit -> integration
make lint          # فقط ruff
make test-unit     # تست‌های درون‌حافظه‌ای (سریع، بدون سرور)
make test-integration
```

همین پایپ‌لاین در CI روی هر push و pull request اجرا می‌شود و در انتها ایمیجِ
Docker هم ساخته می‌شود.

## داکر

```bash
docker build -t book-api .
docker run -e JWT_SECRET_KEY=a-very-long-secret-key-min-32-chars -p 5000:5000 book-api
```

بعد مستندات را روی `http://localhost:5000/docs` باز کن.

## ساختار پروژه

```
app/            کدِ اپلیکیشن (مسیرها، مدل‌ها، هلپرها، specِ OpenAPI)
migrations/     مهاجرت‌های دیتابیسِ Alembic
scripts/        اسکریپت‌های یک‌بارمصرف (مثلِ importِ JSON قدیمی به DB)
tests/          تست‌های unit/ و integration/
main.py         نقطهٔ ورودِ اپ
Dockerfile      تعریفِ ایمیجِ کانتینر
Makefile        تسک‌های setup / run / test / lint
```

## مجوز

MIT
