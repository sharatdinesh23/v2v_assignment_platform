"""Student dashboard: solved / unsolved questions + a VS Code-like editor."""
from __future__ import annotations

import reflex as rx

from ..states.student_state import StudentState
from .components import page_shell, status_banner, MonacoEditor


def _file_tree_item(item: dict) -> rx.Component:
    indent = rx.cond(
        item["depth"] == 1,
        "20px",
        rx.cond(
            item["depth"] == 2,
            "32px",
            rx.cond(
                item["depth"] == 3,
                "44px",
                "8px"
            )
        )
    )

    chevron = rx.cond(
        item["kind"] == "folder",
        rx.cond(
            item["is_expanded"],
            rx.icon("chevron-down", size=14, color="var(--gray-9)"),
            rx.icon("chevron-right", size=14, color="var(--gray-9)"),
        ),
        rx.box(width="14px")  # Spacer for alignment if file
    )

    item_icon = rx.cond(
        item["kind"] == "folder",
        rx.cond(
            item["is_expanded"],
            rx.icon("folder-open", size=15, color="var(--accent-9)"),
            rx.icon("folder", size=15, color="var(--accent-9)"),
        ),
        rx.icon("file-code", size=15, color="var(--gray-10)"),
    )

    # Hover buttons for quick actions (VS Code style)
    action_buttons = rx.cond(
        item["kind"] == "folder",
        rx.hstack(
            rx.icon(
                "file-plus",
                size=13,
                color="var(--gray-10)",
                cursor="pointer",
                on_click=lambda: StudentState.open_create_dialog(item["path"], "file"),
                style={"opacity": "0.6", "&:hover": {"opacity": "1"}},
            ),
            rx.icon(
                "folder-plus",
                size=13,
                color="var(--gray-10)",
                cursor="pointer",
                on_click=lambda: StudentState.open_create_dialog(item["path"], "folder"),
                style={"opacity": "0.6", "&:hover": {"opacity": "1"}},
            ),
            rx.icon(
                "trash-2",
                size=13,
                color="var(--red-9)",
                cursor="pointer",
                on_click=lambda: StudentState.delete_folder(item["path"]),
                style={"opacity": "0.6", "&:hover": {"opacity": "1"}},
            ),
            spacing="1",
        ),
        rx.cond(
            item['path'] != "main.py",
            rx.icon(
                "trash-2",
                size=13,
                color="var(--red-9)",
                cursor="pointer",
                on_click=lambda: StudentState.delete_file(item['path']),
                style={"opacity": "0.6", "&:hover": {"opacity": "1"}},
            ),
            rx.box()
        )
    )

    # The actual tree item row
    tree_item_row = rx.hstack(
        chevron,
        item_icon,
        rx.text(item["name"], size="2", overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
        rx.spacer(),
        action_buttons,
        padding_left=indent,
        padding_y="0.25rem",
        padding_right="0.5rem",
        border_radius="0.25rem",
        background=rx.cond(
            StudentState.active_file == item["path"],
            "var(--accent-3)",
            "transparent",
        ),
        color=rx.cond(
            StudentState.active_file == item["path"],
            "var(--accent-11)",
            "var(--gray-12)",
        ),
        _hover={"background": "var(--gray-3)"},
        align="center",
        spacing="2",
        cursor="pointer",
        on_click=lambda: StudentState.select_path(item["path"]),
        width="100%",
    )

    # Wrap inside standard Radix Context Menu for right-click capabilities
    return rx.context_menu.root(
        rx.context_menu.trigger(tree_item_row),
        rx.context_menu.content(
            rx.cond(
                item["kind"] == "folder",
                rx.fragment(
                    rx.context_menu.item(
                        rx.hstack(rx.icon("file-plus", size=14), rx.text("New File")),
                        on_select=lambda: StudentState.open_create_dialog(item["path"], "file")
                    ),
                    rx.context_menu.item(
                        rx.hstack(rx.icon("folder-plus", size=14), rx.text("New Folder")),
                        on_select=lambda: StudentState.open_create_dialog(item["path"], "folder")
                    ),
                    rx.context_menu.separator(),
                    rx.context_menu.item(
                        rx.hstack(rx.icon("trash-2", size=14), rx.text("Delete Folder")),
                        color_scheme="red",
                        on_select=lambda: StudentState.delete_folder(item["path"])
                    ),
                ),
                rx.fragment(
                    rx.cond(
                        item["path"] != "main.py",
                        rx.context_menu.item(
                            rx.hstack(rx.icon("trash-2", size=14), rx.text("Delete File")),
                            color_scheme="red",
                            on_select=lambda: StudentState.delete_file(item["path"])
                        ),
                        rx.context_menu.item("Delete File (Locked)", disabled=True)
                    )
                )
            )
        )
    )


def _editor_dialog() -> rx.Component:
    # Explorer pane content
    explorer_pane = rx.vstack(
        rx.hstack(
            rx.text("EXPLORER", size="1", weight="bold", color="var(--gray-9)"),
            rx.spacer(),
            # Root creation actions
            rx.icon(
                "file-plus",
                size=13,
                color="var(--gray-10)",
                cursor="pointer",
                on_click=lambda: StudentState.open_create_dialog("", "file"),
                style={"opacity": "0.6", "&:hover": {"opacity": "1"}},
            ),
            rx.icon(
                "folder-plus",
                size=13,
                color="var(--gray-10)",
                cursor="pointer",
                on_click=lambda: StudentState.open_create_dialog("", "folder"),
                style={"opacity": "0.6", "&:hover": {"opacity": "1"}},
            ),
            spacing="2",
            width="100%",
            padding_bottom="0.5rem",
        ),
        rx.divider(margin_y="0.25rem"),
        # File Tree scrollable area
        rx.scroll_area(
            rx.vstack(
                rx.foreach(StudentState.file_tree_items, _file_tree_item),
                spacing="1",
                width="100%",
            ),
            height="380px",
            type="always",
            width="100%",
        ),
        width="100%",
        spacing="2",
        padding="0.75rem",
        background="var(--gray-2)",
        height="100%",
    )

    # Drawer for mobile file tree
    mobile_explorer_drawer = rx.drawer.root(
        rx.drawer.overlay(),
        rx.drawer.portal(
            rx.drawer.content(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Workspace Explorer", size="4"),
                        rx.spacer(),
                        rx.drawer.close(
                            rx.button("Close", size="1", variant="soft", on_click=StudentState.close_mobile_explorer)
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.divider(),
                    explorer_pane,
                    spacing="3",
                    padding="1.5rem",
                    height="100%",
                ),
                background="var(--gray-1)",
                height="80vh",
                position="bottom",
                border_radius="1rem 1rem 0 0",
            )
        ),
        open=StudentState.show_mobile_explorer,
    )

    return rx.dialog.root(
        rx.dialog.content(
            # Top header bar
            rx.hstack(
                rx.hstack(
                    rx.icon("code", size=18, color="var(--accent-9)"),
                    rx.heading(StudentState.active_test_name, size="4"),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                # Actions (Submit, Save, Close)
                rx.hstack(
                    rx.button(
                        rx.icon("save", size=14),
                        "Save Draft",
                        variant="soft",
                        on_click=StudentState.save_only,
                        size="2",
                    ),
                    rx.button(
                        rx.icon("send", size=14),
                        "Submit",
                        color_scheme="green",
                        on_click=StudentState.submit_solution,
                        size="2",
                    ),
                    rx.dialog.close(
                        rx.button(
                            "Close",
                            variant="soft",
                            color_scheme="gray",
                            on_click=StudentState.close_editor,
                            size="2",
                        )
                    ),
                    spacing="2",
                ),
                width="100%",
                padding_bottom="0.75rem",
                border_bottom="1px solid var(--gray-4)",
            ),

            # Workspace area
            rx.grid(
                # Problem statement
                rx.box(
                    rx.vstack(
                        rx.text("Problem Description", size="2", weight="bold", color="var(--gray-11)"),
                        rx.scroll_area(
                            rx.text(
                                StudentState.active_question,
                                size="2",
                                white_space="pre-wrap",
                                color="var(--gray-11)",
                            ),
                            height="180px",
                            type="always",
                            scrollbars="vertical",
                        ),
                        padding="0.75rem",
                        border="1px solid var(--gray-4)",
                        border_radius="0.5rem",
                        background="var(--gray-2)",
                        height="100%",
                    ),
                    grid_column="span 12",
                ),
                # Left Sidebar (Desktop Explorer)
                rx.box(
                    rx.hstack(
                        # Activity bar simulation
                        rx.vstack(
                            rx.icon("files", size=18, color="var(--accent-9)"),
                            rx.spacer(),
                            width="40px",
                            background="var(--gray-3)",
                            align="center",
                            padding_y="0.5rem",
                            height="100%",
                            border_right="1px solid var(--gray-4)",
                        ),
                        explorer_pane,
                        height="100%",
                        width="100%",
                        spacing="0",
                    ),
                    display=["none", "none", "block"],  # hide on mobile/tablet
                    grid_column="span 3",
                    border="1px solid var(--gray-4)",
                    border_radius="0.5rem",
                    overflow="hidden",
                ),
                # Main Editor Pane
                rx.box(
                    rx.vstack(
                        # Editor Header (Tabs)
                        rx.hstack(
                            # Mobile Explorer Trigger
                            rx.button(
                                rx.icon("menu", size=14),
                                "Files",
                                size="1",
                                variant="soft",
                                on_click=StudentState.toggle_mobile_explorer,
                                display=["block", "block", "none"],
                            ),
                            # Active tab name
                            rx.hstack(
                                rx.icon("file-code", size=14, color="var(--accent-9)"),
                                rx.text(StudentState.active_file, size="2", weight="medium"),
                                padding="0.25rem 0.75rem",
                                background="var(--gray-3)",
                                border_radius="0.25rem 0.25rem 0 0",
                                align="center",
                                spacing="2",
                                height="100%",
                            ),
                            width="100%",
                            background="var(--gray-2)",
                            padding="0.25rem",
                            border_bottom="1px solid var(--gray-4)",
                            align="center",
                        ),
                        # Monaco editor
                        MonacoEditor.create(
                            value=StudentState.active_content,
                            on_change=StudentState.edit_content,
                            height="350px",
                        ),
                        # Bottom info bar
                        rx.hstack(
                            rx.text("Language: Python", size="1", color="var(--gray-10)"),
                            rx.spacer(),
                            rx.text(f"File: {StudentState.active_file}", size="1", color="var(--gray-10)"),
                            width="100%",
                            padding="0.25rem 0.5rem",
                            background="var(--gray-3)",
                            border_radius="0 0 0.5rem 0.5rem",
                        ),
                        width="100%",
                        spacing="0",
                    ),
                    grid_column=["span 12", "span 12", "span 9"],
                    border="1px solid var(--gray-4)",
                    border_radius="0.5rem",
                    overflow="hidden",
                ),
                columns="12",
                spacing="3",
                width="100%",
                margin_top="0.75rem",
            ),
            mobile_explorer_drawer,
            max_width="1100px",
            width="98vw",
            height="90vh",
        ),
        open=StudentState.show_editor,
    )


def _solved_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(StudentState.solved_test_name),
            rx.vstack(
                rx.hstack(
                    rx.badge(StudentState.solved_status_label),
                    rx.text("Grade:", size="2"),
                    rx.badge(StudentState.solved_grade, color_scheme="green"),
                    spacing="2",
                ),
                rx.text("Your submission", size="2", weight="medium"),
                rx.scroll_area(
                    rx.code_block(
                        StudentState.solved_code,
                        language="python",
                        width="100%",
                    ),
                    height="260px",
                    type="always",
                    scrollbars="vertical",
                    width="100%",
                ),
                rx.cond(
                    StudentState.solved_feedback != "",
                    rx.callout(
                        StudentState.solved_feedback,
                        icon="message-square",
                        size="1",
                        width="100%",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Close",
                        variant="soft",
                        color_scheme="gray",
                        on_click=StudentState.close_solved,
                    )
                ),
                justify="end",
                margin_top="1rem",
            ),
            max_width="640px",
        ),
        open=StudentState.show_solved,
    )


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------
def _unsolved_card(t: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(t["name"], size="4"),
                rx.spacer(),
                rx.badge("Unsolved", color_scheme="red", variant="soft"),
                width="100%",
                align="center",
            ),
            rx.text(
                t["question"],
                size="2",
                color="var(--gray-11)",
                no_of_lines=2,
            ),
            rx.hstack(
                rx.icon("clock", size=14, color="var(--gray-10)"),
                rx.text("Ends " + t["end_at"], size="1", color="var(--gray-10)"),
                spacing="1",
                align="center",
            ),
            rx.button(
                rx.icon("code", size=15),
                "Open & solve",
                on_click=lambda: StudentState.open_editor(t["id"]),
                width="100%",
                margin_top="0.5rem",
            ),
            spacing="2",
            width="100%",
        ),
        width="100%",
    )


