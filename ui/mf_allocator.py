from typing import Dict, List, Any
import random

from ui.mf_data import get_funds_by_category


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _normalize(alloc: Dict[str, float]) -> Dict[str, float]:
    total = sum(alloc.values())
    if total <= 0:
        return alloc
    return {k: round((v / total) * 100, 1) for k, v in alloc.items()}


def get_allocation(profile: Dict[str, Any]) -> Dict[str, Any]:
    risk = profile.get("risk_appetite", "Moderate")
    horizon = profile.get("horizon", "3-5 Years")
    goal = profile.get("goal", "Wealth Creation")
    amount = float(profile.get("amount", 10000))
    age = int(profile.get("age") or 35)
    existing = profile.get("existing_investor", "No")

    horizon_years = {
        "<1 Year": 0.5,
        "1-3 Years": 2,
        "3-5 Years": 4,
        "5-10 Years": 7,
        "10+ Years": 12,
    }
    h_years = horizon_years.get(horizon, 4)

    alloc: Dict[str, float] = {}
    rationale: List[str] = []
    insights: List[str] = []

    risk_score = 5
    diversification_score = 5
    portfolio_quality = "Balanced"
    ai_confidence = "High"
    recommended_period = horizon

    if goal == "Emergency Fund":
        alloc = {
            "Liquid Fund": 70.0,
            "Debt Fund": 30.0,
        }
        rationale = [
            "Emergency funds require immediate liquidity.",
            "Low-volatility instruments preserve capital.",
            "No equity exposure reduces downside risk.",
        ]
        insights = [
            "Liquid funds provide instant redemption.",
            "Debt funds add slightly higher returns than savings accounts.",
        ]
        risk_score = 2
        diversification_score = 3

    elif goal == "Tax Saving":
        base_equity = 80 if risk == "High" else 60 if risk == "Moderate" else 40
        alloc = {
            "ELSS": base_equity,
            "Debt Fund": (100 - base_equity) * 0.6,
            "Liquid Fund": (100 - base_equity) * 0.4,
        }
        rationale = [
            "ELSS offers tax benefits under Section 80C.",
            "Debt portion reduces portfolio volatility.",
            "Liquid portion ensures liquidity for short-term needs.",
        ]
        insights = [
            "ELSS has 3-year lock-in but highest EEE returns.",
            "Debt allocation balances equity volatility.",
        ]
        risk_score = 4 if risk == "High" else 3
        diversification_score = 4

    elif goal == "Capital Preservation":
        alloc = {
            "Debt Fund": 50.0,
            "Liquid Fund": 30.0,
            "Large Cap": 15.0,
            "Gold ETF": 5.0,
        }
        rationale = [
            "Capital preservation takes priority over high returns.",
            "Debt and liquid funds provide stability.",
            "Small equity exposure hedges against inflation.",
        ]
        insights = [
            "Debt funds offer predictable income.",
            "Gold ETF provides inflation hedge.",
            "Large cap adds minimal growth without high risk.",
        ]
        risk_score = 2
        diversification_score = 4

    elif goal == "Passive Income":
        alloc = {
            "Debt Fund": 35.0,
            "Hybrid Fund": 25.0,
            "Large Cap": 25.0,
            "Dividend Yield": 15.0,
        }
        rationale = [
            "Debt funds generate regular interest income.",
            "Hybrid funds balance income and growth.",
            "Dividend-paying stocks add passive cash flow.",
        ]
        insights = [
            "Debt funds provide steady monthly income.",
            "Hybrid funds participate in equity upside.",
            "Dividend stocks supplement regular income.",
        ]
        risk_score = 3
        diversification_score = 4

    elif goal == "Retirement":
        equity_base = 90 if h_years >= 10 else 70 if h_years >= 5 else 50
        if risk == "High":
            equity_base = min(equity_base + 10, 95)
        elif risk == "Low":
            equity_base = max(equity_base - 15, 30)
        alloc = {
            "Large Cap": equity_base * 0.4,
            "Flexi Cap": equity_base * 0.35,
            "Mid Cap": equity_base * 0.15,
            "Debt Fund": (100 - equity_base) * 0.7,
            "Gold ETF": (100 - equity_base) * 0.3,
        }
        rationale = [
            "Long retirement horizon allows high equity allocation.",
            "Flexi cap funds adapt to market cycles.",
            "Debt portion increases as retirement approaches.",
        ]
        insights = [
            "Equity builds long-term wealth for retirement corpus.",
            "Gold provides cushion during market stress.",
            "Debt allocation should increase as you near retirement.",
        ]
        risk_score = 6 if risk == "High" else 4
        diversification_score = 5

    elif goal == "Child Education":
        equity_base = 80 if h_years >= 7 else 60 if h_years >= 4 else 40
        if risk == "High":
            equity_base = min(equity_base + 10, 90)
        elif risk == "Low":
            equity_base = max(equity_base - 10, 30)
        alloc = {
            "Large Cap": equity_base * 0.5,
            "Flexi Cap": equity_base * 0.3,
            "Mid Cap": equity_base * 0.2,
            "Debt Fund": (100 - equity_base) * 0.8,
            "Gold ETF": (100 - equity_base) * 0.2,
        }
        rationale = [
            "Education goals need inflation-beating returns.",
            "Balanced equity-debt mix reduces volatility.",
            "Debt increases as the goal date approaches.",
        ]
        insights = [
            "Large cap funds provide stability for goal planning.",
            "Flexi cap funds capture market opportunities.",
            "Debt allocation should increase 2 years before goal.",
        ]
        risk_score = 5 if risk == "High" else 3
        diversification_score = 5

    elif goal == "House Purchase":
        equity_base = 60 if h_years >= 5 else 40 if h_years >= 3 else 20
        if risk == "High":
            equity_base = min(equity_base + 15, 75)
        elif risk == "Low":
            equity_base = max(equity_base - 15, 15)
        alloc = {
            "Large Cap": equity_base * 0.5,
            "Flexi Cap": equity_base * 0.3,
            "Hybrid Fund": equity_base * 0.2,
            "Debt Fund": (100 - equity_base) * 0.7,
            "Liquid Fund": (100 - equity_base) * 0.3,
        }
        rationale = [
            "House purchase requires capital protection.",
            "Moderate equity exposure balances growth and safety.",
            "Debt ensures funds are available when needed.",
        ]
        insights = [
            "Hybrid funds reduce equity volatility.",
            "Debt funds preserve capital for down payment.",
            "Gradually shift to debt as goal nears.",
        ]
        risk_score = 3 if risk == "High" else 2
        diversification_score = 5

    else:
        equity_base = 80 if h_years >= 7 else 60 if h_years >= 4 else 40
        if risk == "High":
            equity_base = min(equity_base + 10, 95)
        elif risk == "Low":
            equity_base = max(equity_base - 15, 25)
        alloc = {
            "Large Cap": equity_base * 0.4,
            "Flexi Cap": equity_base * 0.25,
            "Mid Cap": equity_base * 0.2,
            "Small Cap": equity_base * 0.15 if risk == "High" else 0.0,
            "Debt Fund": (100 - equity_base) * 0.7,
            "Gold ETF": (100 - equity_base) * 0.3,
        }

        if age > 55:
            alloc["Debt Fund"] = alloc.get("Debt Fund", 0) + 10
            alloc["Large Cap"] = max(0, alloc.get("Large Cap", 0) - 5)
            alloc["Mid Cap"] = max(0, alloc.get("Mid Cap", 0) - 5)
            rationale.append("Age-adjusted allocation reduces equity exposure.")
            risk_score = max(2, risk_score - 2)

        rationale = [
            "Wealth creation benefits from long-term equity compounding.",
            "Flexi and multi-cap funds adapt to market regimes.",
            "Debt and gold provide downside protection.",
        ]
        insights = [
            "Equity allocation maximises long-term wealth creation.",
            "Flexi-cap funds help navigate market cycles.",
            "Gold reduces portfolio volatility during crashes.",
        ]
        risk_score = 6 if risk == "High" else 4 if risk == "Moderate" else 2
        diversification_score = 6 if risk == "High" else 5

    alloc = _normalize(alloc)

    recommended_funds: Dict[str, List[Dict]] = {}
    for cat, pct in alloc.items():
        if pct < 5:
            continue
        funds = get_funds_by_category(cat)
        if not funds:
            continue
        picks = random.sample(funds, min(3, len(funds)))
        recommended_funds[cat] = picks

    weights = [alloc.get(cat, 0) / 100.0 for cat in recommended_funds]
    category_cagrs = []
    for cat, funds in recommended_funds.items():
        best = max((f["cagr_5y"] for f in funds), default=12.0)
        category_cagrs.append(best)

    expected_cagr = sum(w * c for w, c in zip(weights, category_cagrs)) if weights else 10.0
    expected_cagr = _clamp(expected_cagr, 4.0, 22.0)

    monthly = amount
    months = int(h_years * 12)
    total_invested = monthly * months
    projected_value = total_invested * ((1 + expected_cagr / 100 / 12) ** months)
    estimated_gain = projected_value - total_invested

    portfolio_quality = (
        "Excellent"
        if expected_cagr >= 14 and risk_score >= 5
        else "Good"
        if expected_cagr >= 10
        else "Conservative"
    )

    if existing == "No":
        rationale.append("New investor profile: starting with SIP builds discipline.")
        insights.append("SIPs reduce timing risk for new investors.")

    return {
        "allocation": alloc,
        "recommended_funds": recommended_funds,
        "expected_cagr": round(expected_cagr, 1),
        "projected_value": round(projected_value, 0),
        "total_invested": round(total_invested, 0),
        "estimated_gain": round(estimated_gain, 0),
        "rationale": rationale,
        "insights": insights,
        "risk_score": risk_score,
        "diversification_score": diversification_score,
        "portfolio_quality": portfolio_quality,
        "ai_confidence": ai_confidence,
        "recommended_period": recommended_period,
    }
