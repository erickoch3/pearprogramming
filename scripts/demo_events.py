#!/usr/bin/env python3
"""Trigger the /events/recommendations endpoint and print the JSON payload."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.app.main import app


def build_request_payload() -> Dict[str, Any]:
    """Construct the request body from environment variables."""
    number_events_raw = os.getenv("NUMBER_EVENTS", "5")
    try:
        number_events = int(number_events_raw)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError(
            f"NUMBER_EVENTS must be an integer, got '{number_events_raw}'."
        ) from exc

    preferences = os.getenv("PREFERENCES")
    payload: Dict[str, Any] = {
        "number_events": max(1, number_events),
        "response_preferences": preferences,
    }
    return payload


def main() -> None:
    """Call the FastAPI endpoint and pretty-print the response."""
    payload = build_request_payload()

    with TestClient(app) as client:
        response = client.post("/events/recommendations", json=payload)
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2, default=str))


if __name__ == "__main__":
    main()
