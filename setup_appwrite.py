"""One-time Appwrite provisioning script.

Creates the database, the three collections (users / tests / submissions) and
all required attributes + indexes. Safe to re-run: anything that already
exists is skipped.

Usage:
    1. Fill in .env (copy from .env.example).
    2. python setup_appwrite.py

Requires a server API key with `databases.write` scope.
"""
from __future__ import annotations

import sys
import time

from appwrite.client import Client
from appwrite.services.databases import Databases

from code_arena.config import settings


def client() -> Databases:
    if not settings.appwrite_configured:
        sys.exit("ERROR: APPWRITE_PROJECT_ID / APPWRITE_API_KEY not set in .env")
    c = Client()
    c.set_endpoint(settings.appwrite_endpoint)
    c.set_project(settings.appwrite_project_id)
    c.set_key(settings.appwrite_api_key)
    return Databases(c)


def _ignore_conflict(fn, *args, **kwargs):
    """Run an Appwrite create call, ignoring 'already exists' (409) errors."""
    try:
        fn(*args, **kwargs)
        # Appwrite processes attribute creation asynchronously; give it a beat.
        time.sleep(0.4)
        print(f"  + {fn.__name__} {args[2] if len(args) > 2 else ''}")
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        if "already exists" in msg or "409" in msg:
            print(f"  = exists: {args[2] if len(args) > 2 else fn.__name__}")
        else:
            print(f"  ! {fn.__name__}: {msg}")


def main() -> None:
    db = client()
    dbid = settings.database_id

    print("Database…")
    _ignore_conflict(db.create, dbid, "Code Arena")

    # ---- users ----------------------------------------------------------
    print("Collection: users")
    _ignore_conflict(db.create_collection, dbid, settings.users_collection, "users")
    _ignore_conflict(db.create_string_attribute, dbid, settings.users_collection, "email", 255, True)
    _ignore_conflict(db.create_string_attribute, dbid, settings.users_collection, "name", 255, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.users_collection, "role", 32, True)
    _ignore_conflict(db.create_string_attribute, dbid, settings.users_collection, "password_hash", 255, True)
    _ignore_conflict(db.create_integer_attribute, dbid, settings.users_collection, "created_at", False)
    _ignore_conflict(db.create_index, dbid, settings.users_collection, "email_idx", "unique", ["email"])
    _ignore_conflict(db.create_index, dbid, settings.users_collection, "role_idx", "key", ["role"])

    # ---- tests ----------------------------------------------------------
    print("Collection: tests")
    _ignore_conflict(db.create_collection, dbid, settings.tests_collection, "tests")
    _ignore_conflict(db.create_string_attribute, dbid, settings.tests_collection, "name", 255, True)
    _ignore_conflict(db.create_integer_attribute, dbid, settings.tests_collection, "end_at", True)
    _ignore_conflict(db.create_string_attribute, dbid, settings.tests_collection, "question", 10000, True)
    _ignore_conflict(db.create_string_attribute, dbid, settings.tests_collection, "expected_input", 10000, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.tests_collection, "expected_output", 10000, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.tests_collection, "created_by", 64, False)
    _ignore_conflict(db.create_integer_attribute, dbid, settings.tests_collection, "created_at", False)

    # ---- submissions ----------------------------------------------------
    print("Collection: submissions")
    _ignore_conflict(db.create_collection, dbid, settings.submissions_collection, "submissions")
    _ignore_conflict(db.create_string_attribute, dbid, settings.submissions_collection, "test_id", 64, True)
    _ignore_conflict(db.create_string_attribute, dbid, settings.submissions_collection, "student_id", 64, True)
    _ignore_conflict(db.create_string_attribute, dbid, settings.submissions_collection, "student_name", 255, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.submissions_collection, "files_json", 100000, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.submissions_collection, "entry_file", 255, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.submissions_collection, "code", 100000, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.submissions_collection, "status", 32, True)
    _ignore_conflict(db.create_string_attribute, dbid, settings.submissions_collection, "ai_grade", 32, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.submissions_collection, "ai_feedback", 10000, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.submissions_collection, "final_grade", 32, False)
    _ignore_conflict(db.create_integer_attribute, dbid, settings.submissions_collection, "submitted_at", False)
    _ignore_conflict(db.create_index, dbid, settings.submissions_collection, "test_student_idx", "key", ["test_id", "student_id"])
    _ignore_conflict(db.create_index, dbid, settings.submissions_collection, "student_idx", "key", ["student_id"])

    # ---- logs -----------------------------------------------------------
    print("Collection: logs")
    _ignore_conflict(db.create_collection, dbid, settings.logs_collection, "logs")
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "timestamp", 50, True)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "level", 32, True)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "message", 5000, True)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "module", 255, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "function", 255, False)
    _ignore_conflict(db.create_integer_attribute, dbid, settings.logs_collection, "line", False)
    _ignore_conflict(db.create_integer_attribute, dbid, settings.logs_collection, "level_no", False)
    _ignore_conflict(db.create_integer_attribute, dbid, settings.logs_collection, "process_id", False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "process_name", 255, False)
    _ignore_conflict(db.create_integer_attribute, dbid, settings.logs_collection, "thread_id", False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "thread_name", 255, False)
    _ignore_conflict(db.create_float_attribute, dbid, settings.logs_collection, "elapsed_seconds", False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "exception", 255, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "source", 50, True)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "user_id", 64, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "session_id", 255, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "page", 255, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "action", 255, False)
    _ignore_conflict(db.create_string_attribute, dbid, settings.logs_collection, "metadata", 10000, False)
    _ignore_conflict(db.create_index, dbid, settings.logs_collection, "timestamp_idx", "key", ["timestamp"])
    _ignore_conflict(db.create_index, dbid, settings.logs_collection, "level_idx", "key", ["level"])
    _ignore_conflict(db.create_index, dbid, settings.logs_collection, "source_idx", "key", ["source"])
    _ignore_conflict(db.create_index, dbid, settings.logs_collection, "user_idx", "key", ["user_id"])
    _ignore_conflict(db.create_index, dbid, settings.logs_collection, "session_idx", "key", ["session_id"])

    print("\nDone. If some attributes show '!', wait a few seconds and re-run.")


if __name__ == "__main__":
    main()
