# 📘 WHAT THIS FILE DOES: pytest test suite for all /tasks API endpoints.
# Uses FastAPI's TestClient to make real HTTP requests against the app.
# Every test runs against an isolated temporary database — no shared state between tests.
# 🔗 pytest reference: https://docs.pytest.org/en/stable/

import sys
import os

# 📘 sys.path.insert lets Python find our modules (main.py, database.py, etc.)
# from the backend/ directory when running pytest from the backend/ folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient

import database
from main import app


# ── FIXTURES ───────────────────────────────────────────────────────────────────

# 📘 A pytest fixture is a reusable setup function. 'autouse=True' means it runs
# automatically before every single test — no need to mention it in each test function.
@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """
    Each test gets its own empty SQLite database file in a temporary directory.
    tmp_path is a built-in pytest fixture that provides a unique temp folder per test.
    After each test, the temp folder (and database) is automatically deleted.
    """
    db_file = str(tmp_path / "test.db")
    database.set_db_path(db_file)  # Point the app at the temp database
    database.init_db()             # Create the empty tasks table
    yield                          # Run the test
    database.set_db_path(None)     # Reset to the default database path


# 📘 The TestClient wraps the FastAPI app so tests can make HTTP calls without
# running a real server. Requests go directly through the app's routing layer.
@pytest.fixture
def client():
    return TestClient(app)


# ── CREATE TASK ────────────────────────────────────────────────────────────────

