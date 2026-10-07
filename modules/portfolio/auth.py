"""Authentication service for InvestIQ Portfolio.

Handles user registration, login, and password management.
"""

from __future__ import annotations

import bcrypt
from datetime import datetime, timezone
from typing import Any

from modules.portfolio.db import check_mongodb_connection, get_collection, get_users_collection_name


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def register_user(username: str, password: str) -> tuple[bool, str]:
    """
    Register a new user in MongoDB.

    Returns:
        tuple[bool, str]: (success, message_or_user_id)
    """
    if not username or not password:
        return False, "Username and password are required."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    # Check database availability first
    conn_result = check_mongodb_connection()
    if not conn_result.ok:
        return False, "Database connection unavailable. Registration cannot be completed."

    users = get_collection(get_users_collection_name())
    if users is None:
        return False, "Unable to access the user database. Please try again later."

    # Check if username already exists
    if users.find_one({"username": username}):
        return False, "Username already exists. Please choose another."

    # Create new user
    hashed = hash_password(password)
    user_doc = {
        "username": username,
        "password_hash": hashed,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = users.insert_one(user_doc)
        return True, str(result.inserted_id)
    except Exception as exc:
        return False, f"Registration failed: {str(exc)}"


def authenticate_user(username: str, password: str) -> tuple[bool, str | None, str]:
    """
    Authenticate a user against MongoDB.

    Returns:
        tuple[bool, str | None, str]: (success, user_id, status)
        - status is one of: "success", "db_unavailable", "invalid_credentials"
    """
    if not username or not password:
        return False, None, "invalid_credentials"

    # Check database availability first
    conn_result = check_mongodb_connection()
    if not conn_result.ok:
        return False, None, "db_unavailable"

    users = get_collection(get_users_collection_name())
    if users is None:
        return False, None, "db_unavailable"

    # Find user by username
    user = users.find_one({"username": username})
    if user is None:
        return False, None, "invalid_credentials"

    # Verify password
    if not verify_password(password, user["password_hash"]):
        return False, None, "invalid_credentials"

    return True, str(user["_id"]), "success"


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    """Get a user by their ID."""
    users = get_collection(get_users_collection_name())
    if users is None:
        return None
    try:
        from bson import ObjectId
        return users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None
