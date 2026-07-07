"""Appwrite data-access layer.

A thin, well-typed wrapper over the Appwrite server SDK. Every operation the
app needs (users, tests, submissions) lives here so the rest of the code never
touches the raw SDK. All methods return plain dicts.

The Appwrite endpoint + API key are read from :mod:`code_arena.config`, which
in turn reads them from the environment / ``.env`` file.
"""
from __future__ import annotations

import json
import sys
import time
from typing import Any, Optional

from appwrite.client import Client
from appwrite.id import ID
from appwrite.query import Query
from appwrite.services.databases import Databases

from .config import settings
from .models import Role, SubmissionStatus
from .security import hash_password


class AppwriteError(RuntimeError):
    """Raised when Appwrite is not configured or a call fails."""


def _client() -> Client:
    if not settings.appwrite_configured:
        raise AppwriteError(
            "Appwrite is not configured. Set APPWRITE_PROJECT_ID and "
            "APPWRITE_API_KEY in your .env file."
        )
    client = Client()
    client.set_endpoint(settings.appwrite_endpoint)
    client.set_project(settings.appwrite_project_id)
    client.set_key(settings.appwrite_api_key)
    return client


def _db() -> Databases:
    return Databases(_client())


def _normalize_document(doc: Any) -> dict[str, Any]:
    """Convert Appwrite document objects to plain dictionaries."""
    if doc is None:
        return {}
    if isinstance(doc, dict):
        return doc

    data: dict[str, Any] = {}

    if hasattr(doc, "to_dict"):
        try:
            data = dict(doc.to_dict())
        except Exception:
            data = {}

    if not data and hasattr(doc, "to_json"):
        try:
            raw = doc.to_json()
            if isinstance(raw, str):
                data = json.loads(raw)
            elif isinstance(raw, dict):
                data = dict(raw)
        except Exception:
            data = {}

    if not data and hasattr(doc, "data"):
        try:
            payload = getattr(doc, "data")
            if isinstance(payload, dict):
                data = dict(payload)
        except Exception:
            data = {}

    if not data and hasattr(doc, "__dict__"):
        data = {
            key: value
            for key, value in vars(doc).items()
            if not key.startswith("_") and not callable(value)
        }

    if not data and hasattr(doc, "get"):
        try:
            data = dict(doc)
        except Exception:
            data = {}

    if isinstance(data, dict):
        nested_data = data.get("data")
        if isinstance(nested_data, dict):
            merged = dict(nested_data)
            for key, value in data.items():
                if key != "data":
                    merged.setdefault(key, value)
            data = merged

        if "$id" not in data and hasattr(doc, "id"):
            data["$id"] = getattr(doc, "id")
        if "$collectionId" not in data and hasattr(doc, "collectionid"):
            data["$collectionId"] = getattr(doc, "collectionid")
        if "$databaseId" not in data and hasattr(doc, "databaseid"):
            data["$databaseId"] = getattr(doc, "databaseid")
        if "$createdAt" not in data and hasattr(doc, "createdat"):
            data["$createdAt"] = getattr(doc, "createdat")
        if "$updatedAt" not in data and hasattr(doc, "updatedat"):
            data["$updatedAt"] = getattr(doc, "updatedat")
        return data

    return {}


def _normalize_documents(result: Any) -> list[dict[str, Any]]:
    """Handle both dict-style and Appwrite SDK object-style list responses."""
    if result is None:
        return []
    if isinstance(result, dict):
        documents = result.get("documents", [])
    else:
        documents = getattr(result, "documents", None)
        if documents is None and hasattr(result, "get"):
            try:
                documents = result.get("documents", [])
            except Exception:
                documents = None
    if documents is None:
        return []
    if isinstance(documents, list):
        return [_normalize_document(doc) for doc in documents]
    return []


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
def get_user_by_email(email: str) -> Optional[dict[str, Any]]:
    email = email.strip().lower()
    res = _db().list_documents(
        settings.database_id,
        settings.users_collection,
        [Query.equal("email", email), Query.limit(1)],
    )
    
    docs = _normalize_documents(res)
    return docs[0] if docs else None


def list_users(role: Optional[str] = None) -> list[dict[str, Any]]:
    queries = [Query.limit(200), Query.order_asc("name")]
    if role:
        queries.append(Query.equal("role", role))
    res = _db().list_documents(
        settings.database_id, settings.users_collection, queries
    )
    return _normalize_documents(res)