class TestCreateTask:
    def test_create_valid_task(self, client):
        """A valid title returns 201 with the created task."""
        response = client.post("/tasks", json={"title": "Buy groceries"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Buy groceries"
        assert data["completed"] is False
        assert "id" in data
        assert "created_at" in data

    def test_create_task_with_due_date(self, client):
        """due_date is stored and returned correctly."""
        response = client.post("/tasks", json={"title": "Submit report", "due_date": "2026-06-01"})
        assert response.status_code == 201
        assert response.json()["due_date"] == "2026-06-01"

    def test_create_task_without_due_date(self, client):
        """due_date defaults to None when not provided."""
        response = client.post("/tasks", json={"title": "Walk the dog"})
        assert response.status_code == 201
        assert response.json()["due_date"] is None

    def test_create_task_empty_title_rejected(self, client):
        """Empty string title returns 422 Unprocessable Entity."""
        response = client.post("/tasks", json={"title": ""})
        assert response.status_code == 422

    def test_create_task_whitespace_title_rejected(self, client):
        """Whitespace-only title returns 422 — treated as empty."""
        response = client.post("/tasks", json={"title": "   "})
        assert response.status_code == 422

    def test_create_task_title_is_stripped(self, client):
        """Leading/trailing whitespace is stripped before saving."""
        response = client.post("/tasks", json={"title": "  hello  "})
        assert response.status_code == 201
        assert response.json()["title"] == "hello"

    def test_create_task_missing_title_rejected(self, client):
        """Request body with no title field returns 422."""
        response = client.post("/tasks", json={})
        assert response.status_code == 422


# ── GET TASKS ──────────────────────────────────────────────────────────────────

class TestGetTasks:
    def test_get_all_tasks_empty_list(self, client):
        """No tasks in database returns an empty array."""
        response = client.get("/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_tasks(self, client):
        """All created tasks are returned."""
        client.post("/tasks", json={"title": "Task 1"})
        client.post("/tasks", json={"title": "Task 2"})
        response = client.get("/tasks")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_filter_complete(self, client):
        """?status=complete returns only completed tasks."""
        t1 = client.post("/tasks", json={"title": "Task 1"}).json()
        client.post("/tasks", json={"title": "Task 2"})
        client.patch(f"/tasks/{t1['id']}", json={"completed": True})

        response = client.get("/tasks?status=complete")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["completed"] is True

    def test_filter_incomplete(self, client):
        """?status=incomplete returns only incomplete tasks."""
        t1 = client.post("/tasks", json={"title": "Task 1"}).json()
        client.post("/tasks", json={"title": "Task 2"})
        client.patch(f"/tasks/{t1['id']}", json={"completed": True})

        response = client.get("/tasks?status=incomplete")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["completed"] is False

    def test_invalid_status_filter_rejected(self, client):
        """An unrecognized status value returns 422."""
        response = client.get("/tasks?status=invalid")
        assert response.status_code == 422


# ── GET SINGLE TASK ────────────────────────────────────────────────────────────

class TestGetTask:
    def test_get_existing_task(self, client):
        """Requesting a task by ID returns the correct task."""
        created = client.post("/tasks", json={"title": "My task"}).json()
        response = client.get(f"/tasks/{created['id']}")
        assert response.status_code == 200
        assert response.json()["title"] == "My task"

    def test_get_nonexistent_task_returns_404(self, client):
        """Requesting an ID that doesn't exist returns 404."""
        response = client.get("/tasks/9999")
        assert response.status_code == 404


# ── UPDATE TASK ────────────────────────────────────────────────────────────────

class TestUpdateTask:
    def test_toggle_task_complete(self, client):
        """Setting completed=true marks the task complete."""
        task = client.post("/tasks", json={"title": "Task"}).json()
        response = client.patch(f"/tasks/{task['id']}", json={"completed": True})
        assert response.status_code == 200
        assert response.json()["completed"] is True

    def test_toggle_task_back_to_incomplete(self, client):
        """Setting completed=false after it was true marks it incomplete again."""
        task = client.post("/tasks", json={"title": "Task"}).json()
        client.patch(f"/tasks/{task['id']}", json={"completed": True})
        response = client.patch(f"/tasks/{task['id']}", json={"completed": False})
        assert response.json()["completed"] is False

    def test_edit_task_title(self, client):
        """Patching title updates the stored title."""
        task = client.post("/tasks", json={"title": "Old title"}).json()
        response = client.patch(f"/tasks/{task['id']}", json={"title": "New title"})
        assert response.status_code == 200
        assert response.json()["title"] == "New title"

    def test_patch_only_updates_specified_fields(self, client):
        """Patching title does not change the completed state."""
        task = client.post("/tasks", json={"title": "Task"}).json()
        client.patch(f"/tasks/{task['id']}", json={"completed": True})
        response = client.patch(f"/tasks/{task['id']}", json={"title": "Renamed"})
        data = response.json()
        assert data["title"] == "Renamed"
        assert data["completed"] is True  # Should be unchanged

    def test_update_nonexistent_task_returns_404(self, client):
        """Patching an ID that doesn't exist returns 404."""
        response = client.patch("/tasks/9999", json={"completed": True})
        assert response.status_code == 404

    def test_update_empty_title_rejected(self, client):
        """Patching with an empty title returns 422."""
        task = client.post("/tasks", json={"title": "Task"}).json()
        response = client.patch(f"/tasks/{task['id']}", json={"title": ""})
        assert response.status_code == 422


# ── DELETE TASK ────────────────────────────────────────────────────────────────

class TestDeleteTask:
    def test_delete_existing_task(self, client):
        """Deleting a task removes it — subsequent GET returns 404."""
        task = client.post("/tasks", json={"title": "Task"}).json()
        response = client.delete(f"/tasks/{task['id']}")
        assert response.status_code == 200
        assert client.get(f"/tasks/{task['id']}").status_code == 404

    def test_delete_nonexistent_task_returns_404(self, client):
        """Deleting an ID that doesn't exist returns 404."""
        response = client.delete("/tasks/9999")
        assert response.status_code == 404


# ── DELETE COMPLETED ───────────────────────────────────────────────────────────

class TestDeleteCompleted:
    def test_delete_all_completed_tasks(self, client):
        """All completed tasks are removed; incomplete tasks remain."""
        t1 = client.post("/tasks", json={"title": "Task 1"}).json()
        t2 = client.post("/tasks", json={"title": "Task 2"}).json()
        client.post("/tasks", json={"title": "Task 3 — incomplete"})

        client.patch(f"/tasks/{t1['id']}", json={"completed": True})
        client.patch(f"/tasks/{t2['id']}", json={"completed": True})

        response = client.delete("/tasks/completed")
        assert response.status_code == 200

        remaining = client.get("/tasks").json()
        assert len(remaining) == 1
        assert remaining[0]["title"] == "Task 3 — incomplete"

    def test_delete_completed_when_none_exist(self, client):
        """Calling delete completed when no tasks are done is a no-op."""
        client.post("/tasks", json={"title": "Task 1"})
        response = client.delete("/tasks/completed")
        assert response.status_code == 200
        assert len(client.get("/tasks").json()) == 1
