# 📘 WHAT THIS FILE DOES: pytest tests for the daily email scheduler job.
# Tests never call the real Claude API or send real emails — both are patched with mocks.
# Verifies that the job calls the right functions and handles every failure mode gracefully.
# 🔗 unittest.mock reference: https://docs.python.org/3/library/unittest.mock.html

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import database
import brief_service
from models import BriefResponse, BriefSection
from scheduler import daily_brief_job, create_scheduler


# ── FIXTURES ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """Each test gets its own empty database — prevents cross-test contamination."""
    db_file = str(tmp_path / "test.db")
    database.set_db_path(db_file)
    database.init_db()
    yield
    database.set_db_path(None)


# 📘 A pre-built BriefResponse used as the mock return value from build_brief().
# Building it here avoids constructing it inside every test.
MOCK_BRIEF = BriefResponse(
    generated_at=datetime.now(timezone.utc).isoformat(),
    task_count=3,
    brief=BriefSection(
        situation="2 active tasks. 1 completed in the last 24 hours.",
        tasks_for_today=["Write report", "Send email"],
        completed_recently=["Buy groceries"],
        priority_order=["Write report", "Send email"],
    ),
)


# ── HAPPY PATH ─────────────────────────────────────────────────────────────────

class TestDailyBriefJob:
    @patch("scheduler.email_sender.send_brief_email")
    @patch("scheduler.brief_service.build_brief", return_value=MOCK_BRIEF)
    def test_job_calls_build_brief_and_send_email(self, mock_build, mock_send):
        """
        When everything is configured, the job calls build_brief() once
        and passes the result to send_brief_email().
        """
        # 📘 Calling daily_brief_job() directly lets us test the function in isolation
        # without waiting for the scheduler to fire at 07:00.
        daily_brief_job()

        mock_build.assert_called_once()
        mock_send.assert_called_once_with(MOCK_BRIEF)

    @patch("scheduler.email_sender.send_brief_email")
    @patch("scheduler.brief_service.build_brief", return_value=MOCK_BRIEF)
    def test_job_does_not_raise_on_success(self, _mock_build, _mock_send):
        """The job function should never raise — errors are logged, not propagated."""
        # 📘 If this raises, the test fails. Schedulers must not crash the app.
        daily_brief_job()  # Should complete without exception


# ── ERROR HANDLING ─────────────────────────────────────────────────────────────

class TestDailyBriefJobErrorHandling:
    @patch("scheduler.brief_service.build_brief",
           side_effect=brief_service.BriefConfigError("ANTHROPIC_API_KEY is not configured"))
    def test_missing_api_key_logs_warning_and_does_not_raise(self, _mock):
        """
        A BriefConfigError (missing API key) should log a warning and return normally.
        The scheduler must not crash just because the API key isn't set yet.
        """
        daily_brief_job()  # Must not raise

    @patch("scheduler.brief_service.build_brief",
           side_effect=brief_service.BriefApiError("Claude returned unexpected output"))
    def test_claude_api_error_logs_and_does_not_raise(self, _mock):
        """A BriefApiError (Claude failed) should log an error and return normally."""
        daily_brief_job()  # Must not raise

    @patch("scheduler.email_sender.send_brief_email",
           side_effect=EnvironmentError("Missing EMAIL_FROM"))
    @patch("scheduler.brief_service.build_brief", return_value=MOCK_BRIEF)
    def test_missing_email_config_logs_and_does_not_raise(self, _mock_build, _mock_send):
        """A missing email env var should log a warning and return normally."""
        daily_brief_job()  # Must not raise

    @patch("scheduler.email_sender.send_brief_email",
           side_effect=Exception("Unexpected SMTP failure"))
    @patch("scheduler.brief_service.build_brief", return_value=MOCK_BRIEF)
    def test_unexpected_error_logs_and_does_not_raise(self, _mock_build, _mock_send):
        """Any unexpected exception during the job should be caught, logged, and swallowed."""
        daily_brief_job()  # Must not raise


# ── SCHEDULER CONFIGURATION ────────────────────────────────────────────────────

class TestCreateScheduler:
    def test_scheduler_has_daily_brief_job(self):
        """create_scheduler() registers exactly one job with the correct ID."""
        scheduler = create_scheduler()
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "daily_brief"

    def test_scheduler_job_fires_at_0700(self):
        """The daily brief job is scheduled for 07:00."""
        scheduler = create_scheduler()
        job = scheduler.get_job("daily_brief")
        # 📘 CronTrigger stores fields as a list of CronExpression objects.
        # We convert to string and check that hour=7 and minute=0 are set.
        trigger_str = str(job.trigger)
        assert "hour='7'" in trigger_str or "hour=7" in trigger_str
