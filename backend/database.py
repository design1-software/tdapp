# 📘 WHAT THIS FILE DOES: Manages the SQLite database connection and all CRUD operations.
# CRUD = Create, Read, Update, Delete — the four basic operations on any data store.
# All database logic lives here. The router (tasks.py) calls these functions and stays thin.
# 🔗 SQLite reference: https://www.w3schools.com/sql/

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, timezone


# 📘 _custom_db_path lets tests swap in a temporary database without touching production data.
# Using None means "use the default path" — tests call set_db_path() to override.
_custom_db_path: str | None = None


def set_db_path(path: str | None) -> None:
    """Allow tests to inject a temporary database path."""
    global _custom_db_path
    _custom_db_path = path


def _get_path() -> str:
    """Return the active database file path."""
    if _custom_db_path is not None:
        return _custom_db_path
    # Default: tasks.db lives in the same directory as this file
    return os.path.join(os.path.dirname(__file__), "tasks.db")


@contextmanager
def _db():
    """
    Context manager for database connections.
    Commits on success, rolls back on error, always closes the connection.
    Using 'with _db() as conn:' ensures the connection is never left open.
    """
    conn = sqlite3.connect(_get_path())
    conn.row_factory = sqlite3.Row  # Makes rows behave like dicts: row["title"]
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent read performance
    try:
        yield conn
        conn.commit()  # 📘 Save all changes when the block exits cleanly
    except Exception:
        conn.rollback()  # 📘 Undo all changes if something went wrong
        raise
    finally:
        conn.close()  # Always close — even if an exception was raised


def init_db() -> None:
    """Create the tasks table if it doesn't already exist."""
    with _db() as conn:
        # 📘 CREATE TABLE IF NOT EXISTS is safe to call every time the app starts.
        # It only creates the table the very first time — never overwrites existing data.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                completed   INTEGER NOT NULL DEFAULT 0,
                due_date    TEXT,
                created_at  TEXT    NOT NULL
            )
        """)


def create_task(title: str, due_date: str | None = None) -> dict:
    """Insert a new task and return it as a dict."""
    with _db() as conn:
        cursor = conn.execute(
            # 📘 INSERT adds a new row. The ? placeholders prevent SQL injection.
            "INSERT INTO tasks (title, completed, due_date, created_at) VALUES (?, 0, ?, ?)",
            (title, due_date, datetime.now(timezone.utc).isoformat()),
        )
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return dict(row)


def get_tasks(status: str | None = None) -> list[dict]:
    """
    Return all tasks, optionally filtered by completion status.
    status='complete'   → only completed tasks
    status='incomplete' → only incomplete tasks
    status=None         → all tasks
    """
    with _db() as conn:
        # 📘 WHERE filters which rows are returned. ORDER BY sorts them.
        if status == "complete":
            rows = conn.execute(
                "SELECT * FROM tasks WHERE completed = 1 ORDER BY created_at"
            ).fetchall()
        elif status == "incomplete":
            rows = conn.execute(
                "SELECT * FROM tasks WHERE completed = 0 ORDER BY created_at"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY created_at"
            ).fetchall()
    return [dict(r) for r in rows]


def get_task(task_id: int) -> dict | None:
    """Return a single task by ID, or None if it doesn't exist."""
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return dict(row) if row else None


def update_task(task_id: int, updates: dict) -> dict | None:
    """
    Apply a partial update to a task.
    'updates' is a dict of only the fields being changed (e.g. {"completed": True}).
    Builds the SET clause dynamically so only provided fields are touched.
    """
    if not updates:
        return get_task(task_id)

    # 📘 Build "title = ?, completed = ?" dynamically from the keys in updates
    fields = ", ".join(f"{col} = ?" for col in updates)
    values = [*updates.values(), task_id]  # Values for ? placeholders, task_id goes last

    with _db() as conn:
        conn.execute(f"UPDATE tasks SET {fields} WHERE id = ?", values)
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return dict(row) if row else None


def delete_task(task_id: int) -> dict | None:
    """Delete a task by ID. Returns the deleted task dict, or None if not found."""
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return dict(row) if row else None


def delete_completed() -> None:
    """Delete all tasks where completed = 1."""
    with _db() as conn:
        conn.execute("DELETE FROM tasks WHERE completed = 1")
