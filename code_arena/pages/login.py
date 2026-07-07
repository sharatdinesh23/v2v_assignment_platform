"""Login page (shared by admins and students)."""
from __future__ import annotations

import reflex as rx

from ..states.auth_state import AuthState


def login_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("code", size=28, color="var(--accent-9)"),
                    rx.heading("Code Arena", size="7"),
                    align="center",
                    spacing="2",
                ),
                rx.text(
                    "Sign in to continue",
                    color="var(--gray-11)",
                    size="2",
                ),
                rx.divider(),
                rx.text("Email", size="2", weight="medium"),
                rx.input(
                    placeholder="you@example.com",
                    value=AuthState.login_email,
                    on_change=AuthState.set_login_email,
                    width="100%",
                    size="3",
                ),
                rx.text("Password", size="2", weight="medium"),
                rx.input(
                    placeholder="password",
                    type="password",
                    value=AuthState.login_password,
                    on_change=AuthState.set_login_password,
                    width="100%",
                    size="3",
                ),
                rx.cond(
                    AuthState.error != "",
                    rx.callout(
                        AuthState.error,
                        icon="triangle_alert",
                        color_scheme="red",
                        size="1",
                        width="100%",
                    ),
                ),
                rx.button(
                    rx.cond(AuthState.loading, "Signing in…", "Sign in"),
                    on_click=AuthState.do_login,
                    width="100%",
                    size="3",
                    disabled=AuthState.loading,
                ),
                rx.text(
                    "Students: your password is your email address.",
                    size="1",
                    color="var(--gray-10)",
                ),
                spacing="3",
                width="100%",
            ),
            width="380px",
            max_width="92vw",
            padding="1.5rem",
        ),
        min_height="100vh",
        background="var(--gray-2)",
    )
