"""MongoDB connection layer for InvestIQ Portfolio.

Single authoritative MongoDB service for the Portfolio module.
Handles connection creation, health checks, and safe error categorization.
"""

from __future__ import annotations

import os
import ssl
import sys
import logging
from typing import Any
from dataclasses import dataclass

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import (
    ServerSelectionTimeoutError,
    ConnectionFailure,
    OperationFailure,
    ConfigurationError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection result type
# ---------------------------------------------------------------------------

@dataclass
class ConnectionResult:
    """Safe connection result that never exposes credentials."""

    ok: bool
    category: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "category": self.category, "message": self.message}


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------

_ENV_VARS = {
    "uri": "MONGODB_URI",
    "database": "MONGODB_DATABASE",
    "users_collection": "MONGODB_USERS_COLLECTION",
    "portfolio_collection": "MONGODB_PORTFOLIO_COLLECTION",
}

_DEFAULTS = {
    "database": "investiq",
    "users_collection": "users",
    "portfolio_collection": "portfolios",
}


def _get_env(var_name: str, default: str | None = None) -> str | None:
    """Load a single environment variable from .env."""
    load_dotenv()
    value = os.getenv(var_name, "").strip()
    return value if value else default


def get_mongodb_uri() -> str | None:
    """Get MongoDB URI from environment."""
    return _get_env(_ENV_VARS["uri"]) or None


def get_database_name() -> str:
    """Get database name from environment."""
    return _get_env(_ENV_VARS["database"], _DEFAULTS["database"]) or _DEFAULTS["database"]


def get_users_collection_name() -> str:
    """Get users collection name from environment."""
    return _get_env(_ENV_VARS["users_collection"], _DEFAULTS["users_collection"]) or _DEFAULTS["users_collection"]


def get_portfolio_collection_name() -> str:
    """Get portfolio collection name from environment."""
    return _get_env(_ENV_VARS["portfolio_collection"], _DEFAULTS["portfolio_collection"]) or _DEFAULTS["portfolio_collection"]


# ---------------------------------------------------------------------------
# MongoClient factory
# ---------------------------------------------------------------------------

def _get_client_kwargs() -> dict[str, Any]:
    """Get MongoClient kwargs with Atlas-compatible TLS configuration."""
    return {
        "serverSelectionTimeoutMS": 10000,
        "connectTimeoutMS": 10000,
        "socketTimeoutMS": 15000,
        "retryWrites": True,
        "w": "majority",
        "tls": True,
        "tlsCAFile": certifi.where(),
    }


def create_client() -> MongoClient | None:
    """Create a new MongoDB client with Atlas-compatible settings."""
    uri = get_mongodb_uri()
    if not uri:
        logger.error("[Portfolio][MongoDB] MONGODB_URI not configured")
        return None

    try:
        kwargs = _get_client_kwargs()
        client = MongoClient(uri, **kwargs)
        logger.info("[Portfolio][MongoDB] Client created successfully")
        return client
    except Exception as exc:
        logger.error("[Portfolio][MongoDB] Failed to create client: %s", type(exc).__name__)
        return None


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def _log_diagnostics() -> None:
    """Log safe diagnostic information (no credentials exposed)."""
    import pymongo

    print("=" * 60)
    print("[Portfolio][MongoDB] CONNECTION TEST")
    print("=" * 60)
    print(f"Python version: {sys.version.split()[0]}")
    print(f"OpenSSL version: {ssl.OPENSSL_VERSION.split()[1]}")
    print(f"PyMongo version: {pymongo.__version__}")
    print(f"certifi version: {certifi.__version__}")
    print(f"URI configured: {'YES' if get_mongodb_uri() else 'NO'}")
    print(f"TLS enabled: YES")
    print(f"CA bundle path: {certifi.where()}")
    print(f"Database configured: {'YES' if get_database_name() else 'NO'}")
    print("Attempting Atlas ping...")
    print("=" * 60)


