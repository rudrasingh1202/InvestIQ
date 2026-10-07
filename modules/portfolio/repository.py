"""Portfolio repository for InvestIQ.

Handles CRUD operations for portfolio holdings.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from modules.portfolio.db import get_collection, get_portfolio_collection_name


def add_holding(
    user_id: str,
    symbol: str,
    stock_name: str,
    buy_price: float,
    quantity: int,
    buy_date: str,
) -> tuple[bool, str]:
    """
    Add a new holding to the user's portfolio.

    Returns:
        tuple[bool, str]: (success, message)
    """
    if not symbol or not stock_name:
        return False, "Stock symbol and name are required."
    if buy_price <= 0:
        return False, "Buy price must be greater than zero."
    if quantity <= 0:
        return False, "Quantity must be greater than zero."
    if not buy_date:
        return False, "Buy date is required."

    holdings = get_collection(get_portfolio_collection_name())
    if holdings is None:
        return False, "Unable to access the database. Please try again later."

    doc = {
        "user_id": user_id,
        "symbol": symbol.strip().upper(),
        "stock_name": stock_name.strip(),
        "buy_price": float(buy_price),
        "quantity": int(quantity),
        "buy_date": buy_date,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    try:
        holdings.insert_one(doc)
        return True, "Holding added successfully."
    except Exception as exc:
        return False, f"Failed to add holding: {str(exc)}"


def get_holdings(user_id: str) -> list[dict[str, Any]]:
    """
    Get all holdings for a user.

    Returns:
        list[dict]: List of holding documents with string _id
    """
    holdings = get_collection(get_portfolio_collection_name())
    if holdings is None:
        return []

    try:
        cursor = holdings.find({"user_id": user_id}).sort("created_at", -1)
        result = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            result.append(doc)
        return result
    except Exception:
        return []


def delete_holding(holding_id: str, user_id: str) -> tuple[bool, str]:
    """
    Delete a holding from the user's portfolio.

    Returns:
        tuple[bool, str]: (success, message)
    """
    holdings = get_collection(get_portfolio_collection_name())
    if holdings is None:
        return False, "Unable to access the database. Please try again later."

    try:
        from bson import ObjectId
        result = holdings.delete_one({"_id": ObjectId(holding_id), "user_id": user_id})
        if result.deleted_count == 1:
            return True, "Holding deleted."
        return False, "Holding not found."
    except Exception as exc:
        return False, f"Failed to delete holding: {str(exc)}"


def update_holding(
    holding_id: str,
    user_id: str,
    symbol: str,
    stock_name: str,
    buy_price: float,
    quantity: int,
    buy_date: str,
) -> tuple[bool, str]:
    """
    Update an existing holding.

    Returns:
        tuple[bool, str]: (success, message)
    """
    if not symbol or not stock_name:
        return False, "Stock symbol and name are required."
    if buy_price <= 0:
        return False, "Buy price must be greater than zero."
    if quantity <= 0:
        return False, "Quantity must be greater than zero."
    if not buy_date:
        return False, "Buy date is required."

    holdings = get_collection(get_portfolio_collection_name())
    if holdings is None:
        return False, "Unable to access the database. Please try again later."

    try:
        from bson import ObjectId
        result = holdings.update_one(
            {"_id": ObjectId(holding_id), "user_id": user_id},
            {
                "$set": {
                    "symbol": symbol.strip().upper(),
                    "stock_name": stock_name.strip(),
                    "buy_price": float(buy_price),
                    "quantity": int(quantity),
                    "buy_date": buy_date,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.modified_count == 1:
            return True, "Holding updated successfully."
        return False, "Holding not found."
    except Exception as exc:
        return False, f"Failed to update holding: {str(exc)}"
