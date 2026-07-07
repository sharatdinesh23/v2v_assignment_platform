"""Reusable UI pieces shared across pages."""
from __future__ import annotations

import reflex as rx

from ..states.auth_state import AuthState


def top_bar(title: str) -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.icon("code", size=24, color="var(--accent-9)"),
            rx.heading(title, size="5"),
            align="center",
            spacing="2",
        ),
        rx.spacer(),
        rx.hstack(
            rx.text(AuthState.user_name, weight="medium"),
            rx.badge(AuthState.role, variant="soft"),
            rx.button(
                "Log out",
                on_click=AuthState.logout,
                variant="soft",
                color_scheme="gray",
                size="2",
            ),
            align="center",
            spacing="3",
        ),
        width="100%",
        padding="1rem 1.5rem",
        border_bottom="1px solid var(--gray-5)",
        background="var(--color-background)",
        position="sticky",
        top="0",
        z_index="10",
        align="center",
    )


def status_banner(message) -> rx.Component:
    return rx.cond(
        message != "",
        rx.callout(
            message,
            icon="info",
            size="1",
            margin_y="0.75rem",
            width="100%",
        ),
    )


def page_shell(title: str, *children) -> rx.Component:
    return rx.box(
        top_bar(title),
        rx.box(
            *children,
            padding="1.5rem",
            max_width="1100px",
            margin="0 auto",
            width="100%",
        ),
        min_height="100vh",
        background="var(--gray-2)",
    )


class MonacoEditor(rx.Component):
    library = "@monaco-editor/react"
    tag = "Editor"

    theme: rx.Var[str] = "vs-dark"
    language: rx.Var[str] = "python"
    value: rx.Var[str] = ""
    width: rx.Var[str] = "100%"
    height: rx.Var[str] = "450px"
    options: rx.Var[dict] = {
        "minimap": {"enabled": False},
        "fontSize": 14,
        "lineNumbers": "on",
        "scrollBeyondLastLine": False,
        "automaticLayout": True,
        "tabSize": 4,
    }

    def get_event_triggers(self) -> dict[str, rx.Var | str]:
        return {
            "on_change": lambda value: [value]
        }

