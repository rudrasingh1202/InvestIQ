"""SEBI/BSE scraping utilities for DRHP PDFs.

Placeholder scaffolding for later implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class DRHPListing:
    """A discovered DRHP document."""

    company_name: str
    pdf_url: str
    filing_date: str | None = None


def search_sebi_bse_drhp(query: str, *, limit: int = 10) -> list[DRHPListing]:
    """Search SEBI/BSE for DRHP PDFs.

    Expected implementation:
    - Scrape relevant pages.
    - Extract company names + PDF links.

    Args:
        query: Search term.
        limit: Max number of results.

    Returns:
        List of DRHPListing.
    """

    raise NotImplementedError

