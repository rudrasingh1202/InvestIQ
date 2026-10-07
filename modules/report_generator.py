"""Generate summary reports for a DRHP analysis."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Report:
    """A structured summary report."""

    title: str
    summary_bullets: list[str]
    risk_summary: str
    financial_summary: str
    objects_of_issue_summary: str


def generate_report(
    *,
    company_name: str,
    risk_score: int,
    risk_reasons: list[str],
    financial_highlights: str,
    objects_of_issue: str,
) -> Report:
    """Generate a human-readable report.

    Args:
        company_name: Name of the company.
        risk_score: 0-100 risk score.
        risk_reasons: List of reasons for risk.
        financial_highlights: Precomputed highlights.
        objects_of_issue: Extracted Objects of Issue text.

    Returns:
        Report.
    """

    raise NotImplementedError

