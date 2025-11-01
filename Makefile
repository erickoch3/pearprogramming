.PHONY: install api mockapi ui mockui clean help test democontext demoevents

# Virtual environment directory
VENV := .venv
PYTHON := $(VENV)/bin/python
UV := uv

# Check if virtual environment exists
VENV_EXISTS := $(shell [ -d $(VENV) ] && echo 1 || echo 0)

help:
	@echo "Available targets:"
	@echo "  make install    - Create virtual environment and install dependencies"
	@echo "  make api        - Start the FastAPI backend service"
	@echo "  make mockapi    - Start the FastAPI backend with mock data (MOCK=1)"
	@echo "  make ui         - Start the Next.js UI development server"
	@echo "  make mockui     - Start the Next.js UI with mock data (NEXT_PUBLIC_MOCK=1)"
	@echo "  make test       - Run the pytest suite"
	@echo "  make clean      - Remove virtual environment"

install:
	@echo "Setting up virtual environment with uv..."
	@if [ ! -d $(VENV) ]; then \
		$(UV) venv $(VENV); \
		echo "Virtual environment created at $(VENV)"; \
	else \
		echo "Virtual environment already exists at $(VENV)"; \
	fi
	@echo "Installing dependencies from api/requirements.txt..."
	@$(UV) pip install --python $(VENV) -r api/requirements.txt
	@if [ -f api/requirements-dev.txt ]; then \
		echo "Installing development dependencies from api/requirements-dev.txt..."; \
		$(UV) pip install --python $(VENV) -r api/requirements-dev.txt; \
	fi
	@echo "Installation complete!"

api:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Running 'make install'..."; \
		$(MAKE) install; \
	fi
	@echo "Starting FastAPI server..."
	@$(PYTHON) -m uvicorn api.app.main:app --reload --host 0.0.0.0 --port 8000

mockapi:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Running 'make install'..."; \
		$(MAKE) install; \
	fi
	@echo "Starting FastAPI server with mock data..."
	@MOCK=1 $(PYTHON) -m uvicorn api.app.main:app --reload --host 0.0.0.0 --port 8000

ui:
	@echo "Starting Next.js UI development server..."
	@cd ui && yarn run dev

mockui:
	@echo "Starting Next.js UI with mock data..."
	@cd ui && NEXT_PUBLIC_MOCK=1 yarn run dev

test:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Running 'make install'..."; \
		$(MAKE) install; \
	fi
	@echo "Running pytest..."
	@set -a; \
	[ -f .env ] && . .env; \
	set +a; \
	$(PYTHON) -m pytest

democontext:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Running 'make install'..."; \
		$(MAKE) install; \
	fi
	@echo "Gathering demo context..."
	@set -a; \
	[ -f .env ] && . .env; \
	set +a; \
	$(PYTHON) -c 'import json, os; from api.app.services.context_aggregator import ContextAggregator; preferences = os.getenv("PREFERENCES"); context = ContextAggregator().gather_context(preferences); print(json.dumps(context, indent=2, default=str))'

demoevents:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Running 'make install'..."; \
		$(MAKE) install; \
	fi
	@echo "Requesting demo event recommendations..."
	@set -a; \
	[ -f .env ] && . .env; \
	set +a; \
	$(PYTHON) scripts/demo_events.py

clean:
	@echo "Removing virtual environment..."
	@rm -rf $(VENV)
	@echo "Virtual environment removed."
