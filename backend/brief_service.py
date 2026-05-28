# 📘 WHAT THIS FILE DOES: Core brief generation logic — shared between the /brief HTTP endpoint
# and the daily email scheduler. Uses regular Python exceptions (not HTTPException) so this
# module works in both HTTP request context and background scheduler context.
# 🔗 Anthropic SDK reference: https://docs.anthropic.com/en/api/getting-started

import json
import os
from datetime import datetime, timedelta, timezone

from anthropic import Anthropic, APIError

import database
from models import BriefResponse, BriefSection


# ── CUSTOM EXCEPTIONS ──────────────────────────────────────────────────────────

# 📘 Custom exception types let callers handle each failure mode explicitly.
# The route handler maps these to HTTP status codes.
# The scheduler catches them and logs them without crashing.

class BriefConfigError(Exception):
    """Raised when ANTHROPIC_API_KEY is not configured."""

class BriefApiError(Exception):
    """Raised when the Claude API call fails or returns malformed output."""


# ── SYSTEM PROMPT ──────────────────────────────────────────────────────────────

# 📘 The system prompt is a strict API contract, not a suggestion.
# It defines the exact JSON schema Claude must return and rules for every field.
# Treating it as a contract — not a hint — is what makes the output validatable.
SYSTEM_PROMPT = """You are a task management assistant that generates structured daily briefings.

Return ONLY a JSON object matching this exact schema. Do not include any text outside the JSON.

Schema:
{
  "situation": "string — 1-2 sentences describing overall task load and completion status",
  "tasks_for_today": ["array of strings — active task titles"],
  "completed_recently": ["array of strings — titles of tasks completed in the last 24 hours"],
  "priority_order": ["array of strings — active tasks sorted by recommended execution sequence"]
}

Rules:
- situation must always be a non-empty string
- If a list section has no items, return an empty array [] — never omit the field
- Do not add extra fields
- Return ONLY the JSON object — no markdown fences, no explanation, no prose"""


# ── CLAUDE CALL ────────────────────────────────────────────────────────────────

def call_claude(user_message: str) -> str:
    """
    Send a message to Claude Sonnet and return the raw text response.

    Raises BriefConfigError if ANTHROPIC_API_KEY is not set.
    Raises BriefApiError if the Anthropic API call fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise BriefConfigError("ANTHROPIC_API_KEY is not configured on this server")

    try:
        client = Anthropic(api_key=api_key)
        # 📘 max_tokens=512 is plenty for a structured brief — caps cost and latency.
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return message.content[0].text
    except APIError as exc:
        raise BriefApiError(f"Claude API error: {exc}") from exc


# ── BRIEF BUILDER ──────────────────────────────────────────────────────────────

def build_brief() -> BriefResponse:
    """
    Generate a BriefResponse from the current task database.

    Splits tasks into active (not completed) and recently completed (within 24h),
    sends both lists to Claude with the system prompt, validates every field in
    Claude's response via Pydantic, and returns a structured BriefResponse.

    Raises BriefConfigError if ANTHROPIC_API_KEY is missing.
    Raises BriefApiError if Claude fails or returns malformed/incomplete output.
    """
    tasks = database.get_tasks()

    # 📘 'now' and 'cutoff' are computed once and reused for both filtering and
    # the generated_at timestamp so the response is internally consistent.
    now    = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    # 📘 Split tasks into two groups: what's still active vs. what was done recently.
    # 'completed_at' is a timestamp set by database.update_task() when completed=True.
    active = [t for t in tasks if not t["completed"]]
    completed_recently = [
        t for t in tasks
        if t["completed"]
        and t.get("completed_at")
        and datetime.fromisoformat(t["completed_at"]) > cutoff
    ]

    # 📘 Structured labeled input → structured output. Give Claude clear sections,
    # not a blob of text. The counts help Claude write an accurate situation sentence.
    active_lines    = "\n".join(f"- {t['title']}" for t in active)            or "None"
    completed_lines = "\n".join(f"- {t['title']}" for t in completed_recently) or "None"

    user_message = (
        f"Active tasks ({len(active)}):\n{active_lines}\n\n"
        f"Completed in the last 24 hours ({len(completed_recently)}):\n{completed_lines}"
    )

    raw = call_claude(user_message)

    # 📘 Validate Claude's response before returning anything.
    # If a field is missing or the wrong type, we raise BriefApiError — we never
    # forward unvalidated AI output directly to the caller.
    try:
        data  = json.loads(raw)
        brief = BriefSection(**data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise BriefApiError(f"Claude returned an unexpected response format: {exc}") from exc

    return BriefResponse(
        generated_at=now.isoformat(),
        task_count=len(tasks),
        brief=brief,
    )
