"""Loguru-based logging configuration with Appwrite backend storage.

This module sets up structured logging that stores logs in an Appwrite database
with proper timestamps, log levels, sources, and additional context.
Both frontend and backend logs are collected here.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from .config import settings


class AppwriteLogHandler:
    """Custom handler that writes logs to Appwrite database."""

    def __init__(self):
        """Initialize the handler."""
        self.buffer: list[dict[str, Any]] = []
        self.buffer_size = 10
        # Import here to avoid circular imports
        from . import db
        self.db = db

    def write(self, message: str) -> None:
        """Write a log record to Appwrite."""
        try:
            # Parse the loguru record
            record = message
            # Loguru provides the message with record dict
            # We'll extract the necessary parts from the logged message
            
            # This is called per log, so we just pass it to Appwrite
            # The actual record extraction happens in the sink below
            pass
        except Exception as e:
            print(f"Error writing to Appwrite: {e}", file=sys.stderr)


def _appwrite_sink(message: str) -> None:
    """Loguru sink that writes logs to Appwrite database.
    
    This function is called by loguru for each log message.
    It extracts the log record and stores it in Appwrite.
    """
    try:
        from . import db
        
        # Extract the record from loguru's message
        record = message.record
        
        # Prepare the log document
        log_doc = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record["level"].name,
            "level_no": record["level"].no,
            "message": record["message"],
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
            "process_id": record["process"].id,
            "process_name": record["process"].name,
            "thread_id": record["thread"].id,
            "thread_name": record["thread"].name,
            "elapsed_seconds": record["elapsed"].total_seconds(),
            "exception": record["exception"][0].__name__ if record["exception"] else None,
            "source": "backend",  # Default source
        }
        
        # Store in Appwrite
        db.create_log(log_doc)
    except Exception as e:
        # Fallback to stderr if Appwrite fails
        print(f"Error in Appwrite log sink: {e}", file=sys.stderr)


def setup_logging() -> None:
    """Configure loguru with console and Appwrite backends.
    
    This sets up:
    - Console output with color formatting
    - Appwrite database storage with structured fields
    - Proper log rotation and retention
    """
    # Remove the default handler
    logger.remove()
    
    # Add console handler with formatting
    logger.add(
        sys.stdout,
        format=(
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level="DEBUG",
        colorize=True,
    )
    
    # Add file handler for debugging
    log_file = Path("logs/app_{time:YYYY-MM-DD}.log")
    log_file.parent.mkdir(exist_ok=True)
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="500 MB",
        retention="7 days",
    )
    
    # Add Appwrite handler if configured
    if settings.appwrite_configured:
        logger.add(
            _appwrite_sink,
            level="INFO",
            serialize=False,
        )


def log_frontend_event(
    level: str,
    message: str,
    source: str = "frontend",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    page: Optional[str] = None,
    action: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Log frontend events to Appwrite database.
    
    This is a convenience function for frontend logging through HTTP API.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        source: Source identifier (default: "frontend")
        user_id: ID of the user
        session_id: Session ID
        page: Page/component name
        action: Action performed
        metadata: Additional metadata dict
    """
    try:
        from . import db
        
        log_doc = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.upper(),
            "message": message,
            "source": source,
            "user_id": user_id,
            "session_id": session_id,
            "page": page,
            "action": action,
            "metadata": json.dumps(metadata or {}),
        }
        
        db.create_log(log_doc)
    except Exception as e:
        logger.error(f"Failed to log frontend event: {e}")


# Export logger for use throughout the app
__all__ = ["logger", "setup_logging", "log_frontend_event"]
