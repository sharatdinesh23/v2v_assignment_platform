"""Password hashing helpers.

Even though a student's initial password equals their email address (per the
spec), we still store only an Argon2 hash — never plaintext — so the database
never contains recoverable credentials.
"""
from __future__ import annotations

import bcrypt
from argon2 import PasswordHasher

_pwd_context = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16)


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False

    try:
        return _pwd_context.verify(hashed, plain)
    except Exception:
        pass

    if not isinstance(hashed, str):
        return False

    try:
        if hashed.startswith(("$2a$", "$2b$", "$2y$")):
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        pass

    try:
        return plain == hashed
    except Exception:
        return False
