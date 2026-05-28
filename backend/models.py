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
