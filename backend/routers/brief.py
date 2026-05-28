# 📘 WHAT THIS FILE DOES: Handles the POST /brief endpoint — the AI Day Brief feature.
# Fetches the current task list, calls Claude Sonnet via the Anthropic SDK with a strict
# JSON schema prompt, validates the response field-by-field via Pydantic, and returns
# a structured brief. If Claude returns anything unexpected, the endpoint fails with 502.
# 🔗 Anthropic SDK reference: https://docs.anthropic.com/en/api/getting-started

import json
import os
from datetime import datetime, timedelta, timezone

from anthropic import Anthropic, APIError
from fastapi import APIRouter, HTTPException

import database
from models import BriefResponse, BriefSection

router = APIRouter(prefix="/brief", tags=["brief"])

# 📘 The system prompt is a strict API contract, not a suggestion.
# It defines the exact JSON schema Claude must return and rules for every field.
# Explicit schemas produce consistent, validatable output from language models.
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


def _call_claude(user_message: str) -> str:
    """
    Make the Anthropic API call and return the raw response string.
    Separated into its own function so tests can patch it cleanly.

    Raises HTTPException(503) if ANTHROPIC_API_KEY is not set.
    Raises HTTPException(502) if the API call itself fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY is not configured on this server",
        )

    try:
        client = Anthropic(api_key=api_key)
        # 📘 client.messages.create() sends a message to Claude and returns a response.
        # 'system' sets the persistent instructions. 'messages' is the conversation.
        # max_tokens caps the response length — 512 is plenty for a structured brief.
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return message.content[0].text  # Extract the text from the response block
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"Claude API error: {exc}") from exc


# ── ENDPOINT ───────────────────────────────────────────────────────────────────

@router.post("", response_model=BriefResponse)
def generate_brief():
    """
    Generate an AI-powered daily task brief using Claude Sonnet.

    Pulls the current task list, sends it to Claude with a strict JSON schema prompt,
    validates the response via Pydantic, and returns a structured BriefResponse.

    Returns 503 if ANTHROPIC_API_KEY is not set.
    Returns 502 if Claude fails or returns malformed/missing fields.
    """
    tasks = database.get_tasks()

    # 📘 Split tasks into active and recently-completed.
    # 'recently' = completed within the last 24 hours, tracked by the completed_at timestamp
    # added to the database in this feature branch.
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    active = [t for t in tasks if not t["completed"]]
    completed_recently = [
        t for t in tasks
        if t["completed"]
        and t.get("completed_at")
        and datetime.fromisoformat(t["completed_at"]) > cutoff
    ]

    # 📘 Structured input → structured output. Give Claude labeled data, not a vague description.
    active_lines    = "\n".join(f"- {t['title']}" for t in active)    or "None"
    completed_lines = "\n".join(f"- {t['title']}" for t in completed_recently) or "None"

    user_message = (
        f"Active tasks ({len(active)}):\n{active_lines}\n\n"
        f"Completed in the last 24 hours ({len(completed_recently)}):\n{completed_lines}"
    )

    raw = _call_claude(user_message)

    # 📘 Validate Claude's response against BriefSection before returning anything.
    # If a field is missing or the wrong type, Pydantic raises ValidationError → 502.
    # We never forward unvalidated AI output directly to the client.
    try:
        data  = json.loads(raw)
        brief = BriefSection(**data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Claude returned an unexpected response format: {exc}",
        ) from exc

    return BriefResponse(
        generated_at=now.isoformat(),
        task_count=len(tasks),
        brief=brief,
    )