def _solved_card(t: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(t["name"], size="4"),
                rx.spacer(),
                rx.badge(t["status_label"], color_scheme="green", variant="soft"),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.text("Grade:", size="2"),
                rx.badge(t["grade"], color_scheme="jade"),
                spacing="2",
            ),
            rx.button(
                rx.icon("eye", size=15),
                "View submission",
                variant="soft",
                on_click=lambda: StudentState.open_solved(t["id"]),
                width="100%",
                margin_top="0.5rem",
            ),
            spacing="2",
            width="100%",
        ),
        width="100%",
    )


def _password_settings() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Password settings", size="4"),
            rx.text("Change your password anytime.", size="2", color="var(--gray-11)"),
            rx.input(
                placeholder="Current password",
                type="password",
                value=StudentState.current_password,
                on_change=StudentState.set_current_password,
                width="100%",
            ),
            rx.input(
                placeholder="New password",
                type="password",
                value=StudentState.new_password,
                on_change=StudentState.set_new_password,
                width="100%",
            ),
            rx.input(
                placeholder="Confirm new password",
                type="password",
                value=StudentState.confirm_password,
                on_change=StudentState.set_confirm_password,
                width="100%",
            ),
            rx.button(
                "Update password",
                on_click=StudentState.change_password,
                width="100%",
            ),
            rx.cond(
                StudentState.password_status != "",
                rx.callout(
                    StudentState.password_status,
                    icon="key-round",
                    size="1",
                    width="100%",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def _create_item_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    StudentState.create_dialog_type == "file",
                    "Create New File",
                    "Create New Folder"
                )
            ),
            rx.dialog.description(
                rx.cond(
                    StudentState.create_dialog_path != "",
                    f"Creating inside: {StudentState.create_dialog_path}/",
                    "Creating inside workspace root (/) "
                ),
                size="2",
                margin_bottom="1rem",
            ),
            rx.vstack(
                rx.text(
                    rx.cond(
                        StudentState.create_dialog_type == "file",
                        "File Name",
                        "Folder Name"
                    ),
                    size="2",
                    weight="medium"
                ),
                rx.input(
                    placeholder=rx.cond(
                        StudentState.create_dialog_type == "file",
                        "e.g. utils.py",
                        "e.g. components"
                    ),
                    value=StudentState.create_dialog_name,
                    on_change=StudentState.set_create_dialog_name,
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=StudentState.close_create_dialog,
                    )
                ),
                rx.button(
                    "Create",
                    on_click=StudentState.submit_create_dialog
                ),
                justify="end",
                spacing="3",
                margin_top="1rem",
            ),
            max_width="400px",
        ),
        open=StudentState.create_dialog_open,
    )


