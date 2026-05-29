# 📘 WHAT THIS FILE DOES: Configures the APScheduler background job for daily email delivery.
# The scheduler runs inside the same uvicorn process as the FastAPI app.
# At 07:00 Eastern every day, it generates a Day Brief and emails it.
# If the job fails for any reason, the error is logged — the scheduler keeps running.
# 🔗 APScheduler docs: https://apscheduler.readthedocs.io/en/3.x/

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import brief_service
import email_sender

# 📘 logging.getLogger(__name__) creates a logger named after this module.
# Log output appears in Railway's deployment logs so you can see when jobs run.
logger = logging.getLogger(__name__)


# ── JOB FUNCTION ───────────────────────────────────────────────────────────────

def daily_brief_job() -> None:
    """
    Generate a Day Brief and send it by email.
    Called automatically by APScheduler at 07:00 Eastern every day.

    All errors are caught and logged — a failed job run should never crash
    the scheduler or the API server. The scheduler will try again the next day.
    """
    logger.info("Daily brief job starting")

    try:
        # 📘 build_brief() calls Claude and validates the response.
        # send_brief_email() formats and delivers it via Gmail SMTP.
        brief_response = brief_service.build_brief()
        email_sender.send_brief_email(brief_response)
        logger.info("Daily brief sent successfully")

    except brief_service.BriefConfigError as exc:
        # 📘 Configuration issue (missing API key) — log a warning, not an error.
        # This is expected if the key wasn't set; no need to page anyone.
        logger.warning("Daily brief skipped — configuration issue: %s", exc)

    except EnvironmentError as exc:
        # Missing email environment variables
        logger.warning("Daily brief skipped — email not configured: %s", exc)

    except Exception as exc:
        # 📘 Catch-all for unexpected errors (network timeout, bad response, etc.).
        # exc_info=True includes the full stack trace in the log — useful for debugging.
        logger.error("Daily brief job failed: %s", exc, exc_info=True)


# ── SCHEDULER FACTORY ──────────────────────────────────────────────────────────

def create_scheduler() -> BackgroundScheduler:
    """
    Build and configure the APScheduler instance with the daily brief job.

    Returns a BackgroundScheduler that is NOT yet started.
    The caller (main.py lifespan) is responsible for calling .start() and .shutdown().

    Why BackgroundScheduler?
    It runs in a daemon thread inside the existing uvicorn process — no separate process
    or worker needed. Simple and appropriate for a single scheduled job at this scale.
    """
    # 📘 timezone sets the default timezone for all jobs in this scheduler.
    # America/New_York handles Eastern Standard Time and Daylight Saving automatically.
    scheduler = BackgroundScheduler(timezone="America/New_York")

    # 📘 CronTrigger fires at a specific clock time, just like a Unix cron job.
    # hour=7, minute=0 = 07:00 AM. The timezone argument here is redundant with the
    # scheduler default but makes the intent explicit.
    scheduler.add_job(
        daily_brief_job,
        trigger=CronTrigger(hour=7, minute=0, timezone="America/New_York"),
        id="daily_brief",
        name="Daily Day Brief email",
        replace_existing=True,  # Safe to call create_scheduler() multiple times
    )

    return scheduler