def check_mongodb_connection() -> ConnectionResult:
    """
    Check MongoDB connection and return a safe categorized result.

    Categories:
        - success: Connection established
        - config: Missing or invalid configuration
        - tls: TLS/SSL handshake failure
        - auth: Authentication failure
        - network: Network/timeout failure
        - unknown: Unclassified failure
    """
    uri = get_mongodb_uri()
    db_name = get_database_name()

    if not uri:
        return ConnectionResult(
            ok=False,
            category="config",
            message="MongoDB configuration is missing. Please set MONGODB_URI in your .env file.",
        )

    _log_diagnostics()

    test_client = None
    try:
        kwargs = _get_client_kwargs()
        test_client = MongoClient(uri, **kwargs)

        test_client.admin.command("ping")
        db = test_client[db_name]
        db.list_collection_names()

        print("[Portfolio][MongoDB] Ping SUCCESS")
        print("[Portfolio][MongoDB] Database connection AVAILABLE")
        return ConnectionResult(
            ok=True,
            category="success",
            message="MongoDB connection successful. Database is accessible.",
        )

    except ConfigurationError as exc:
        print("[Portfolio][MongoDB] Ping FAILED")
        print(f"[Portfolio][MongoDB] Exception: {type(exc).__name__}")
        print("[Portfolio][MongoDB] Category: config")
        return ConnectionResult(
            ok=False,
            category="config",
            message=f"Invalid MongoDB configuration: {type(exc).__name__}. Please check your MONGODB_URI format.",
        )

    except OperationFailure as exc:
        print("[Portfolio][MongoDB] Ping FAILED")
        print(f"[Portfolio][MongoDB] Exception: {type(exc).__name__}")
        if "authentication" in str(exc).lower():
            print("[Portfolio][MongoDB] Category: auth")
            return ConnectionResult(
                ok=False,
                category="auth",
                message="MongoDB authentication failed. Please verify your credentials in MONGODB_URI.",
            )
        print("[Portfolio][MongoDB] Category: unknown")
        return ConnectionResult(
            ok=False,
            category="unknown",
            message=f"MongoDB operation failed: {type(exc).__name__}.",
        )

    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        error_msg = str(exc).lower()
        print("[Portfolio][MongoDB] Ping FAILED")
        print(f"[Portfolio][MongoDB] Exception: {type(exc).__name__}")
        if "ssl" in error_msg or "tls" in error_msg or "handshake" in error_msg:
            print("[Portfolio][MongoDB] Category: tls")
            return ConnectionResult(
                ok=False,
                category="tls",
                message=(
                    "Secure MongoDB connection could not be established.\n\n"
                    "This is often caused by:\n"
                    "1. Antivirus software with SSL scanning enabled\n"
                    "2. Windows Defender network protection\n"
                    "3. Corporate firewall or proxy\n\n"
                    "Please try:\n"
                    "- Temporarily disable antivirus SSL scanning\n"
                    "- Add Python to antivirus exclusions\n"
                    "- Try a different network (mobile hotspot)\n"
                    "- Contact your network administrator"
                ),
            )
        print("[Portfolio][MongoDB] Category: network")
        return ConnectionResult(
            ok=False,
            category="network",
            message="MongoDB connection timed out. Please check your network connection.",
        )

    except Exception as exc:
        print("[Portfolio][MongoDB] Ping FAILED")
        print(f"[Portfolio][MongoDB] Exception: {type(exc).__name__}")
        print("[Portfolio][MongoDB] Category: unknown")
        return ConnectionResult(
            ok=False,
            category="unknown",
            message=f"MongoDB connection failed: {type(exc).__name__}.",
        )

    finally:
        if test_client is not None:
            try:
                test_client.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Database / Collection access
# ---------------------------------------------------------------------------

_client: MongoClient | None = None


def _get_client() -> MongoClient | None:
    """Get or create a cached MongoClient."""
    global _client
    if _client is None:
        _client = create_client()
    return _client


def reset_client() -> None:
    """Reset the cached client (useful after connection failures)."""
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None


def get_database() -> Database | None:
    """Get the MongoDB database instance with connection verification."""
    client = _get_client()
    if client is None:
        return None

    try:
        db_name = get_database_name()
        db = client[db_name]
        client.admin.command("ping")
        _ensure_indexes(client, db)
        logger.info("[Portfolio][MongoDB] Database connection established")
        return db
    except Exception as exc:
        logger.error("[Portfolio][MongoDB] Database connection failed: %s", type(exc).__name__)
        reset_client()
        return None


def get_collection(name: str) -> Collection | None:
    """Get a MongoDB collection by name."""
    db = get_database()
    if db is None:
        return None
    return db[name]


def _ensure_indexes(client: MongoClient, db: Database) -> None:
    """Create necessary indexes for collections (idempotent)."""
    try:
        users: Collection = db[get_users_collection_name()]
        users.create_index("username", unique=True)

        holdings: Collection = db[get_portfolio_collection_name()]
        holdings.create_index("user_id")
        holdings.create_index([("user_id", 1), ("symbol", 1)])
    except Exception as exc:
        logger.warning("[Portfolio][MongoDB] Failed to create indexes: %s", type(exc).__name__)


def is_database_available() -> bool:
    """Check if MongoDB is available without raising exceptions."""
    result = check_mongodb_connection()
    return result.ok


def close_connection() -> None:
    """Close the MongoDB connection (for cleanup)."""
    reset_client()
