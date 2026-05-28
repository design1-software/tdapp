# 📘 WHAT THIS FILE DOES: Defines the data shapes (models) for tasks.
# Pydantic models validate incoming request data and shape outgoing responses.
# FastAPI uses these models to auto-generate the /docs API explorer.
# 🔗 FastAPI models reference: https://fastapi.tiangolo.com/tutorial/body/

from pydantic import BaseModel, field_validator
from typing import Optional


# 📘 TaskCreate is the shape of data required to CREATE a new task.
# 'title' is required. 'due_date' is optional (None by default).
class TaskCreate(BaseModel):
    title: str
    due_date: Optional[str] = None  # ISO date string, e.g. "2026-06-01"

    # 📘 @field_validator runs before the data is accepted.
    # It strips whitespace and rejects blank titles with a 422 error.
    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()  # Remove leading/trailing spaces
        if not v:
            raise ValueError("title cannot be empty or whitespace only")
        return v  # Return the cleaned value


# 📘 TaskUpdate is the shape for PATCH requests — all fields are optional.
# Only the fields included in the request body are changed.
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None
    due_date: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("title cannot be empty or whitespace only")
        return v


# 📘 Task is the full shape of a task as stored in the database.
# This model is used for all API responses — it includes id and created_at.
class Task(BaseModel):
    id: int
    title: str
    completed: bool  # Pydantic converts SQLite's 0/1 integers to True/False automatically
    due_date: Optional[str] = None
    created_at: str  # ISO datetime string, e.g. "2026-05-27T14:00:00+00:00"
    completed_at: Optional[str] = None  # Set when task is marked complete; cleared on un-complete


# ── Day Brief models (Phase 2) ────────────────────────────────────────────────

# 📘 BriefSection is the shape Claude must return — treated as a strict contract.
# Every field is required. If Claude omits one, Pydantic raises a ValidationError
# and the endpoint returns 502 instead of passing bad data to the client.
class BriefSection(BaseModel):
    situation: str               # 1-2 sentences: overall task load and completion status
    tasks_for_today: list[str]   # Active task titles in recommended priority order
    completed_recently: list[str]  # Titles of tasks completed in the last 24 hours
    priority_order: list[str]    # All active tasks sorted by recommended execution sequence


# 📘 BriefResponse wraps BriefSection with metadata added by the server.
class BriefResponse(BaseModel):
    generated_at: str   # ISO timestamp of when the brief was generated
    task_count: int     # Total tasks at time of generation
    brief: BriefSection
