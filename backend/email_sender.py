# 📘 WHAT THIS FILE DOES: Formats and sends the Day Brief as an HTML email via Resend.
# Resend is an HTTP-based email API — no SMTP needed, works on all hosting platforms.
# We use httpx (already in requirements.txt) to make the API call over HTTPS.
# 🔗 Resend API reference: https://resend.com/docs/api-reference/emails/send-email
# 🔗 httpx reference: https://www.python-httpx.org/

import os
import httpx
from datetime import datetime

from models import BriefResponse

# 📘 Resend's shared sender address — works on the free tier without a verified domain.
# If you own a domain and verify it with Resend, you can set EMAIL_FROM to any address
# on that domain (e.g. "briefs@yourdomain.com") via the Railway env var.
RESEND_DEFAULT_FROM = "onboarding@resend.dev"
RESEND_API_URL = "https://api.resend.com/emails"


def format_brief_email(brief_response: BriefResponse) -> tuple[str, str]:
    """
    Build the email subject line and HTML body from a BriefResponse.

    Parameters:
        brief_response — the validated BriefResponse from brief_service.build_brief()

    Returns:
        (subject, html_body) as a tuple of strings
    """
    b = brief_response.brief

    # 📘 fromisoformat() parses the ISO datetime string stored in generated_at.
    # strftime() converts it to a human-readable format for the email subject.
    generated_at = datetime.fromisoformat(brief_response.generated_at)
    date_str = generated_at.strftime("%A, %B %-d, %Y")  # e.g. "Thursday, May 29, 2026"

    subject = f"TDApp Day Brief — {date_str}"

    # 📘 A helper that converts a Python list into HTML <li> elements.
    # Returns an italicized "None" placeholder when the list is empty.
    def bullet_list(items: list) -> str:
        if not items:
            return "<li><em>None</em></li>"
        return "\n".join(f"<li>{item}</li>" for item in items)

    html_body = f"""<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1a1a2e;">

  <h2 style="margin-bottom: 4px;">&#10022; TDApp Day Brief</h2>
  <p style="color: #888; margin-top: 0;">{date_str} &middot; {brief_response.task_count} task{"s" if brief_response.task_count != 1 else ""}</p>

  <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 16px 0;">

  <h3 style="color: #444;">Situation</h3>
  <p>{b.situation}</p>

  <h3 style="color: #444;">Priority Order</h3>
  <ol>{bullet_list(b.priority_order)}</ol>

  <h3 style="color: #444;">Active Tasks</h3>
  <ul>{bullet_list(b.tasks_for_today)}</ul>

  <h3 style="color: #444;">Completed (Last 24h)</h3>
  <ul>{bullet_list(b.completed_recently)}</ul>

  <hr style="border: none; border-top: 1px solid #e0e0e0; margin-top: 30px;">
  <p style="color: #aaa; font-size: 12px;">Sent by TDApp &middot; Amplify Federal</p>

</body>
</html>"""

    return subject, html_body


def send_brief_email(brief_response: BriefResponse) -> None:
    """
    Send the formatted Day Brief via the Resend email API.

    Reads two required environment variables:
        RESEND_API_KEY — API key from resend.com
        EMAIL_TO       — one or more recipient addresses, comma-separated
                         e.g. "alice@gmail.com" or "alice@gmail.com, bob@gmail.com"

    EMAIL_FROM is optional — defaults to Resend's shared sender (onboarding@resend.dev).
    Set it to a custom address only if you have a verified domain on Resend.

    Raises EnvironmentError if RESEND_API_KEY or EMAIL_TO is missing.
    Raises httpx.HTTPStatusError if the Resend API rejects the request.
    """
    api_key = os.environ.get("RESEND_API_KEY")
    to_raw  = os.environ.get("EMAIL_TO")
    sender  = os.environ.get("EMAIL_FROM", RESEND_DEFAULT_FROM)

    # 📘 Check required vars before making any network call — fail fast with a clear message.
    missing = [k for k, v in {"RESEND_API_KEY": api_key, "EMAIL_TO": to_raw}.items() if not v]
    if missing:
        raise EnvironmentError(
            f"Missing required email environment variable(s): {', '.join(missing)}"
        )

    # 📘 Split EMAIL_TO on commas so a single variable supports multiple recipients.
    # "alice@gmail.com, bob@gmail.com" → ["alice@gmail.com", "bob@gmail.com"]
    recipients = [addr.strip() for addr in to_raw.split(",") if addr.strip()]

    subject, html_body = format_brief_email(brief_response)

    # 📘 Resend accepts a simple JSON payload over HTTPS — no SMTP socket needed.
    # The Authorization header carries the API key as a Bearer token.
    payload = {
        "from":    sender,
        "to":      recipients,
        "subject": subject,
        "html":    html_body,
    }

    # 📘 httpx.post() sends an HTTP POST request and returns a response object.
    # raise_for_status() turns any 4xx/5xx response into a Python exception,
    # so callers don't have to check the status code manually.
    response = httpx.post(
        RESEND_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )

    # 📘 Include Resend's response body in the exception so callers can see the exact error.
    if response.is_error:
        raise httpx.HTTPStatusError(
            f"Resend {response.status_code}: {response.text}",
            request=response.request,
            response=response,
        )
