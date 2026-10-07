"""Listing gain prediction.

Provides an estimate for potential listing gain percentage.

Logic is intentionally placeholder.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any



@dataclass(frozen=True)
class ListingGainEstimate:
    """Estimated listing gain."""

    gain_percent: float
    confidence: float
    drivers: list[str]


def get_grey_market_premium(company_name: str) -> float | None:
    """Scrape/lookup grey market premium for a company.

    Expected later implementation:
    - Query investorgain.com (or another reliable source)
    - Extract numeric GMP percentage
    - Return None if unavailable

    Args:
        company_name: Company name.

    Returns:
        GMP in percentage points, or None.
    """

    raise NotImplementedError


def compute_valuation_score(pe_ratio: float | None, sector_avg_pe: float | None) -> str:
    """Compute valuation score (Overvalued/Fair/Undervalued) by P/E.

    Expected later implementation:
    - Overvalued: pe_ratio > sector_avg_pe * 1.15
    - Fair: pe_ratio within +/- 15%
    - Undervalued: pe_ratio < sector_avg_pe * 0.85

    Args:
        pe_ratio: Company P/E.
        sector_avg_pe: Sector average P/E.

    Returns:
        One of ('Overvalued','Fair','Undervalued')
    """

    raise NotImplementedError


def estimate_listing_gain(
    *,
    financial_score: float | None,
    risk_score: float | None,
    gmp: float | None,
    subscription_times: float | None = None,
) -> dict[str, Any]:
    """Estimate conservative/base/bull listing gain percentages.

    Formula (base case):
        base_case = (financial_score/100 * 30) - (risk_score/100 * 15) + gmp_factor

    Where gmp_factor is a scaled representation of GMP (expected to be gmp itself
    in percentage points by default).

    Args:
        financial_score: 0-100.
        risk_score: 0-100.
        gmp: GMP percentage points (if available).
        subscription_times: Optional subscription times (later to refine bands).

    Returns:
        dict with keys:
          - conservative_gain (float)
          - base_case_gain (float)
          - bull_case_gain (float)
          - confidence ('High'|'Medium'|'Low')
    """

    raise NotImplementedError


def apply_or_avoid(
    listing_gain_dict: dict[str, Any],
    risk_score: float | None,
    financial_score: float | None,
) -> dict[str, Any]:
    """Apply decision logic to APPLY / AVOID.

    Returns:
        dict with keys:
          - verdict: 'APPLY' / 'AVOID' / 'APPLY WITH CAUTION'
          - reasons: list[str] (3-5 bullet reasons)
          - target_price: float (expected: issue_price * (1 + base_case/100))

    Expected later implementation:
    - Use risk_score thresholds for AVOID
    - Use financial_score and base_case_gain for APPLY
    """

    raise NotImplementedError


