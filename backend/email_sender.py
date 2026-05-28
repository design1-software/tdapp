# 📘 WHAT THIS FILE DOES: Formats and sends the Day Brief as an HTML email via Gmail SMTP.
# Uses Python's built-in smtplib — no extra dependencies needed.
# Gmail requires an App Password (not your regular password) when 2FA is on.
# How to get one: Google Account → Security → 2-Step Verification → App Passwords
# 🔗 smtplib reference: https://www.w3schools.com/python/module_smtplib.asp

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from models import BriefResponse


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
    date_str = generated_at.strftime("%A, %B %-d, %Y")  # e.g. "Wednesday, May 28, 2026"

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
    Send the formatted Day Brief via Gmail SMTP.

    Reads three environment variables:
        EMAIL_FROM         — the Gmail address sending the email
        EMAIL_APP_PASSWORD — Gmail App Password (not your account password)
        EMAIL_TO           — one or more recipient addresses, comma-separated
                             e.g. "alice@gmail.com" or "alice@gmail.com, bob@gmail.com"

    Raises EnvironmentError if any variable is missing.
    Raises smtplib.SMTPException if the connection or login fails.
    """
    sender   = os.environ.get("EMAIL_FROM")
    password = os.environ.get("EMAIL_APP_PASSWORD")
    to_raw   = os.environ.get("EMAIL_TO")

    # 📘 Check for all three before trying to connect — fail fast with a clear message.
    missing = [k for k, v in {
        "EMAIL_FROM": sender,
        "EMAIL_APP_PASSWORD": password,
        "EMAIL_TO": to_raw,
    }.items() if not v]

    if missing:
        raise EnvironmentError(
            f"Missing required email environment variable(s): {', '.join(missing)}"
        )

    # 📘 Split EMAIL_TO on commas so a single variable supports multiple recipients.
    # "alice@gmail.com, bob@gmail.com" → ["alice@gmail.com", "bob@gmail.com"]
    # strip() removes any accidental whitespace around each address.
    recipients = [addr.strip() for addr in to_raw.split(",") if addr.strip()]

    subject, html_body = format_brief_email(brief_response)

    # 📘 MIMEMultipart("alternative") creates a message with two versions:
    # a plain-text fallback and an HTML version. Email clients that support HTML
    # show the styled version; others fall back to plain text automatically.
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = ", ".join(recipients)  # Shows all recipients in the To: header

    # Plain-text fallback for clients that don't render HTML
    b = brief_response.brief
    plain_lines = [
        subject,
        "",
        "SITUATION",
        b.situation,
        "",
        "PRIORITY ORDER",
    ]
    plain_lines += [f"{i + 1}. {t}" for i, t in enumerate(b.priority_order)] or ["None"]
    plain_lines += ["", "ACTIVE TASKS"]
    plain_lines += [f"- {t}" for t in b.tasks_for_today] or ["None"]
    plain_lines += ["", "COMPLETED (LAST 24H)"]
    plain_lines += [f"- {t}" for t in b.completed_recently] or ["None"]
    plain_text = "\n".join(plain_lines)

    # 📘 Attach plain text first, then HTML. RFC 2822 says the last part takes precedence,
    # so HTML-capable clients will render the HTML version.
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    # 📘 SMTP_SSL connects on port 465 with TLS from the start.
    # Gmail requires TLS — regular port 25 or STARTTLS (587) also work but 465 is simplest.
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        # 📘 sendmail() accepts a list of recipients — delivers one copy to each address.
        server.sendmail(sender, recipients, msg.as_string())
