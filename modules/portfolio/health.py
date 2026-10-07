"""Portfolio health scoring module for InvestIQ.

Calculates a health score (0-100) based on portfolio-level signals:
- Diversification
- Concentration risk
- Current P&L
- Position concentration
- Performance distribution
"""

from __future__ import annotations

from typing import Any


def calculate_portfolio_health(
    holdings: list[dict[str, Any]],
    current_prices: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Calculate portfolio health score (0-100).

    Scoring methodology:
        - Base score: 50
        - Diversification: +5 to +15 (based on number of holdings)
        - Concentration: +0 to +10 (based on max single-stock weight)
        - Top-5 balance: +0 to +5 (based on top-5 concentration)
        - Performance: +0 to +10 (based on overall P&L %)
        - Win ratio: +0 to +5 (based on profitable positions)

    Classification:
        - 80-100: HEALTHY (GREEN)
        - 60-79: MODERATE (YELLOW)
        - 0-59: HIGH RISK (RED)

    Args:
        holdings: List of holding documents
        current_prices: Optional dict mapping symbol to current price

    Returns:
        dict: Health score result with score, risk_level, risk_color,
              strengths, improvements, and portfolio metrics
    """
    if not holdings:
        return {
            "score": 0,
            "risk_level": "No Data",
            "risk_color": "gray",
            "strengths": [],
            "improvements": ["Add holdings to enable health scoring."],
        }

    # Calculate portfolio metrics
    total_invested = sum(h.get("buy_price", 0) * h.get("quantity", 0) for h in holdings)
    total_current = 0.0
    for h in holdings:
        symbol = h.get("symbol", "")
        cp = current_prices.get(symbol) if current_prices else None
        if cp is None:
            cp = h.get("current_price", 0)
        total_current += cp * h.get("quantity", 0)

    pnl = total_current - total_invested
    pnl_pct = (pnl / total_invested * 100) if total_invested > 0 else 0.0

    num_holdings = len(holdings)

    # Calculate position weights
    current_values = []
    for h in holdings:
        symbol = h.get("symbol", "")
        cp = current_prices.get(symbol) if current_prices else None
        if cp is None:
            cp = h.get("current_price", 0)
        current_values.append(cp * h.get("quantity", 0))

    total_value = sum(current_values)
    weights = [v / total_value for v in current_values] if total_value > 0 else []

    max_weight = max(weights) if weights else 0.0
    top5_weight = sum(sorted(weights, reverse=True)[:5]) if len(weights) >= 5 else sum(weights)

    # Calculate health score
    score = 50
    strengths = []
    improvements = []

    # Diversification scoring
    if num_holdings >= 10:
        score += 15
        strengths.append("Excellent diversification (10+ holdings)")
    elif num_holdings >= 5:
        score += 10
        strengths.append("Good diversification (5+ holdings)")
    elif num_holdings >= 3:
        score += 5
        strengths.append("Moderate diversification")
    else:
        improvements.append("Add more holdings to reduce concentration risk")

    # Concentration scoring
    if max_weight <= 0.20:
        score += 10
        strengths.append("No single stock dominates the portfolio")
    elif max_weight <= 0.35:
        score += 5
    else:
        improvements.append("Reduce single-stock concentration (max weight > 35%)")

    # Top-5 balance scoring
    if top5_weight <= 0.70:
        score += 5
        strengths.append("Top holdings are well balanced")
    else:
        improvements.append("Top 5 holdings represent over 70% of portfolio")

    # Performance scoring
    if pnl_pct >= 20:
        score += 10
        strengths.append(f"Strong overall performance (+{pnl_pct:.1f}%)")
    elif pnl_pct >= 5:
        score += 5
        strengths.append(f"Positive portfolio returns (+{pnl_pct:.1f}%)")
    elif pnl_pct >= 0:
        score += 2
    else:
        if pnl_pct >= -10:
            improvements.append("Portfolio is slightly negative; review underperformers")
        else:
            improvements.append("Significant portfolio drawdown detected")

    # Win ratio scoring
    positive_count = 0
    for h in holdings:
        symbol = h.get("symbol", "")
        cp = current_prices.get(symbol) if current_prices else None
        if cp is None:
            cp = h.get("current_price", 0)
        if cp > h.get("buy_price", 0):
            positive_count += 1

    win_ratio = positive_count / num_holdings if num_holdings > 0 else 0.0
    if win_ratio >= 0.7:
        score += 5
        strengths.append("High win ratio across holdings")
    elif win_ratio >= 0.5:
        score += 2

    # Clamp score to 0-100
    score = max(0, min(100, score))

    # Classification
    if score >= 75:
        risk_level = "Healthy"
        risk_color = "green"
    elif score >= 50:
        risk_level = "Moderate"
        risk_color = "yellow"
    else:
        risk_level = "High Risk"
        risk_color = "red"

    return {
        "score": score,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "strengths": strengths[:4],
        "improvements": improvements[:4],
        "total_invested": total_invested,
        "total_current": total_current,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "num_holdings": num_holdings,
        "max_weight": max_weight,
    }
