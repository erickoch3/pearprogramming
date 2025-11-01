.PHONY: install api clean help

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
	@echo "Installation complete!"

api:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Running 'make install'..."; \
		$(MAKE) install; \
	fi
	@echo "Starting FastAPI server..."
	@$(PYTHON) -m uvicorn api.app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	@echo "Removing virtual environment..."
	@rm -rf $(VENV)
	@echo "Virtual environment removed."
