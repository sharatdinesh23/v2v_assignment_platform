"""Shared constants and lightweight typed helpers.

These are plain dicts coming back from Appwrite; we keep string constants for
statuses and roles here so the rest of the code never hard-codes magic strings.
"""
from __future__ import annotations


class Role:
    ADMIN = "admin"
    STUDENT = "student"


class SubmissionStatus:
    # Student has not submitted anything yet (no document exists).
    UNSOLVED = "unsolved"
    # Student submitted; waiting for the AI grader to run.
    SUBMITTED = "submitted"
    # AI produced a provisional grade; admin must confirm.
    AI_GRADED = "ai_graded"
    # Admin accepted / overrode the grade -> final.
    FINAL = "final"


# Human-readable labels for the UI.
STATUS_LABELS = {
    SubmissionStatus.UNSOLVED: "Unsolved",
    SubmissionStatus.SUBMITTED: "Submitted (awaiting AI)",
    SubmissionStatus.AI_GRADED: "AI graded (pending review)",
    SubmissionStatus.FINAL: "Final grade",
}
