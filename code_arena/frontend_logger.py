"""Frontend logging utilities for Reflex components.

This module provides functions to send logs from the frontend to the backend
via HTTP API, which then stores them in the Appwrite database.
"""
from __future__ import annotations

import json
from typing import Any, Optional

import httpx


class FrontendLogger:
    """Logger for frontend events that sends logs to the backend."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the frontend logger.
        
        Args:
            base_url: Base URL of the backend API
        """
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.user_id: Optional[str] = None

    def set_user_context(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Set user and session context for logging.
        
        Args:
            user_id: User ID for logs
            session_id: Session ID for logs
        """
        self.user_id = user_id
        self.session_id = session_id

    def _send_log(self, log_data: dict[str, Any]) -> bool:
        """Send a log entry to the backend.
        
        Args:
            log_data: Log data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/logs"
            with httpx.Client() as client:
                response = client.post(url, json=log_data, timeout=5)
                return response.status_code in (200, 201)
        except Exception as e:
            # Silently fail to avoid breaking frontend
            print(f"Failed to send log: {e}")
            return False

    def debug(
        self,
        message: str,
        page: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log a debug message."""
        self._log("DEBUG", message, page, action, metadata)

    def info(
        self,
        message: str,
        page: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log an info message."""
        self._log("INFO", message, page, action, metadata)

    def warning(
        self,
        message: str,
        page: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log a warning message."""
        self._log("WARNING", message, page, action, metadata)

    def error(
        self,
        message: str,
        page: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log an error message."""
        self._log("ERROR", message, page, action, metadata)

    def critical(
        self,
        message: str,
        page: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log a critical message."""
        self._log("CRITICAL", message, page, action, metadata)

    def _log(
        self,
        level: str,
        message: str,
        page: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Internal method to log a message.
        
        Args:
            level: Log level
            message: Log message
            page: Page/component name
            action: Action performed
            metadata: Additional metadata
        """
        log_data = {
            "level": level,
            "message": message,
            "source": "frontend",
            "user_id": self.user_id,
            "session_id": self.session_id,
            "page": page,
            "action": action,
            "metadata": json.dumps(metadata or {}),
        }
        self._send_log(log_data)

    def log_page_view(
        self,
        page_name: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log a page view event.
        
        Args:
            page_name: Name of the page viewed
            metadata: Additional metadata (route, referrer, etc.)
        """
        self.info(
            f"Page viewed: {page_name}",
            page=page_name,
            action="page_view",
            metadata=metadata,
        )

    def log_user_action(
        self,
        action_name: str,
        page: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log a user action event.
        
        Args:
            action_name: Name of the action (e.g., "button_click", "form_submit")
            page: Page where action occurred
            details: Additional details about the action
        """
        self.info(
            f"User action: {action_name}",
            page=page,
            action=action_name,
            metadata=details,
        )

    def log_error(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        page: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> None:
        """Log an error event.
        
        Args:
            error_message: Error message
            error_type: Type of error
            page: Page where error occurred
            stack_trace: Stack trace (if available)
        """
        metadata = {
            "error_type": error_type,
            "stack_trace": stack_trace,
        }
        self.error(
            error_message,
            page=page,
            action="error",
            metadata=metadata,
        )


# Global instance for use in components
frontend_logger = FrontendLogger()