def create_user(
    email: str,
    password: str,
    name: str,
    role: str = Role.STUDENT,
) -> dict[str, Any]:
    email = email.strip().lower()
    if get_user_by_email(email):
        raise AppwriteError(f"A user with email {email} already exists.")
    data = {
        "email": email,
        "name": name or email,
        "role": role,
        "password_hash": hash_password(password),
        "created_at": int(time.time()),
    }
    return _db().create_document(
        settings.database_id,
        settings.users_collection,
        ID.unique(),
        data,
    )


def delete_user(user_id: str) -> None:
    _db().delete_document(
        settings.database_id, settings.users_collection, user_id
    )


def update_user_password_hash(user_id: str, password_hash: str) -> None:
    _db().update_document(
        settings.database_id,
        settings.users_collection,
        user_id,
        {"password_hash": password_hash},
    )


def ensure_seed_admin() -> None:
    """Create the seed admin from .env on first run (idempotent)."""
    if not settings.appwrite_configured:
        return
    existing = get_user_by_email(settings.seed_admin_email)
    if existing:
        return
    create_user(
        email=settings.seed_admin_email,
        password=settings.seed_admin_password,
        name=settings.seed_admin_name,
        role=Role.ADMIN,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def create_test(
    name: str,
    end_at: int,
    question: str,
    expected_input: str,
    expected_output: str,
    created_by: str,
) -> dict[str, Any]:
    payload = f"{question}\n\nExpected input:\n{expected_input or '(none)'}\n\nExpected output:\n{expected_output or '(none)'}"
    data = {
        "name": name,
        "end_at": str(int(end_at)),
        "question": payload,
    }
    return _db().create_document(
        settings.database_id,
        settings.tests_collection,
        ID.unique(),
        data,
    )


def list_tests() -> list[dict[str, Any]]:
    res = _db().list_documents(
        settings.database_id,
        settings.tests_collection,
        [Query.limit(200)],
    )
    return _normalize_documents(res)


def get_test(test_id: str) -> Optional[dict[str, Any]]:
    try:
        return _db().get_document(
            settings.database_id, settings.tests_collection, test_id
        )
    except Exception:
        return None


def delete_test(test_id: str) -> None:
    _db().delete_document(
        settings.database_id, settings.tests_collection, test_id
    )


# ---------------------------------------------------------------------------
# Submissions
# ---------------------------------------------------------------------------
def get_submission(test_id: str, student_id: str) -> Optional[dict[str, Any]]:
    res = _db().list_documents(
        settings.database_id,
        settings.submissions_collection,
        [
            Query.equal("test_id", test_id),
            Query.equal("student_id", student_id),
            Query.limit(1),
        ],
    )
    docs = _normalize_documents(res)
    return docs[0] if docs else None


def list_submissions_for_student(student_id: str) -> list[dict[str, Any]]:
    res = _db().list_documents(
        settings.database_id,
        settings.submissions_collection,
        [Query.equal("student_id", student_id), Query.limit(500)],
    )
    return _normalize_documents(res)


def list_submissions_for_test(test_id: str) -> list[dict[str, Any]]:
    res = _db().list_documents(
        settings.database_id,
        settings.submissions_collection,
        [Query.equal("test_id", test_id), Query.limit(500)],
    )
    return _normalize_documents(res)


def list_all_submissions() -> list[dict[str, Any]]:
    res = _db().list_documents(
        settings.database_id,
        settings.submissions_collection,
        [Query.limit(2000)],
    )
    return _normalize_documents(res)


def upsert_submission(
    test_id: str,
    student_id: str,
    student_name: str,
    files: dict[str, str],
    entry_file: str,
) -> dict[str, Any]:
    """Create or update a student's submission and mark it as SUBMITTED.

    ``files`` is a mapping of path -> content for the dummy code editor. It is
    stored as a JSON string so it survives a single Appwrite string attribute.
    """
    payload = {
        "test_id": test_id,
        "student_id": student_id,
        "student_name": student_name,
        "files_json": json.dumps(files),
        "entry_file": entry_file,
        "code": files.get(entry_file, ""),
        "status": SubmissionStatus.SUBMITTED,
        "ai_grade": "",
        "ai_feedback": "",
        "final_grade": "",
        "submitted_at": int(time.time()),
    }
    existing = get_submission(test_id, student_id)
    if existing:
        return _db().update_document(
            settings.database_id,
            settings.submissions_collection,
            existing["$id"],
            payload,
        )
    return _db().create_document(
        settings.database_id,
        settings.submissions_collection,
        ID.unique(),
        payload,
    )


def set_ai_grade(submission_id: str, grade: str, feedback: str) -> dict[str, Any]:
    return _db().update_document(
        settings.database_id,
        settings.submissions_collection,
        submission_id,
        {
            "ai_grade": grade,
            "ai_feedback": feedback,
            "status": SubmissionStatus.AI_GRADED,
        },
    )


def set_final_grade(submission_id: str, grade: str) -> dict[str, Any]:
    return _db().update_document(
        settings.database_id,
        settings.submissions_collection,
        submission_id,
        {"final_grade": grade, "status": SubmissionStatus.FINAL},
    )


def reset_to_ai_pending(submission_id: str) -> dict[str, Any]:
    """Admin chose 'redo' -> push back to SUBMITTED so AI grades again."""
    return _db().update_document(
        settings.database_id,
        settings.submissions_collection,
        submission_id,
        {"status": SubmissionStatus.SUBMITTED, "ai_grade": "", "ai_feedback": ""},
    )


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def create_log(log_data: dict[str, Any]) -> dict[str, Any]:
    """Store a log entry in the database.
    
    Args:
        log_data: Dictionary containing log information with fields:
            - timestamp: ISO format timestamp
            - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            - message: Log message
            - module: Module name
            - function: Function name
            - line: Line number
            - source: "backend" or "frontend"
            - user_id (optional): Associated user ID
            - session_id (optional): Session ID
            - page (optional): Page/component name
            - action (optional): Action performed
            - metadata (optional): Additional metadata JSON
    """
    if not settings.appwrite_configured:
        return {}
    
    # Ensure timestamp exists
    if "timestamp" not in log_data:
        log_data["timestamp"] = int(time.time())
    
    # Ensure level exists
    if "level" not in log_data:
        log_data["level"] = "INFO"
    
    # Ensure message exists
    if "message" not in log_data:
        log_data["message"] = ""
    
    # Ensure source exists
    if "source" not in log_data:
        log_data["source"] = "unknown"
    
    try:
        return _db().create_document(
            settings.database_id,
            settings.logs_collection,
            ID.unique(),
            log_data,
        )
    except Exception as e:
        # If logging fails, don't crash the app
        print(f"Error creating log entry: {e}", file=sys.stderr)
        return {}


def list_logs(
    limit: int = 100,
    offset: int = 0,
    level: Optional[str] = None,
    source: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Retrieve logs from the database.
    
    Args:
        limit: Maximum number of logs to return
        offset: Number of logs to skip
        level: Filter by log level
        source: Filter by source (backend/frontend)
    """
    if not settings.appwrite_configured:
        return []
    
    queries = [
        Query.order_desc("timestamp"),
        Query.limit(min(limit, 500)),
        Query.offset(offset),
    ]
    
    if level:
        queries.append(Query.equal("level", level.upper()))
    
    if source:
        queries.append(Query.equal("source", source.lower()))
    
    try:
        res = _db().list_documents(
            settings.database_id,
            settings.logs_collection,
            queries,
        )
        return _normalize_documents(res)
    except Exception as e:
        print(f"Error listing logs: {e}", file=sys.stderr)
        return []


def get_logs_by_user(user_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """Get all logs associated with a specific user.
    
    Args:
        user_id: User ID to filter by
        limit: Maximum number of logs to return
    """
    if not settings.appwrite_configured:
        return []
    
    try:
        res = _db().list_documents(
            settings.database_id,
            settings.logs_collection,
            [
                Query.equal("user_id", user_id),
                Query.order_desc("timestamp"),
                Query.limit(min(limit, 500)),
            ],
        )
        return _normalize_documents(res)
    except Exception as e:
        print(f"Error getting user logs: {e}", file=sys.stderr)
        return []


def get_logs_by_session(session_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """Get all logs from a specific session.
    
    Args:
        session_id: Session ID to filter by
        limit: Maximum number of logs to return
    """
    if not settings.appwrite_configured:
        return []
    
    try:
        res = _db().list_documents(
            settings.database_id,
            settings.logs_collection,
            [
                Query.equal("session_id", session_id),
                Query.order_desc("timestamp"),
                Query.limit(min(limit, 500)),
            ],
        )
        return _normalize_documents(res)
    except Exception as e:
        print(f"Error getting session logs: {e}", file=sys.stderr)
        return []
