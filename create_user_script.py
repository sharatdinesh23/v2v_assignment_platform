from __future__ import annotations

import sys
from code_arena.config import settings
from code_arena.db import get_user_by_email, create_user, _db
from code_arena.security import hash_password


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python create_user_script.py <email> <password> [name] [role]")
        print("Note: If the user already exists, their password and role will be updated.")
        print("Examples:")
        print("  Create/Update student: python create_user_script.py student@example.com pass123")
        print("  Create/Update admin:   python create_user_script.py admin@example.com pass123 \"Admin User\" admin")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    password = sys.argv[2]
    
    # Defaults
    default_name = email.split("@")[0].capitalize()
    name = sys.argv[3] if len(sys.argv) > 3 else default_name
    role = sys.argv[4].strip().lower() if len(sys.argv) > 4 else "student"

    if role not in ["student", "admin"]:
        print(f"Error: Invalid role '{role}'. Allowed roles are 'student' or 'admin'.")
        sys.exit(1)

    if not settings.appwrite_configured:
        print("Appwrite is not configured. Check your .env file.")
        sys.exit(1)

    try:
        existing_user = get_user_by_email(email)
        if existing_user:
            user_id = existing_user["$id"]
            print(f"User with email '{email}' already exists (ID: {user_id}).")
            print("Updating password and details...")
            
            # Update password and role
            update_data = {
                "password_hash": hash_password(password),
                "role": role,
            }
            if len(sys.argv) > 3:
                update_data["name"] = name
                
            _db().update_document(
                settings.database_id,
                settings.users_collection,
                user_id,
                update_data,
            )
            print(f"Successfully updated user '{email}' (Role: {role})")
        else:
            print(f"User '{email}' does not exist. Creating new user...")
            user = create_user(email=email, password=password, name=name, role=role)
            print("Successfully created new user:")
            print({
                "id": user.get("$id"),
                "email": user.get("email"),
                "role": user.get("role"),
                "name": user.get("name"),
            })
            
    except Exception as exc:
        print(f"Failed to create/update user: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
