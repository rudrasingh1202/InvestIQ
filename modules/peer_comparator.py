"""Peer comparison for financial metrics."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PeerComparison:
    """Comparison results."""

    sector: str
    peer_tickers: list[str]
    metrics: pd.DataFrame
    notes: list[str]


def compare_to_peers(financials: pd.DataFrame, *, sector: str, top_n: int = 10) -> PeerComparison:
    """Compare a company's metrics to sector peers.

    Args:
        financials: Structured financial metrics for the company.
        sector: Sector/industry category.
        top_n: Number of peers to include.

    Returns:
        PeerComparison.
    """

    raise NotImplementedError

