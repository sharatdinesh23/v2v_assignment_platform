"""Admin dashboard: tests, students, submission review, Excel export."""
from __future__ import annotations

import reflex as rx

from ..states.admin_state import AdminState
from .components import page_shell, status_banner, MonacoEditor


def _review_file_tree_item(item: dict) -> rx.Component:
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

    return rx.hstack(
        chevron,
        item_icon,
        rx.text(item["name"], size="2", overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
        padding_left=indent,
        padding_y="0.25rem",
        padding_right="0.5rem",
        border_radius="0.25rem",
        background=rx.cond(
            AdminState.review_active_file == item["path"],
            "var(--accent-3)",
            "transparent",
        ),
        color=rx.cond(
            AdminState.review_active_file == item["path"],
            "var(--accent-11)",
            "var(--gray-12)",
        ),
        _hover={"background": "var(--gray-3)"},
        align="center",
        spacing="2",
        cursor="pointer",
        on_click=lambda: AdminState.select_review_path(item["path"]),
        width="100%",
    )


def _breadcrumbs(test_name: rx.Var[str] | str = "", student_name: rx.Var[str] | str = "") -> rx.Component:
    return rx.hstack(
        rx.text(
            "Assignments",
            cursor="pointer",
            on_click=AdminState.clear_selected_test,
            color="var(--accent-9)",
            _hover={"text_decoration": "underline"}
        ),
        # Reactively show test name if test_name is not empty
        rx.cond(
            test_name != "",
            rx.hstack(
                rx.text("/", color="var(--gray-9)"),
                rx.text(
                    test_name,
                    cursor="pointer",
                    on_click=AdminState.clear_selected_sub,
                    color=rx.cond(student_name != "", "var(--accent-9)", "var(--gray-12)"),
                    _hover=rx.cond(student_name != "", {"text_decoration": "underline"}, {}),
                ),
                align="center",
                spacing="2",
            ),
            rx.box()
        ),
        # Reactively show student name if student_name is not empty
        rx.cond(
            student_name != "",
            rx.hstack(
                rx.text("/", color="var(--gray-9)"),
                rx.text(f"{student_name}'s Submission", color="var(--gray-12)"),
                align="center",
                spacing="2",
            ),
            rx.box()
        ),
        spacing="2",
        align="center",
        margin_bottom="1rem",
    )


def _admin_editor_view() -> rx.Component:
    explorer_pane = rx.vstack(
        rx.hstack(
            rx.text("EXPLORER", size="1", weight="bold", color="var(--gray-9)"),
            rx.spacer(),
            spacing="2",
            width="100%",
            padding_bottom="0.5rem",
        ),
        # File Tree scrollable area
        rx.scroll_area(
            rx.vstack(
                rx.foreach(AdminState.review_file_tree_items, _review_file_tree_item),
                spacing="1",
                width="100%",
            ),
            height="360px",
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
                            rx.button("Close", size="1", variant="soft", on_click=AdminState.close_review_mobile_explorer)
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
        open=AdminState.review_show_mobile_explorer,
    )

    return rx.vstack(
        _breadcrumbs(AdminState.review_test, AdminState.review_student),

        # Grading workspace
        rx.grid(
            # Editor Sidebar (Desktop Explorer)
            rx.box(
                rx.hstack(
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
                display=["none", "none", "block"],
                grid_column="span 3",
                border="1px solid var(--gray-4)",
                border_radius="0.5rem",
                overflow="hidden",
            ),
            # Editor Pane
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
                            on_click=AdminState.toggle_review_mobile_explorer,
                            display=["block", "block", "none"],
                        ),
                        # Active tab name
                        rx.hstack(
                            rx.icon("file-code", size=14, color="var(--accent-9)"),
                            rx.text(AdminState.review_active_file, size="2", weight="medium"),
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
                    # Monaco editor (read-only)
                    MonacoEditor.create(
                        value=AdminState.review_active_content,
                        options={"readOnly": True, "minimap": {"enabled": False}},
                        height="400px",
                    ),
                    # Bottom info bar
                    rx.hstack(
                        rx.text("Language: Python (Read Only)", size="1", color="var(--gray-10)"),
                        rx.spacer(),
                        rx.text(f"File: {AdminState.review_active_file}", size="1", color="var(--gray-10)"),
                        width="100%",
                        padding="0.25rem 0.5rem",
                        background="var(--gray-3)",
                    ),
                    width="100%",
                    spacing="0",
                ),
                grid_column=["span 12", "span 12", "span 6"],
                border="1px solid var(--gray-4)",
                border_radius="0.5rem",
                overflow="hidden",
            ),
            # Review / Grading Side Panel
            rx.box(
                rx.vstack(
                    rx.heading("Grading & Review", size="4"),
                    rx.divider(),
                    rx.vstack(
                        rx.text("AI Provisioned Feedback", size="2", weight="bold"),
                        rx.cond(
                            AdminState.review_ai_feedback != "",
                            rx.callout(
                                AdminState.review_ai_feedback,
                                icon="bot",
                                size="1",
                                width="100%",
                            ),
                            rx.text("Awaiting AI grading run.", color="var(--gray-10)", size="2"),
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.text("AI Grade:", size="2"),
                        rx.badge(
                            rx.cond(AdminState.review_ai_grade != "", AdminState.review_ai_grade, "N/A"),
                            color_scheme="amber"
                        ),
                        spacing="2",
                    ),
                    rx.vstack(
                        rx.text("Final Grade", size="2", weight="bold"),
                        rx.input(
                            value=AdminState.review_final_grade,
                            on_change=AdminState.set_review_final_grade,
                            placeholder="e.g. 85",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.divider(),
                    rx.hstack(
                        rx.button(
                            "Redo (send to AI)",
                            color_scheme="orange",
                            variant="soft",
                            on_click=AdminState.redo_grade,
                            width="100%",
                        ),
                        
                        spacing="2",
                        width="100%",
                    ),
                    rx.button(
                            "Accept & Save",
                            color_scheme="green",
                            on_click=AdminState.accept_grade,
                            width="100%",
                        ),
                    rx.button(
                        "Back to submissions",
                        variant="soft",
                        color_scheme="gray",
                        on_click=AdminState.clear_selected_sub,
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                padding="1rem",
                border="1px solid var(--gray-4)",
                border_radius="0.5rem",
                background="var(--gray-2)",
                grid_column=["span 12", "span 12", "span 3"],
            ),
            columns="12",
            spacing="3",
            width="100%",
        ),
        mobile_explorer_drawer,
        width="100%",
    )


def _sub_row(s: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(s["student"]),
        rx.table.cell(rx.badge(s["status_label"])),
        rx.table.cell(rx.cond(s["ai_grade"] != "", s["ai_grade"], "Awaiting")),
        rx.table.cell(rx.cond(s["final_grade"] != "", s["final_grade"], "Pending review")),
        rx.table.cell(
            rx.button(
                "Review",
                size="1",
                variant="soft",
                on_click=lambda: AdminState.select_sub(s["id"]),
            )
        ),
    )


def _admin_submissions_list_view() -> rx.Component:
    return rx.vstack(
        _breadcrumbs(AdminState.selected_test_name),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading(f"Submissions for {AdminState.selected_test_name}", size="4"),
                    rx.spacer(),
                    rx.button(
                        "Back to Assignments",
                        variant="soft",
                        color_scheme="gray",
                        on_click=AdminState.clear_selected_test,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    AdminState.has_filtered_submissions,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Student"),
                                rx.table.column_header_cell("Status"),
                                rx.table.column_header_cell("AI Grade"),
                                rx.table.column_header_cell("Final Grade"),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(rx.foreach(AdminState.filtered_submissions, _sub_row)),
                        width="100%",
                    ),
                    rx.text("No submissions yet for this test.", color="var(--gray-10)", size="2"),
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        width="100%",
    )


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------
def _create_test_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Create a new test"),
            rx.dialog.description(
                "Students will see this as an unsolved question.",
                size="2",
                margin_bottom="1rem",
            ),
            rx.vstack(
                rx.text("Name of the test", size="2", weight="medium"),
                rx.input(
                    placeholder="e.g. Two Sum",
                    value=AdminState.t_name,
                    on_change=AdminState.set_t_name,
                    width="100%",
                ),
                rx.text("End date & time", size="2", weight="medium"),
                rx.input(
                    type="datetime-local",
                    value=AdminState.t_end,
                    on_change=AdminState.set_t_end,
                    width="100%",
                ),
                rx.text("Question", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Describe the problem…",
                    value=AdminState.t_question,
                    on_change=AdminState.set_t_question,
                    width="100%",
                    rows="4",
                ),
                rx.text("Expected input", size="2", weight="medium"),
                rx.text_area(
                    placeholder="e.g. [2,7,11,15], target = 9",
                    value=AdminState.t_expected_input,
                    on_change=AdminState.set_t_expected_input,
                    width="100%",
                    rows="2",
                ),
                rx.text("Expected output", size="2", weight="medium"),
                rx.text_area(
                    placeholder="e.g. [0,1]",
                    value=AdminState.t_expected_output,
                    on_change=AdminState.set_t_expected_output,
                    width="100%",
                    rows="2",
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
                        on_click=AdminState.close_test_dialog,
                    )
                ),
                rx.button("Create test", on_click=AdminState.submit_test),
                justify="end",
                spacing="3",
                margin_top="1rem",
            ),
            max_width="520px",
        ),
        open=AdminState.show_test_dialog,
    )


def _add_student_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Add a student"),
            rx.dialog.description(
                "A login is created where the password equals the email.",
                size="2",
                margin_bottom="1rem",
            ),
            rx.vstack(
                rx.text("Email address", size="2", weight="medium"),
                rx.input(
                    placeholder="student@example.com",
                    value=AdminState.s_email,
                    on_change=AdminState.set_s_email,
                    width="100%",
                ),
                rx.text("Full name (optional)", size="2", weight="medium"),
                rx.input(
                    placeholder="Jane Doe",
                    value=AdminState.s_name,
                    on_change=AdminState.set_s_name,
                    width="100%",
                ),
                rx.text("Mode", size="2", weight="medium"),
                rx.select(
                    ["online", "offline"],
                    value=AdminState.s_mode,
                    on_change=AdminState.set_s_mode,
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
                        on_click=AdminState.close_student_dialog,
                    )
                ),
                rx.button("Add student", on_click=AdminState.submit_student),
                justify="end",
                spacing="3",
                margin_top="1rem",
            ),
            max_width="440px",
        ),
        open=AdminState.show_student_dialog,
    )
