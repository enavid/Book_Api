"""Infrastructure tests for the DB plumbing (migration, DATABASE_URL override, import script) via subprocesses; some are TDD-red."""
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
JWT = "infra-test-secret-key-very-long-and-secure-000"

# The garbage env-var name main.py once read for the DB URL instead of "DATABASE_URL" (issues #46/#47); test_database_url_env_var_is_honored exposes the mismatch.
CURRENT_DB_ENV_KEY = "kx%40jj5%2Fg"


def _base_env(**extra):
    env = os.environ.copy()
    env["JWT_SECRET_KEY"] = JWT
    env.pop(CURRENT_DB_ENV_KEY, None)  # start from a clean slate
    env.update(extra)
    return env


def _fresh_db_path():
    fd, path = tempfile.mkstemp(suffix=".db", prefix="infra_test_")
    os.close(fd)
    os.remove(path)  # we want the filename, not an empty file
    return path


def _sqlite_url(path):
    # Forward slashes so the URL parses on Windows too (C:\x -> C:/x).
    return "sqlite:///" + Path(path).as_posix()


def _sqlite_tables(db_path):
    if not os.path.exists(db_path):
        return set()
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    finally:
        con.close()
    return {r[0] for r in rows}


class TestDatabaseUrlOverride:
    """Issue #40/#47: the DB connection string must be overridable via the DATABASE_URL env var."""

    def test_database_url_env_var_is_honored(self):
        # EXPECTED TO FAIL (open bug): main.py read os.environ.get('kx%40jj5%2Fg') instead of 'DATABASE_URL', so DATABASE_URL was ignored.
        custom = _fresh_db_path()
        code = (
            "import main;"
            "print('URI_MARKER=' + main.app.config['SQLALCHEMY_DATABASE_URI'])"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(PROJECT_DIR),
            env=_base_env(DATABASE_URL=_sqlite_url(custom)),
            capture_output=True, text=True,
        )
        marker = next(
            (ln for ln in proc.stdout.splitlines() if ln.startswith("URI_MARKER=")),
            "",
        )
        # Compare on the slash-free filename so this holds on Windows too
        # (the URI uses forward slashes, a raw Windows path uses backslashes).
        assert os.path.basename(custom) in marker, (
            "DATABASE_URL was ignored; app used: " + marker
        )


class TestMigrationsBuildSchema:
    """Issue #42: flask db upgrade must build the whole schema from an empty DB (the migration must create_table, not only alter)."""

    def test_fresh_upgrade_creates_users_and_books_tables(self):
        # EXPECTED TO FAIL (open bug #42): the migration cannot create the tables
        # from scratch, so a fresh clone / CI has no way to build the database.
        db_path = _fresh_db_path()
        # Set both the (buggy) current key and the intended DATABASE_URL so this
        # test keeps working once #40 is fixed.
        env = _base_env(
            DATABASE_URL=_sqlite_url(db_path),
            **{CURRENT_DB_ENV_KEY: _sqlite_url(db_path)},
        )
        proc = subprocess.run(
            [sys.executable, "-m", "flask", "--app", "main", "db", "upgrade"],
            cwd=str(PROJECT_DIR), env=env,
            capture_output=True, text=True,
        )
        tables = _sqlite_tables(db_path)
        if os.path.exists(db_path):
            os.remove(db_path)
        assert proc.returncode == 0, (
            "flask db upgrade failed on a fresh DB:\n" + proc.stderr[-800:]
        )
        assert {"users", "books"}.issubset(tables), (
            "tables after upgrade: " + str(tables)
        )


class TestJsonImportScript:
    """Issue #45: scripts/import_json_to_db.py must move legacy JSON data into the database."""

    def test_import_script_exists(self):
        # EXPECTED TO FAIL (open bug #45): the script was never written; the
        # scripts/ directory does not even exist.
        script = PROJECT_DIR / "scripts" / "import_json_to_db.py"
        assert script.exists(), f"missing data-migration script: {script}"
