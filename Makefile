PYTHON     = python3
VENV       = venv
VENV_BIN   = $(VENV)/bin
PIP        = $(VENV_BIN)/pip
PYTEST     = $(VENV_BIN)/pytest
FLASK      = $(VENV_BIN)/python

.DEFAULT_GOAL := help

.PHONY: help setup run stop test test-unit test-integration check clean

help:
	@echo ""
	@echo "  make setup             Create virtualenv and install all dependencies"
	@echo "  make run               Start the API server (dev mode)"
	@echo "  make stop              Stop the running API server"
	@echo "  make test              Run all tests (unit + integration)"
	@echo "  make test-unit         Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make check             Alias for make test"
	@echo "  make clean             Remove cache files and logs"
	@echo ""

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt -q
	@echo ""
	@echo "Setup complete. Run 'make run' to start the server."

run:
	@mkdir -p data/Users
	@if [ -z "$$JWT_SECRET_KEY" ]; then \
		echo "WARNING: JWT_SECRET_KEY not set — using insecure default for dev"; \
		JWT_SECRET_KEY=dev-only-secret-do-not-use-in-production $(FLASK) main.py; \
	else \
		$(FLASK) main.py; \
	fi

stop:
	@pkill -f "python.*main.py" 2>/dev/null && echo "Server stopped." || echo "No server was running."

check: test

test: test-unit test-integration

test-unit:
	@echo "========== Unit Tests =========="
	$(PYTEST) tests/unit/ -v

test-integration:
	@echo "========== Integration Tests =========="
	@mkdir -p data/Users
	JWT_SECRET_KEY=test-secret-key $(PYTEST) tests/integration/ -v --tb=short

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f app.log
	@echo "Clean done."
