"""Student-side state: solved/unsolved lists + a VS Code-like editor."""
from __future__ import annotations

import datetime as _dt

import reflex as rx

from .. import db
from ..config import settings
from ..logging_config import logger
from ..models import SubmissionStatus, STATUS_LABELS
from .auth_state import AuthState


def _fmt_epoch(value) -> str:
    try:
        return _dt.datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OverflowError):
        return "-"


class StudentState(AuthState):
    unsolved: list[dict[str, str]] = []
    solved: list[dict[str, str]] = []
    status_msg: str = ""
    is_busy: bool = False

    @rx.var
    def has_unsolved(self) -> bool:
        return len(self.unsolved) > 0

    @rx.var
    def has_solved(self) -> bool:
        return len(self.solved) > 0

    # --- code editor popup ---------------------------------------------
    show_editor: bool = False
    active_test_id: str = ""
    active_test_name: str = ""
    active_question: str = ""
    active_expected_input: str = ""
    active_expected_output: str = ""

    # In-browser workspace: path -> content. Folders are represented by paths
    # that contain a "/". This never runs code; it only saves.
    editor_files: dict[str, str] = {}
    folders: list[str] = []
    expanded_folders: list[str] = []
    active_file: str = "main.py"
    show_mobile_explorer: bool = False

    new_file_name: str = ""
    new_folder_name: str = ""

    # Dialog state for relative folder creation
    create_dialog_open: bool = False
    create_dialog_path: str = ""
    create_dialog_type: str = "file"  # "file" or "folder"
    create_dialog_name: str = ""

    def toggle_mobile_explorer(self):
        self.show_mobile_explorer = not self.show_mobile_explorer

    def close_mobile_explorer(self):
        self.show_mobile_explorer = False

    def set_new_file_name(self, value: str):
        self.new_file_name = value

    def set_new_folder_name(self, value: str):
        self.new_folder_name = value

    def set_create_dialog_name(self, value: str):
        self.create_dialog_name = value

    # --- view-solved popup ---------------------------------------------
    show_solved: bool = False
    solved_test_name: str = ""
    solved_code: str = ""
    solved_status_label: str = ""
    solved_grade: str = ""
    solved_feedback: str = ""

    # ---------------------------------------------------------------
    def load_dashboard(self):
        guard = self.require_student()
        if guard is not None:
            return guard
        return StudentState.refresh

    def refresh(self):
        if not settings.appwrite_configured:
            self.status_msg = "Appwrite not configured — see .env.example."
            return
        self.is_busy = True
        yield
        try:
            subs = {
                s.get("test_id"): s
                for s in db.list_submissions_for_student(self.user_id)
            }
            unsolved, solved = [], []
            for t in db.list_tests():
                tid = t["$id"]
                sub = subs.get(tid)
                base = {
                    "id": tid,
                    "name": t.get("name", ""),
                    "end_at": _fmt_epoch(t.get("end_at")),
                    "question": t.get("question", ""),
                }
                if sub and sub.get("status") in (
                    SubmissionStatus.SUBMITTED,
                    SubmissionStatus.AI_GRADED,
                    SubmissionStatus.FINAL,
                ):
                    status = sub.get("status", "")
                    # Students only ever see the FINAL grade, never the AI one.
                    grade = (
                        sub.get("final_grade", "")
                        if status == SubmissionStatus.FINAL
                        else ""
                    )
                    solved.append(
                        {
                            **base,
                            "status": status,
                            "status_label": STATUS_LABELS.get(status, status),
                            "grade": grade or "Pending review",
                            "code": sub.get("code", ""),
                            "feedback": (
                                sub.get("ai_feedback", "")
                                if status == SubmissionStatus.FINAL
                                else ""
                            ),
                        }
                    )
                else:
                    unsolved.append(base)
            self.unsolved = unsolved
            self.solved = solved
            self.status_msg = ""
        except (TypeError, ValueError, KeyError, RuntimeError) as exc:  # noqa: BLE001
            self.status_msg = f"Failed to load: {exc}"
        finally:
            self.is_busy = False

    # ---------------------------------------------------------------
    # Code editor
    # ---------------------------------------------------------------
    def open_editor(self, test_id: str):
        match = next((t for t in self.unsolved if t["id"] == test_id), None)
        if not match:
            return
        self.active_test_id = test_id
        self.active_test_name = match["name"]
        self.active_question = match["question"]
        self.editor_files = {"main.py": "# Write your solution here\n"}
        self.folders = []
        self.expanded_folders = []
        self.active_file = "main.py"
        self.new_file_name = ""
        self.new_folder_name = ""
        self.show_editor = True

    def close_editor(self):
        self.show_editor = False

    @rx.var
    def file_list(self) -> list[str]:
        return sorted(self.editor_files.keys())

    @rx.var
    def active_content(self) -> str:
        return self.editor_files.get(self.active_file, "")

    def select_file(self, name: str):
        self.active_file = name

    def edit_content(self, value: str):
        # Reassign the dict so Reflex detects the change.
        files = dict(self.editor_files)
        files[self.active_file] = value
        self.editor_files = files

    @rx.var
    def current_directory(self) -> str:
        if "/" in self.active_file:
            return self.active_file.rsplit("/", 1)[0]
        return ""

    @rx.var
    def file_tree_items(self) -> list[dict]:
        # Collect all folders (both explicit and implicit parent folders)
        all_folders = set(self.folders)
        for path in self.editor_files.keys():
            if "/" in path:
                parts = path.split("/")
                for i in range(1, len(parts)):
                    all_folders.add("/".join(parts[:i]))

        nodes = []
        for f in all_folders:
            nodes.append({
                "name": f.split("/")[-1],
                "path": f,
                "kind": "folder",
                "depth": len(f.split("/")) - 1,
                "is_expanded": f in self.expanded_folders
            })
        for f in self.editor_files.keys():
            nodes.append({
                "name": f.split("/")[-1],
                "path": f,
                "kind": "file",
                "depth": len(f.split("/")) - 1 if "/" in f else 0,
                "is_expanded": False
            })

        # Sort: folders first, then files (hierarchically)
        def hierarchical_key(node):
            parts = node["path"].split("/")
            key_parts = []
            for i, part in enumerate(parts):
                is_last = (i == len(parts) - 1)
                is_folder = (node["kind"] == "folder") if is_last else True
                key_parts.append((0 if is_folder else 1, part))
            return key_parts

        nodes.sort(key=hierarchical_key)

        # Filter visibility
        visible_nodes = []
        for node in nodes:
            path = node["path"]
            parts = path.split("/")
            visible = True
            for i in range(1, len(parts)):
                ancestor = "/".join(parts[:i])
                if ancestor not in self.expanded_folders:
                    visible = False
                    break
            if visible:
                visible_nodes.append(node)

        return visible_nodes

    def toggle_folder(self, folder_path: str):
        if folder_path in self.expanded_folders:
            self.expanded_folders = [f for f in self.expanded_folders if f != folder_path]
        else:
            self.expanded_folders = self.expanded_folders + [folder_path]

    def add_file(self):
        name = self.new_file_name.strip().strip("/")
        if not name:
            return
        parent = self.current_directory
        full_path = f"{parent}/{name}" if parent else name

        files = dict(self.editor_files)
        if full_path not in files:
            files[full_path] = ""
        self.editor_files = files
        self.active_file = full_path
        self.new_file_name = ""

        # Auto expand parent folders
        parts = full_path.split("/")
        for i in range(1, len(parts)):
            ancestor = "/".join(parts[:i])
            if ancestor not in self.expanded_folders:
                self.expanded_folders = self.expanded_folders + [ancestor]

    def select_path(self, path: str):
        if path in self.editor_files:
            self.active_file = path
            self.show_mobile_explorer = False
        else:
            self.toggle_folder(path)

    def add_folder(self):
        name = self.new_folder_name.strip().strip("/")
        if not name:
            return
        parent = self.current_directory
        full_path = f"{parent}/{name}" if parent else name

        if full_path not in self.folders:
            self.folders = self.folders + [full_path]

        # Auto expand parent and new folder
        parts = full_path.split("/")
        for i in range(1, len(parts)):
            ancestor = "/".join(parts[:i])
            if ancestor not in self.expanded_folders:
                self.expanded_folders = self.expanded_folders + [ancestor]
        if full_path not in self.expanded_folders:
            self.expanded_folders = self.expanded_folders + [full_path]

        self.new_folder_name = ""

    def delete_file(self, path: str):
        if path == "main.py":
            return
        files = dict(self.editor_files)
        if path in files:
            del files[path]
        self.editor_files = files
        if self.active_file == path:
            self.active_file = "main.py"

    def delete_folder(self, folder_path: str):
        self.folders = [f for f in self.folders if f != folder_path]
        prefix = folder_path + "/"
        files = dict(self.editor_files)
        to_delete = [p for p in files if p.startswith(prefix)]
        for p in to_delete:
            del files[p]
        self.editor_files = files
        if self.active_file.startswith(prefix):
            self.active_file = "main.py"

    def save_only(self):
        """Save the current working files without submitting for grading."""
        self.status_msg = "Draft saved locally (not submitted)."
        logger.info(f"Student {self.user_email} saved draft for test '{self.active_test_name or self.active_test_id}'.")

    def submit_solution(self):
        if not self.active_test_id:
            return
        try:
            db.upsert_submission(
                test_id=self.active_test_id,
                student_id=self.user_id,
                student_name=self.user_name or self.user_email,
                files=self.editor_files,
                entry_file=self.active_file,
            )
        except (TypeError, ValueError, KeyError, RuntimeError) as exc:  # noqa: BLE001
            self.status_msg = f"Submit failed: {exc}"
            logger.error(f"Student {self.user_email} submission failed for test {self.active_test_id}: {exc}")
            return
        self.show_editor = False
        self.status_msg = (
            "Submitted! It will be AI-graded, then confirmed by an admin."
        )
        logger.info(f"Student {self.user_email} successfully submitted solution for test '{self.active_test_name}'.")
        return StudentState.refresh

    # ---------------------------------------------------------------
    # View solved
    # ---------------------------------------------------------------
    def open_solved(self, test_id: str):
        match = next((t for t in self.solved if t["id"] == test_id), None)
        if not match:
            return
        self.solved_test_name = match["name"]
        self.solved_code = match["code"]
        self.solved_status_label = match["status_label"]
        self.solved_grade = match["grade"]
        self.solved_feedback = match["feedback"]
        self.show_solved = True

    def close_solved(self):
        self.show_solved = False

    def open_create_dialog(self, path: str, item_type: str):
        self.create_dialog_path = path
        self.create_dialog_type = item_type
        self.create_dialog_name = ""
        self.create_dialog_open = True

    def close_create_dialog(self):
        self.create_dialog_open = False

    def submit_create_dialog(self):
        name = self.create_dialog_name.strip().strip("/")
        if not name:
            return

        parent = self.create_dialog_path
        full_path = f"{parent}/{name}" if parent else name

        if self.create_dialog_type == "file":
            files = dict(self.editor_files)
            if full_path not in files:
                files[full_path] = ""
            self.editor_files = files
            self.active_file = full_path
        else:
            if full_path not in self.folders:
                self.folders = self.folders + [full_path]
            if full_path not in self.expanded_folders:
                self.expanded_folders = self.expanded_folders + [full_path]

        # Auto expand parent folders
        parts = full_path.split("/")
        for i in range(1, len(parts)):
            ancestor = "/".join(parts[:i])
            if ancestor not in self.expanded_folders:
                self.expanded_folders = self.expanded_folders + [ancestor]

        self.create_dialog_open = False
        self.create_dialog_name = ""
