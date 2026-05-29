# 📘 WHAT THIS FILE DOES: HTTP route handlers for /brief endpoints.
# POST /brief       — generate and return an AI Day Brief as JSON
# POST /brief/email — generate a brief and send it via email immediately (useful for testing)
# This is a thin layer. All brief generation logic lives in brief_service.py so it can
# be reused by the daily email scheduler without pulling in FastAPI's HTTPException.
# This file's only job: convert brief_service exceptions into the correct HTTP status codes.
# 🔗 FastAPI routing: https://fastapi.tiangolo.com/tutorial/bigger-applications/

from fastapi import APIRouter, HTTPException

import brief_service
import email_sender
from models import BriefResponse

router = APIRouter(prefix="/brief", tags=["brief"])


@router.post("", response_model=BriefResponse)
def generate_brief():
    """
    Generate an AI-powered daily task brief using Claude Sonnet.

    Delegates all logic to brief_service.build_brief() and maps the result:
      BriefConfigError → 503 (API key not configured on this server)
      BriefApiError    → 502 (Claude failed or returned malformed output)
    """
    # 📘 try/except here is the translation layer between service errors and HTTP errors.
    # The service raises plain Python exceptions; we convert them to HTTP responses here.
    try:
        return brief_service.build_brief()
    except brief_service.BriefConfigError as exc:
        # 📘 503 Service Unavailable — the server is missing a required configuration.
        raise HTTPException(status_code=503, detail=str(exc))
    except brief_service.BriefApiError as exc:
        # 📘 502 Bad Gateway — upstream service (Claude) returned an unexpected result.
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/email")
def send_brief_email():
    """
    Generate a Day Brief and send it immediately via email.

    Useful for testing the email feature on demand without waiting for the 07:00 scheduler.
    Uses the EMAIL_FROM, EMAIL_APP_PASSWORD, and EMAIL_TO environment variables configured
    on the server — the same variables the daily scheduler uses.

    Returns 200 with the list of recipients if the email was sent successfully.
    Returns 503 if the API key or email environment variables are missing.
    Returns 502 if Claude fails or returns malformed output.
    """
    # 📘 Step 1 — generate the brief (same path as POST /brief)
    try:
        brief_response = brief_service.build_brief()
    except brief_service.BriefConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except brief_service.BriefApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # 📘 Step 2 — send the email using the configured environment variables
    try:
        email_sender.send_brief_email(brief_response)
    except EnvironmentError as exc:
        # 📘 EnvironmentError means a required env var (EMAIL_FROM, EMAIL_APP_PASSWORD,
        # or EMAIL_TO) is not set on this server.
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Email send failed: {exc}")

    # 📘 Return the recipient list so the caller can confirm where the email was sent.
    import os
    to_raw = os.environ.get("EMAIL_TO", "")
    recipients = [addr.strip() for addr in to_raw.split(",") if addr.strip()]
    return {"status": "sent", "recipients": recipients}