def _add_bulk_student_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Bulk Student Upload"),
            rx.dialog.description(
                "Upload an Excel file (.xlsx or .xls) containing at least Name and Email columns.",
                size="2",
                margin_bottom="1rem",
            ),
            rx.vstack(
                rx.upload(
                    rx.vstack(
                        rx.icon("upload", size=24, color="var(--accent-9)"),
                        rx.text("Drag and drop file here, or click to browse", size="2"),
                        rx.text("Only .xlsx and .xls formats are supported.", size="1", color="var(--gray-10)"),
                        align="center",
                        spacing="2",
                    ),
                    id="excel_uploader",
                    border="1px dashed var(--gray-6)",
                    padding="2rem",
                    border_radius="0.5rem",
                    width="100%",
                    accept={
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
                        "application/vnd.ms-excel": [".xls"]
                    },
                    max_files=1,
                ),
                rx.hstack(
                    rx.foreach(
                        rx.selected_files("excel_uploader"),
                        rx.text
                    ),
                    spacing="2",
                ),
                spacing="3",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=AdminState.close_bulk_student_dialog,
                    )
                ),
                rx.button(
                    "Upload & Process",
                    on_click=AdminState.handle_excel_upload(
                        rx.upload_files(upload_id="excel_uploader")
                    ),
                ),
                justify="end",
                spacing="3",
                margin_top="1rem",
            ),
            max_width="480px",
        ),
        open=AdminState.show_bulk_student_dialog,
    )

# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------
def _assignment_row(t: dict) -> rx.Component:
    sub_count = AdminState.test_submission_counts.get(t["id"], 0)
    pending_count = AdminState.test_pending_counts.get(t["id"], 0)

    return rx.table.row(
        rx.table.cell(t["name"]),
        rx.table.cell(t["end_at"]),
        rx.table.cell(f"{sub_count} submissions ({pending_count} pending)"),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    "View Submissions",
                    size="1",
                    variant="soft",
                    on_click=lambda: AdminState.select_test(t["id"]),
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    "Delete",
                    size="1",
                    variant="soft",
                    color_scheme="red",
                    on_click=lambda: AdminState.delete_test(t["id"]),
                ),
                spacing="2",
            )
        ),
    )


def _tests_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Test Creation", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    "New test",
                    on_click=AdminState.open_test_dialog,
                    size="2",
                ),
                width="100%",
                align="center",
            ),
            rx.text(
                "Use the 'New test' button to create dynamic programming assignments for students.",
                color="var(--gray-11)",
                size="2",
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def _student_row(s: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(s["name"]),
        rx.table.cell(s["email"]),
        rx.table.cell(s.get("mode", "")),
        rx.table.cell(
            rx.button(
                rx.icon("user-minus", size=14),
                "Remove",
                size="1",
                variant="soft",
                color_scheme="red",
                on_click=lambda: AdminState.remove_student(s["id"]),
            )
        ),
    )


def _students_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Students", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("user-plus",size=16),
                    "Bulk student upload",
                    on_click=AdminState.open_bulk_student_dialog,
                    size="2",
                ),
                rx.button(
                    rx.icon("user-plus", size=16),
                    "Add student",
                    on_click=AdminState.open_student_dialog,
                    size="2",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                AdminState.has_students,
                rx.vstack(
                    rx.grid(
                        rx.input(
                            placeholder="Filter by name...",
                            value=AdminState.filter_student_name,
                            on_change=AdminState.set_filter_student_name,
                            size="1",
                            width="100%",
                        ),
                        rx.input(
                            placeholder="Filter by email...",
                            value=AdminState.filter_student_email,
                            on_change=AdminState.set_filter_student_email,
                            size="1",
                            width="100%",
                        ),
                        rx.select(
                            ["all", "online", "offline"],
                            placeholder="Filter by mode...",
                            value=AdminState.filter_student_mode,
                            on_change=AdminState.set_filter_student_mode,
                            size="1",
                            width="100%",
                        ),
                        columns="1 3",
                        spacing="2",
                        width="100%",
                        margin_bottom="0.5rem",
                    ),
                    rx.cond(
                        AdminState.has_filtered_students,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Name"),
                                    rx.table.column_header_cell("Email"),
                                    rx.table.column_header_cell("Mode"),
                                    rx.table.column_header_cell(""),
                                )
                            ),
                            rx.table.body(rx.foreach(AdminState.filtered_students, _student_row)),
                            width="100%",
                        ),
                        rx.text("No students match the current filters.", color="var(--gray-10)", size="2"),
                    ),
                    width="100%",
                ),
                rx.text("No students yet.", color="var(--gray-10)", size="2"),
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def _submissions_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Assignments & Grading", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("bot", size=16),
                    "Run AI grading",
                    on_click=AdminState.run_ai_grading,
                    size="2",
                    variant="soft",
                    color_scheme="amber",
                    loading=AdminState.is_busy,
                ),
                rx.button(
                    rx.icon("download", size=16),
                    "Export results (.xlsx)",
                    size="2",
                    on_click=AdminState.export_results,
                ),
                width="100%",
                align="center",
                spacing="3",
            ),
            rx.cond(
                AdminState.has_tests,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Assignment"),
                            rx.table.column_header_cell("Ends"),
                            rx.table.column_header_cell("Submissions"),
                            rx.table.column_header_cell(""),
                        )
                    ),
                    rx.table.body(rx.foreach(AdminState.tests, _assignment_row)),
                    width="100%",
                ),
                rx.text("No assignments created yet.", color="var(--gray-10)", size="2"),
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def admin_dashboard() -> rx.Component:
    return page_shell(
        "Code Arena · Admin",
        status_banner(AdminState.status_msg),
        rx.cond(
            AdminState.selected_sub_id != "",
            # Level 3: IDE review workspace
            _admin_editor_view(),
            rx.cond(
                AdminState.selected_test_id != "",
                # Level 2: Student submissions list for active test
                _admin_submissions_list_view(),
                # Level 1: Normal dashboard (Students, Tests, Assignments list)
                rx.vstack(
                    _tests_section(),
                    rx.accordion.root(
                        rx.accordion.item(
                            rx.accordion.header(
                                rx.accordion.trigger(
                                    rx.hstack(
                                        rx.icon("users", size=18),
                                        rx.heading("Students", size="3"),
                                        align="center",
                                        spacing="2",
                                    )
                                )
                            ),
                            rx.accordion.content(
                                rx.box(_students_section(), padding_top="0.5rem")
                            ),
                            value="students",
                        ),
                        rx.accordion.item(
                            rx.accordion.header(
                                rx.accordion.trigger(
                                    rx.hstack(
                                        rx.icon("clipboard-list", size=18),
                                        rx.heading("Assignments & Grading", size="3"),
                                        align="center",
                                        spacing="2",
                                    )
                                )
                            ),
                            rx.accordion.content(
                                rx.box(_submissions_section(), padding_top="0.5rem")
                            ),
                            value="assignments",
                        ),
                        type="multiple",
                        default_value=["students", "assignments"],
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
            ),
        ),
        _create_test_dialog(),
        _add_student_dialog(),
        _add_bulk_student_dialog(),
    )
