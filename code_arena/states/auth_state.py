"""Authentication + session state.

Reflex keeps one instance of this state per browser session on the server, so
storing the logged-in user id / role here is safe and never exposed to other
users. Passwords are verified against the bcrypt hash stored in Appwrite.

Role-based access control is enforced by the ``require_admin`` / ``require_student``
``on_load`` guards, which redirect anyone who is not allowed to see a page.
"""
from __future__ import annotations

import reflex as rx

from .. import db
from ..config import settings
from ..logging_config import logger
from ..models import Role
from ..security import hash_password, verify_password


class AuthState(rx.State):
    # Persisted across page reloads for this browser via a cookie-backed var.
    user_id: str = rx.Cookie("", name="ca_uid")
    role: str = rx.Cookie("", name="ca_role")
    user_name: str = rx.Cookie("", name="ca_name")
    user_email: str = rx.Cookie("", name="ca_email")

    # Login form
    login_email: str = ""
    login_password: str = ""
    error: str = ""
    loading: bool = False

    # Password settings
    current_password: str = ""
    new_password: str = ""
    confirm_password: str = ""
    password_status: str = ""
    password_loading: bool = False

    def set_login_email(self, value: str):
        self.login_email = value

    def set_login_password(self, value: str):
        self.login_password = value

    def set_current_password(self, value: str):
        self.current_password = value

    def set_new_password(self, value: str):
        self.new_password = value

    def set_confirm_password(self, value: str):
        self.confirm_password = value

    @rx.var
    def is_authenticated(self) -> bool:
        return bool(self.user_id)

    @rx.var
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    @rx.var
    def is_student(self) -> bool:
        return self.role == Role.STUDENT

    def _seed_if_needed(self) -> None:
        try:
            db.ensure_seed_admin()
        except Exception:
            # If Appwrite is unreachable we still show a helpful login error.
            pass

    def do_login(self):
        self.error = ""
        self.loading = True
        yield
        email = self.login_email.strip().lower()
        if not email or not self.login_password:
            self.error = "Enter both email and password."
            self.loading = False
            logger.warning("Login attempt failed: Email or password field empty.")
            return
        if not settings.appwrite_configured:
            self.error = (
                "Appwrite is not configured. Fill in .env and run "
                "setup_appwrite.py first."
            )
            self.loading = False
            logger.error("Login attempt failed: Appwrite is not configured in settings.")
            return
        self._seed_if_needed()
        try:
            user = db.get_user_by_email(email)
        except Exception as exc:  # noqa: BLE001
            self.error = f"Login failed: {exc}"
            self.loading = False
            logger.error(f"Login failed for {email} due to DB exception: {exc}")
            return

        if not user:
            self.error = "Invalid email or password."
            self.loading = False
            logger.warning(f"Login failed: Email {email} not found in database.")
            return

        stored_hash = user.get("password_hash", "")
        if not verify_password(self.login_password, stored_hash):
            self.error = "Invalid email or password."
            self.loading = False
            logger.warning(f"Login failed: Incorrect password for user {email}.")
            return

        if stored_hash and not stored_hash.startswith("$argon2"):
            try:
                db.update_user_password_hash(
                    user["$id"],
                    hash_password(self.login_password),
                )
                logger.info(f"Migrated user {email} password to Argon2 hash format.")
            except Exception as exc:
                logger.error(f"Failed to migrate password to Argon2 for {email}: {exc}")
                pass

        self.user_id = user["$id"]
        self.role = user.get("role", Role.STUDENT)
        self.user_name = user.get("name", email)
        self.user_email = email
        self.login_password = ""
        self.loading = False
        logger.info(f"User {email} logged in successfully with role: {self.role}.")
        if self.role == Role.ADMIN:
            return rx.redirect("/admin")
        return rx.redirect("/student")

    def change_password(self):
        self.password_status = ""
        if not self.current_password or not self.new_password or not self.confirm_password:
            self.password_status = "Fill in all password fields."
            logger.warning(f"Password update failed for {self.user_email}: empty fields.")
            return
        if self.new_password != self.confirm_password:
            self.password_status = "New passwords do not match."
            logger.warning(f"Password update failed for {self.user_email}: new passwords do not match.")
            return
        if len(self.new_password) < 6:
            self.password_status = "Use at least 6 characters."
            logger.warning(f"Password update failed for {self.user_email}: new password too short.")
            return
        try:
            user = db.get_user_by_email(self.user_email)
        except Exception as exc:  # noqa: BLE001
            self.password_status = f"Password update failed: {exc}"
            logger.error(f"Password update failed for {self.user_email} due to DB exception: {exc}")
            return
        if not user:
            self.password_status = "You are not signed in."
            logger.warning("Password update failed: user not signed in.")
            return
        stored_hash = user.get("password_hash", "")
        if not verify_password(self.current_password, stored_hash):
            self.password_status = "Current password is incorrect."
            logger.warning(f"Password update failed for {self.user_email}: incorrect current password.")
            return
        try:
            db.update_user_password_hash(
                user["$id"],
                hash_password(self.new_password),
            )
        except Exception as exc:  # noqa: BLE001
            self.password_status = f"Password update failed: {exc}"
            logger.error(f"Password update database call failed for {self.user_email}: {exc}")
            return
        self.current_password = ""
        self.new_password = ""
        self.confirm_password = ""
        self.password_status = "Password updated successfully."
        logger.info(f"User {self.user_email} updated their password successfully.")

    def logout(self):
        email = self.user_email
        self.user_id = ""
        self.role = ""
        self.user_name = ""
        self.user_email = ""
        self.login_email = ""
        self.login_password = ""
        self.current_password = ""
        self.new_password = ""
        self.confirm_password = ""
        self.password_status = ""
        logger.info(f"User {email} logged out successfully.")
        return rx.redirect("/")

    # ---- route guards (use as on_load) ---------------------------------
    def require_admin(self):
        if not self.is_authenticated:
            return rx.redirect("/")
        if not self.is_admin:
            return rx.redirect("/student")

    def require_student(self):
        if not self.is_authenticated:
            return rx.redirect("/")
        if not self.is_student:
            return rx.redirect("/admin")

    def redirect_if_authed(self):
        if self.is_authenticated:
            return rx.redirect("/admin" if self.is_admin else "/student")
