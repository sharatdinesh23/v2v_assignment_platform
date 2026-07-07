"""FastAPI application mounted into the Reflex app.

Exposes the Excel results export. The grid is:

    Student name | <test 1> | <test 2> | ...

where each cell is that student's FINAL grade for the test (blank if not
graded yet). Only final grades are exported — AI-provisional grades are never
leaked into results.

The endpoint is guarded by a short-lived signed token (see tokens.py) minted by
the admin session, so the raw APP_SECRET never reaches the browser.
"""
from __future__ import annotations

import io
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from openpyxl import Workbook

from . import db
from .config import settings
from .logging_config import logger
from .models import Role, SubmissionStatus
from .tokens import verify_export_token

fastapi_app = FastAPI(title="Code Arena API")


@fastapi_app.get("/api/health")
def health():
    return {"status": "ok", "appwrite_configured": settings.appwrite_configured}


@fastapi_app.get("/api/export/results.xlsx")
def export_results(token: str = Query(default="")):
    # Short-lived signed token minted by the admin session. The raw secret
    # never reaches the browser; only this expiring HMAC token does.
    if not verify_export_token(token):
        return JSONResponse({"error": "unauthorized or expired"}, status_code=401)

    if not settings.appwrite_configured:
        return JSONResponse({"error": "appwrite not configured"}, status_code=503)

    tests = db.list_tests()
    students = db.list_users(role=Role.STUDENT)
    submissions = db.list_all_submissions()

    # (student_id, test_id) -> final grade
    grade_map: dict[tuple[str, str], str] = {}
    for s in submissions:
        if s.get("status") == SubmissionStatus.FINAL:
            grade_map[(s.get("student_id"), s.get("test_id"))] = s.get(
                "final_grade", ""
            )

    wb = Workbook()
    ws = wb.active
    ws.title = "Results"

    header = ["Student name"] + [t.get("name", "") for t in tests]
    ws.append(header)

    for u in students:
        row = [u.get("name", u.get("email", ""))]
        for t in tests:
            row.append(grade_map.get((u["$id"], t["$id"]), ""))
        ws.append(row)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": "attachment; filename=test_results.xlsx"
        },
    )


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class LogEntry(BaseModel):
    """Frontend log entry schema."""
    level: str
    message: str
    source: str = "frontend"
    user_id: str | None = None
    session_id: str | None = None
    page: str | None = None
    action: str | None = None
    metadata: str | None = None


@fastapi_app.post("/api/logs")
def create_log(log_entry: LogEntry) -> JSONResponse:
    """Receive and store a log entry from the frontend.
    
    Args:
        log_entry: Log entry with level, message, and context
        
    Returns:
        JSON response with status
    """
    try:
        log_data = log_entry.model_dump()
        db.create_log(log_data)
        logger.info(
            f"Frontend log [{log_data['level']}]: {log_data['message']}",
            extra={
                "user_id": log_data.get("user_id"),
                "session_id": log_data.get("session_id"),
                "page": log_data.get("page"),
            },
        )
        return JSONResponse({"status": "ok"}, status_code=201)
    except Exception as e:
        logger.error(f"Error storing frontend log: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@fastapi_app.get("/api/logs")
def list_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    level: str | None = None,
    source: str | None = None,
) -> JSONResponse:
    """List logs from the database.
    
    Args:
        limit: Maximum logs to return
        offset: Number of logs to skip
        level: Filter by log level
        source: Filter by source (backend/frontend)
        
    Returns:
        List of log entries
    """
    try:
        logs = db.list_logs(limit=limit, offset=offset, level=level, source=source)
        return JSONResponse({"logs": logs, "count": len(logs)})
    except Exception as e:
        logger.error(f"Error retrieving logs: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@fastapi_app.get("/api/logs/user/{user_id}")
def get_user_logs(user_id: str, limit: int = Query(100, ge=1, le=500)) -> JSONResponse:
    """Get logs for a specific user.
    
    Args:
        user_id: User ID to filter by
        limit: Maximum logs to return
        
    Returns:
        List of log entries for the user
    """
    try:
        logs = db.get_logs_by_user(user_id, limit=limit)
        return JSONResponse({"logs": logs, "count": len(logs)})
    except Exception as e:
        logger.error(f"Error retrieving user logs: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@fastapi_app.get("/api/logs/session/{session_id}")
def get_session_logs(session_id: str, limit: int = Query(100, ge=1, le=500)) -> JSONResponse:
    """Get logs for a specific session.
    
    Args:
        session_id: Session ID to filter by
        limit: Maximum logs to return
        
    Returns:
        List of log entries for the session
    """
    try:
        logs = db.get_logs_by_session(session_id, limit=limit)
        return JSONResponse({"logs": logs, "count": len(logs)})
    except Exception as e:
        logger.error(f"Error retrieving session logs: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
