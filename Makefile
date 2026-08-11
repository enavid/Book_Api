# Cross-platform Makefile (works on both Linux/macOS and Windows).
#
# Requires GNU Make. On Windows install it once with any of:
#     winget install ezwinports.make      (or)   choco install make   (or)   scoop install make
# then run the same targets (make setup / make run / make test) from cmd or PowerShell.
#
# OS-sensitive work (mkdir, setting env vars, killing the server, cleaning)
# is done through Python one-liners instead of shell built-ins, so the exact
# shell (sh vs cmd.exe) does not matter.

VENV = .venv

ifeq ($(OS),Windows_NT)
    PYTHON := python
    PY     := $(VENV)\Scripts\python.exe
    PIP    := $(VENV)\Scripts\pip.exe
    PYTEST := $(VENV)\Scripts\pytest.exe
    RUFF   := $(VENV)\Scripts\ruff.exe
    STOP   := -taskkill /F /IM python.exe /T
else
    PYTHON := python3
    PY     := $(VENV)/bin/python
    PIP    := $(VENV)/bin/pip
    PYTEST := $(VENV)/bin/pytest
    RUFF   := $(VENV)/bin/ruff
    STOP   := -pkill -f 'python.*main.py'
endif

DEV_SECRET = dev-only-secret-do-not-use-in-production-please

.DEFAULT_GOAL := help

.PHONY: help setup run stop test test-unit test-integration lint lint-fix check clean

help:
	@$(PYTHON) -c "print('\n  make setup             Create virtualenv and install all dependencies\n  make run               Start the API server (dev mode)\n  make stop              Stop the running API server\n  make test              Run the full pipeline: lint -> unit -> integration\n  make lint              Check code style with ruff\n  make lint-fix          Auto-fix what ruff can\n  make test-unit         Run unit tests only\n  make test-integration  Run integration tests only\n  make check             Alias for make test\n  make clean             Remove cache files and logs\n')"

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt -q
	@$(PYTHON) -c "print('\nSetup complete. Run make run to start the server.')"

run:
	@$(PY) -c "import os; os.makedirs('data/Users', exist_ok=True); os.environ.get('JWT_SECRET_KEY') or print('WARNING: JWT_SECRET_KEY not set - using insecure dev default'); os.environ.setdefault('JWT_SECRET_KEY', '$(DEV_SECRET)'); import runpy; runpy.run_path('main.py', run_name='__main__')"

stop:
	@$(STOP)

check: test

# The pipeline order matters: lint first (fast, no server), then the in-process
# unit tests, then the slower integration tests that spin up a real server. A
# failure at any stage stops the ones after it, so you get the cheapest feedback
# first — the same order the CI pipeline runs (.github/workflows/ci.yml).
test: lint test-unit test-integration

lint:
	@$(PYTHON) -c "print('========== Lint (ruff) ==========')"
	$(RUFF) check .

# Convenience: auto-fix what ruff can (import order, unused imports, ...).
lint-fix:
	$(RUFF) check . --fix

test-unit:
	@$(PYTHON) -c "print('========== Unit Tests ==========')"
	$(PYTEST) tests/unit/ -v

test-integration:
	@$(PYTHON) -c "print('========== Integration Tests ==========')"
	@$(PY) -c "import os; os.makedirs('data/Users', exist_ok=True)"
	$(PYTEST) tests/integration/ -v --tb=short

clean:
	@$(PYTHON) -c "import shutil, glob, os; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True)]; [os.remove(f) for f in glob.glob('**/*.pyc', recursive=True)]; (os.path.exists('app.log') and os.remove('app.log')); print('Clean done.')"
db-migrate:
	flask --app main db migrate -m "$(m)"

db-upgrade:
	flask --app main db upgrade