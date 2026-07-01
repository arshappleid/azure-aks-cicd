import re
from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app, hello_world

client = TestClient(app)

# ── Unit Tests ────────────────────────────────────────────────────────────────

class TestHelloWorldUnit:
    def test_returns_dict(self):
        """hello_world() should return a dictionary."""
        result = hello_world()
        assert isinstance(result, dict)

    def test_response_has_message_key(self):
        """Response must contain a 'message' key."""
        result = hello_world()
        assert "message" in result

    def test_response_has_time_key(self):
        """Response must contain a 'time' key."""
        result = hello_world()
        assert "time" in result

    def test_message_value(self):
        """'message' value should match the expected server name."""
        result = hello_world()
        assert result["message"] == "Prabhmeets Server"

    def test_time_format(self):
        """'time' value should match HH:MM AM/PM format."""
        result = hello_world()
        pattern = r"^(0[1-9]|1[0-2]):[0-5]\d (AM|PM)$"
        assert re.match(pattern, result["time"]), (
            f"Time '{result['time']}' does not match expected HH:MM AM/PM format"
        )


# ── API / Integration Tests ───────────────────────────────────────────────────

class TestInfoRoute:
    def test_get_info_status_code(self):
        """GET /info should return HTTP 200."""
        response = client.get("/info")
        assert response.status_code == 200

    def test_get_info_returns_json(self):
        """GET /info should return a JSON body."""
        response = client.get("/info")
        assert response.headers["content-type"] == "application/json"

    def test_get_info_message(self):
        """GET /info JSON body should contain the correct message."""
        response = client.get("/info")
        data = response.json()
        assert data["message"] == "Prabhmeets Server"

    def test_get_info_time_format(self):
        """GET /info JSON body 'time' should be in HH:MM AM/PM format."""
        response = client.get("/info")
        data = response.json()
        pattern = r"^(0[1-9]|1[0-2]):[0-5]\d (AM|PM)$"
        assert re.match(pattern, data["time"]), (
            f"Time '{data['time']}' does not match expected HH:MM AM/PM format"
        )

    def test_get_info_response_keys(self):
        """GET /info response should only contain 'message' and 'time' keys."""
        response = client.get("/info")
        assert set(response.json().keys()) == {"message", "time","env"}

    def test_unknown_route_returns_404(self):
        """Any undefined route should return HTTP 404."""
        response = client.get("/unknown")
        assert response.status_code == 404
