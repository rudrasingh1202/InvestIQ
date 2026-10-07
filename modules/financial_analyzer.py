"""Financial table parsing and normalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd



@dataclass(frozen=True)
class Financials:
    """Parsed financial statements."""

    pnl: pd.DataFrame
    balance_sheet: pd.DataFrame
    cash_flow: pd.DataFrame
    raw: dict[str, Any]


def parse_pl_statement(tables: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """Parse P&L statement DataFrame from a list of extracted tables.

    Target output columns:
        [year, revenue, ebitda, pat, eps, ebitda_margin, pat_margin]

    Notes:
    - This is a heuristic extractor: scans tables for recognizable column names.
    - Handles INR Lakhs / INR Crores by detecting units from column headers/text.

    Args:
        tables: Extracted tables from pdfplumber.

    Returns:
        Normalized P&L DataFrame.
    """

    raise NotImplementedError


def parse_balance_sheet(tables: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """Parse Balance Sheet statement from extracted tables.

    Target output columns:
        [year, total_assets, total_debt, equity, debt_equity_ratio, current_ratio]

    Args:
        tables: Extracted tables from pdfplumber.

    Returns:
        Normalized balance sheet DataFrame.
    """

    raise NotImplementedError


def parse_cashflow(tables: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """Parse Cash Flow statement from extracted tables.

    Target output columns:
        [year, operating_cf, investing_cf, financing_cf, free_cashflow]

    Args:
        tables: Extracted tables from pdfplumber.

    Returns:
        Normalized cash flow DataFrame.
    """

    raise NotImplementedError


def compute_growth_rates(pl_df: pd.DataFrame) -> dict[str, float]:
    """Compute CAGR for revenue and PAT over 3 years.

    Expects pl_df has columns: year, revenue, pat.

    Returns:
        dict {revenue_cagr, pat_cagr}.
    """

    raise NotImplementedError


def financial_health_score(
    pl_df: pd.DataFrame,
    bs_df: pd.DataFrame,
    cf_df: pd.DataFrame,
) -> int:
    """Compute financial health score (0-100).

    Scoring rules:
      - positive PAT growth = +20
      - D/E < 1 = +20
      - positive OCF = +20
      - EBITDA margin > 15% = +20
      - revenue CAGR > 20% = +20

    Args:
        pl_df: Parsed P&L DataFrame.
        bs_df: Parsed Balance Sheet DataFrame.
        cf_df: Parsed Cash Flow DataFrame.

    Returns:
        int in [0, 100]
    """

    raise NotImplementedError


def parse_financial_tables(pdf_text: str) -> Financials:
    """Parse P&L, Balance Sheet, and Cash Flow tables from DRHP text.

    Placeholder for later integration with pdf table extraction.

    Args:
        pdf_text: Extracted DRHP text.

    Returns:
        Financials with structured statements.
    """

    raise NotImplementedError


