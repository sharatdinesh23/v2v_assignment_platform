from __future__ import annotations

import getpass
import sys
from code_arena.config import settings
from code_arena.db import get_user_by_email, create_user, _db
from code_arena.security import hash_password


def print_menu() -> None:
    print("\n" + "=" * 45)
    print("      CODE ARENA - USER MANAGEMENT MENU      ")
    print("=" * 45)
    print("1. Create or Update Student")
    print("2. Create or Update Admin")
    print("3. Exit")
    print("=" * 45)


def main() -> None:
    if not settings.appwrite_configured:
        print("Appwrite is not configured. Check your .env file.")
        sys.exit(1)

    while True:
        print_menu()
        choice = input("Select an option (1-3): ").strip()

        if choice == "3":
            print("\nExiting. Goodbye!")
            sys.exit(0)

        if choice not in ["1", "2"]:
            print("\nInvalid selection. Please choose 1, 2, or 3.")
            continue

        role = "student" if choice == "1" else "admin"
        print(f"\n--- [Option Selected: Create/Update {role.capitalize()}] ---")
        
        email = input("Enter email address: ").strip().lower()
        if not email:
            print("Error: Email cannot be empty.")
            continue

        # Use getpass to securely input the password
        try:
            password = getpass.getpass("Enter password: ")
        except Exception:
            password = input("Enter password: ")
            
        if not password:
            print("Error: Password cannot be empty.")
            continue

        name = input("Enter name (optional, press Enter to default): ").strip()
        if not name:
            name = email.split("@")[0].capitalize()

        try:
            existing_user = get_user_by_email(email)
            if existing_user:
                user_id = existing_user["$id"]
                print(f"\nUser '{email}' already exists (ID: {user_id}).")
                confirm = input("Do you want to update this user's password and role? (y/n): ").strip().lower()
                if confirm != "y":
                    print("Update cancelled.")
                    continue
                
                print("Updating password and details...")
                update_data = {
                    "password_hash": hash_password(password),
                    "role": role,
                    "name": name,
                }
                _db().update_document(
                    settings.database_id,
                    settings.users_collection,
                    user_id,
                    update_data,
                )
                print(f"Successfully updated user '{email}' as {role.capitalize()}!")
            else:
                print(f"\nCreating new user '{email}'...")
                user = create_user(email=email, password=password, name=name, role=role)
                print(f"Successfully created new {role.capitalize()}:")
                print({
                    "id": user.get("$id"),
                    "email": user.get("email"),
                    "role": user.get("role"),
                    "name": user.get("name"),
                })
        except Exception as exc:
            print(f"\nError: {exc}")


if __name__ == "__main__":
    main()
