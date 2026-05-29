# 📘 WHAT THIS FILE DOES: HTTP route handler for POST /brief — the AI Day Brief endpoint.
# This is a thin layer. All brief generation logic lives in brief_service.py so it can
# be reused by the daily email scheduler without pulling in FastAPI's HTTPException.
# This file's only job: convert brief_service exceptions into the correct HTTP status codes.
# 🔗 FastAPI routing: https://fastapi.tiangolo.com/tutorial/bigger-applications/

from fastapi import APIRouter, HTTPException

import brief_service
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
