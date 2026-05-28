# 📘 WHAT THIS FILE DOES: pytest tests for the POST /brief endpoint.
# Tests never call the real Anthropic API — _call_claude is patched with a mock.
# This keeps tests fast, free, and deterministic regardless of network or API key.
# 🔗 unittest.mock reference: https://docs.python.org/3/library/unittest.mock.html

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

import database
from main import app

# 📘 A valid JSON string that matches the BriefSection schema exactly.
# Used as the mock return value whenever _call_claude is patched.
VALID_BRIEF_JSON = json.dumps({
    "situation": "2 active tasks remaining. 1 task completed in the last 24 hours.",
    "tasks_for_today": ["Write report", "Send email"],
    "completed_recently": ["Buy groceries"],
    "priority_order": ["Write report", "Send email"],
})


# ── FIXTURES ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """Each test gets its own empty database — same pattern as test_tasks.py."""
    db_file = str(tmp_path / "test.db")
    database.set_db_path(db_file)
    database.init_db()
    yield
    database.set_db_path(None)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def seeded_client(client):
    """A client with a pre-populated task list for brief generation tests."""
    client.post("/tasks", json={"title": "Write report"})
    client.post("/tasks", json={"title": "Send email"})
    t = client.post("/tasks", json={"title": "Buy groceries"}).json()
    client.patch(f"/tasks/{t['id']}", json={"completed": True})
    return client


# ── HAPPY PATH ─────────────────────────────────────────────────────────────────

class TestGenerateBrief:
    # 📘 @patch replaces _call_claude with a MagicMock for the duration of the test.
    # We control exactly what "Claude" returns, so tests are fast and free.
    @patch("routers.brief._call_claude", return_value=VALID_BRIEF_JSON)
    def test_returns_200_with_correct_structure(self, _mock, seeded_client):
        """A valid Claude response returns 200 with a fully structured BriefResponse."""
        response = seeded_client.post("/brief")
        assert response.status_code == 200
        data = response.json()
        assert "generated_at" in data
        assert "task_count" in data
        assert "brief" in data

    @patch("routers.brief._call_claude", return_value=VALID_BRIEF_JSON)
    def test_brief_contains_all_required_fields(self, _mock, seeded_client):
        """All four BriefSection fields are present in the response."""
        data = seeded_client.post("/brief").json()["brief"]
        assert "situation" in data
        assert "tasks_for_today" in data
        assert "completed_recently" in data
        assert "priority_order" in data

    @patch("routers.brief._call_claude", return_value=VALID_BRIEF_JSON)
    def test_task_count_matches_database(self, _mock, seeded_client):
        """task_count reflects the total number of tasks at time of generation."""
        data = seeded_client.post("/brief").json()
        assert data["task_count"] == 3  # 2 active + 1 completed

    @patch("routers.brief._call_claude", return_value=VALID_BRIEF_JSON)
    def test_empty_task_list_still_generates_brief(self, _mock, client):
        """Brief generation works even when there are no tasks."""
        response = client.post("/brief")
        assert response.status_code == 200
        assert response.json()["task_count"] == 0


# ── ERROR HANDLING ─────────────────────────────────────────────────────────────

class TestBriefErrorHandling:
    def test_missing_api_key_returns_503(self, client, monkeypatch):
        """503 is returned when ANTHROPIC_API_KEY is not set."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        response = client.post("/brief")
        assert response.status_code == 503
        assert "ANTHROPIC_API_KEY" in response.json()["detail"]

    @patch("routers.brief._call_claude", return_value="this is not json {{{")
    def test_malformed_json_from_claude_returns_502(self, _mock, seeded_client):
        """502 is returned if Claude sends back invalid JSON."""
        response = seeded_client.post("/brief")
        assert response.status_code == 502

    @patch("routers.brief._call_claude", return_value=json.dumps({
        "situation": "ok",
        # 📘 tasks_for_today, completed_recently, and priority_order are all missing
    }))
    def test_missing_fields_from_claude_returns_502(self, _mock, seeded_client):
        """502 is returned if Claude's JSON is missing required BriefSection fields."""
        response = seeded_client.post("/brief")
        assert response.status_code == 502

    @patch("routers.brief._call_claude", return_value=json.dumps({
        "situation": "ok",
        "tasks_for_today": [],
        "completed_recently": [],
        "priority_order": [],
        "unexpected_extra_field": "should be ignored by Pydantic",
    }))
    def test_extra_fields_from_claude_are_ignored(self, _mock, seeded_client):
        """Pydantic silently ignores extra fields — does not cause a 502."""
        response = seeded_client.post("/brief")
        assert response.status_code == 200
        assert "unexpected_extra_field" not in response.json()["brief"]