def student_dashboard() -> rx.Component:
    return page_shell(
        "Code Arena · Student",
        status_banner(StudentState.status_msg),
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Assignments", value="assignments"),
                rx.tabs.trigger("Settings", value="settings"),
            ),
            rx.tabs.content(
                rx.vstack(
                    rx.grid(
                        rx.box(
                            rx.vstack(
                                rx.heading("Unsolved questions", size="5"),
                                rx.cond(
                                    StudentState.has_unsolved,
                                    rx.grid(
                                        rx.foreach(StudentState.unsolved, _unsolved_card),
                                        columns="1",
                                        spacing="3",
                                        width="100%",
                                    ),
                                    rx.text("Nothing to solve right now.", color="var(--gray-10)"),
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            width="100%",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.heading("Solved questions", size="5"),
                                rx.cond(
                                    StudentState.has_solved,
                                    rx.grid(
                                        rx.foreach(StudentState.solved, _solved_card),
                                        columns="1",
                                        spacing="3",
                                        width="100%",
                                    ),
                                    rx.text("You haven't submitted anything yet.", color="var(--gray-10)"),
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            width="100%",
                        ),
                        columns="1 1",
                        spacing="4",
                        width="100%",
                        display_mobile="block",
                        margin_top="1rem",
                    ),
                    width="100%",
                ),
                value="assignments",
            ),
            rx.tabs.content(
                rx.box(
                    _password_settings(),
                    max_width="500px",
                    margin="2rem auto",
                    width="100%",
                ),
                value="settings",
            ),
            default_value="assignments",
            width="100%",
        ),
        _editor_dialog(),
        _solved_dialog(),
        _create_item_dialog(),
    )
