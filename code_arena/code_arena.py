"""Application entry point.

Wires the Reflex frontend together, mounts the FastAPI backend (for the Excel
export endpoint), and registers the role-guarded pages.

Run with:  reflex run
"""
from __future__ import annotations

import reflex as rx

from .api import fastapi_app
from .logging_config import setup_logging, logger
from .states.admin_state import AdminState
from .states.auth_state import AuthState
from .states.student_state import StudentState
from .pages.admin_dashboard import admin_dashboard
from .pages.login import login_page
from .pages.student_dashboard import student_dashboard

# Initialize logging
setup_logging()
logger.info("Initializing Code Arena application")

# The Reflex app. Passing ``api_transformer`` mounts our FastAPI application so
# both the UI and the /api/* routes are served by a single process.
app = rx.App(
    api_transformer=fastapi_app,
    theme=rx.theme(
        appearance="dark",
        accent_color="indigo",
        radius="large",
        scaling="100%",
    ),
)

# Public login page. If already signed in, bounce to the right dashboard.
app.add_page(
    login_page,
    route="/",
    title="Sign in · Code Arena",
    on_load=AuthState.redirect_if_authed,
)

# Admin area (guarded server-side by require_admin inside load_dashboard).
app.add_page(
    admin_dashboard,
    route="/admin",
    title="Admin · Code Arena",
    on_load=AdminState.load_dashboard,
)

# Student area (guarded server-side by require_student inside load_dashboard).
app.add_page(
    student_dashboard,
    route="/student",
    title="Student · Code Arena",
    on_load=StudentState.load_dashboard,
)
