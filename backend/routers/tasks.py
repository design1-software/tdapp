# 📘 WHAT THIS FILE DOES: Defines all HTTP route handlers for /tasks endpoints.
# Routes are thin: they validate input (via Pydantic models), call database functions,
# and return responses. Business logic stays in database.py.
# 🔗 FastAPI routing reference: https://fastapi.tiangolo.com/tutorial/bigger-applications/

from typing import Annotated, List, Optional
from fastapi import APIRouter, HTTPException, Query

import database
from models import Task, TaskCreate, TaskUpdate

# 📘 APIRouter groups related routes under a shared prefix.
# prefix="/tasks" means every route below is automatically at /tasks/...
router = APIRouter(prefix="/tasks", tags=["tasks"])


# ── CREATE ─────────────────────────────────────────────────────────────────────

@router.post("", response_model=Task, status_code=201)
def create_task(body: TaskCreate):
    """
    Create a new task.
    Requires a non-empty title. due_date is optional (ISO date string).
    Returns 422 if title is empty or whitespace-only.
    """
    return database.create_task(body.title, body.due_date)


# ── READ ALL ───────────────────────────────────────────────────────────────────

@router.get("", response_model=List[Task])
def get_tasks(
    # 📘 Query() adds metadata about this parameter for the /docs page.
    # pattern enforces that status must be 'complete' or 'incomplete' if provided.
    status: Annotated[
        Optional[str],
        Query(description="Filter by status: 'complete' or 'incomplete'"),
    ] = None,
):
    """
    Return all tasks. Accepts an optional ?status= filter.
    ?status=complete   → completed tasks only
    ?status=incomplete → incomplete tasks only
    Omit status        → all tasks
    Returns 422 for any other status value.
    """
    if status is not None and status not in ("complete", "incomplete"):
        raise HTTPException(
            status_code=422,
            detail="status must be 'complete' or 'incomplete'",
        )
    return database.get_tasks(status)


# ── READ ONE ───────────────────────────────────────────────────────────────────

@router.get("/{task_id}", response_model=Task)
def get_task(task_id: int):
    """Return a single task by ID. Returns 404 if not found."""
    task = database.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


# ── UPDATE ─────────────────────────────────────────────────────────────────────

@router.patch("/{task_id}", response_model=Task)
def update_task(task_id: int, body: TaskUpdate):
    """
    Partially update a task (title, completed, or due_date).
    Only fields included in the request body are changed — omitted fields stay the same.
    Returns 404 if the task doesn't exist.
    Returns 422 if title is present but empty.
    """
    if database.get_task(task_id) is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # 📘 model_dump(exclude_unset=True) gives us only the fields the client sent.
    # This is what makes PATCH work correctly — we don't overwrite unmentioned fields.
    updates = body.model_dump(exclude_unset=True)
    return database.update_task(task_id, updates)


# ── DELETE COMPLETED (must be defined BEFORE /{task_id} to take routing priority) ──

@router.delete("/completed")
def delete_completed():
    """Delete all completed tasks in one operation."""
    database.delete_completed()
    return {"message": "All completed tasks deleted"}


# ── DELETE ONE ─────────────────────────────────────────────────────────────────

@router.delete("/{task_id}")
def delete_task(task_id: int):
    """Delete a single task by ID. Returns 404 if not found."""
    task = database.delete_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"message": f"Task {task_id} deleted"}
