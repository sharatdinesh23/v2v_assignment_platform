from __future__ import annotations

import sys

from code_arena.config import settings
from code_arena.db import create_user


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: python create_user_script.py <email> <password> <name> [role]")
        print("Example: python create_user_script.py admin@example.com secret123 Admin admin")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    password = sys.argv[2]
    name = sys.argv[3]
    role = sys.argv[4] if len(sys.argv) > 4 else "student"

    if not settings.appwrite_configured:
        print("Appwrite is not configured. Check your .env file.")
        sys.exit(1)

    try:
        user = create_user(email=email, password=password, name=name, role=role)
        print("User created successfully")
        print({"id": user.get("$id"), "email": user.get("email"), "role": user.get("role")})
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to create user: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
