"""Central configuration loaded from environment / .env file.

All secrets (Appwrite URL + API key, OpenRouter key, etc.) live here and are
read from the process environment so nothing sensitive is committed to source.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

try:
    # Load a local .env if present. Safe to call even if the file is missing.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional at runtime
    pass


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    # Appwrite
    appwrite_endpoint: str = _get("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
    appwrite_project_id: str = _get("APPWRITE_PROJECT_ID")
    appwrite_api_key: str = _get("APPWRITE_API_KEY")
    database_id: str = _get("APPWRITE_DATABASE_ID", "code_arena")
    users_collection: str = _get("APPWRITE_USERS_COLLECTION", "users")
    tests_collection: str = _get("APPWRITE_TESTS_COLLECTION", "tests_v2")
    submissions_collection: str = _get("APPWRITE_SUBMISSIONS_COLLECTION", "submissions")
    logs_collection: str = _get("APPWRITE_LOGS_COLLECTION", "logs")

    # Seed admin
    seed_admin_email: str = _get("SEED_ADMIN_EMAIL", "admin@example.com")
    seed_admin_password: str = _get("SEED_ADMIN_PASSWORD", "change_me_now")
    seed_admin_name: str = _get("SEED_ADMIN_NAME", "Administrator")

    # OpenRouter
    openrouter_api_key: str = _get("OPENROUTER_API_KEY")
    openrouter_model: str = _get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    openrouter_base_url: str = _get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    # Misc
    app_secret: str = _get("APP_SECRET", "please-change-this-secret")

    @property
    def appwrite_configured(self) -> bool:
        return bool(self.appwrite_project_id and self.appwrite_api_key)

    @property
    def openrouter_configured(self) -> bool:
        return bool(self.openrouter_api_key)


settings = Settings()
