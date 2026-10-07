"""Risk scoring for DRHPs.

Provides a 0-100 risk score combining:
- Rule-based keyword scoring
- Optional LLM risk summary (via Gemini)

All logic is best-effort and non-blocking for UI.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskScore:
    """Risk scoring output."""

    score_0_100: int
    reasons: list[str]


def classify_risk_severity(risk_text: str) -> dict[str, int]:
    """Classify risk severity by category using keyword matching.

    Returns category scores in [0..10] based on keyword hit density.
    """

    text_lower = (risk_text or "").lower()

    # Financial risk keywords
    financial_keywords = [
        "debt",
        "borrowing",
        "loan",
        "default",
        "loss",
        "negative cash",
        "working capital",
        "npa",
        "write-off",
        "revenue decline",
        "unprofitable",
        "net loss",
    ]

    # Regulatory risk keywords
    regulatory_keywords = [
        "sebi",
        "rbi",
        "regulation",
        "compliance",
        "penalty",
        "license",
        "approval",
        "government policy",
        "gst",
        "statutory",
        "non-compliance",
        "show cause",
    ]

    # Litigation keywords
    litigation_keywords = [
        "litigation",
        "lawsuit",
        "legal proceedings",
        "court",
        "dispute",
        "arbitration",
        "criminal",
        "fir",
        "notice",
        "contingent liability",
        "claim against",
    ]

    # Operational keywords
    operational_keywords = [
        "key personnel",
        "attrition",
        "technology failure",
        "cyber",
        "supply chain",
        "raw material",
        "competition",
        "market share",
        "customer concentration",
        "single client",
    ]

    # Promoter keywords
    promoter_keywords = [
        "promoter",
        "related party",
        "conflict of interest",
        "pledge",
        "encumbrance",
        "family",
        "group company",
        "promoter selling",
        "offer for sale",
    ]

    def score(keywords: list[str], text: str, max_score: int = 10) -> int:
        if not keywords:
            return 0
        hits = sum(1 for k in keywords if k in text)
        # Scale: proportional to hit density; cap at max_score.
        return min(max_score, int((hits / len(keywords)) * max_score * 2.5))

    return {
        "financial": score(financial_keywords, text_lower),
        "regulatory": score(regulatory_keywords, text_lower),
        "litigation": score(litigation_keywords, text_lower),
        "operational": score(operational_keywords, text_lower),
        "promoter": score(promoter_keywords, text_lower),
    }


def llm_risk_summary(risk_text: str) -> str:
    """Summarize the TOP 5 most critical risks via Gemini.

    Expected output format:
    1. [RISK NAME] (HIGH/MEDIUM/LOW): One clear sentence ...
    ... up to 5
    """

    from utils.helpers import call_llm

    prompt = f"""Analyze these risk factors and list the TOP 5 risks:

Format:
1. HIGH: One sentence about the biggest risk.
2. HIGH: One sentence about another major risk.
3. MEDIUM: One sentence about a medium risk.
4. MEDIUM: One sentence about another medium risk.
5. LOW: One sentence about a lower risk.

Risk Factors: {risk_text[:4000]}"""

    content = call_llm(prompt, max_tokens=400)
    content = content.replace('<pad>', '').replace('埠', '').replace('<pad', '')
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        words = line.split()
        if len(words) > 10 and len(set(words)) < 3:
            continue
        cleaned_lines.append(line)
    content = '\n'.join(cleaned_lines).strip()
    return content


def overall_risk_score(all_scores: dict[str, int]) -> int:
    """Compute overall risk score (0-100), higher = riskier.

    Weighted average of category scores (each 0-10):
    - financial 30%
    - regulatory 25%
    - litigation 20%
    - operational 15%
    - promoter 10%
    """

    weights = {
        "financial": 0.30,
        "regulatory": 0.25,
        "litigation": 0.20,
        "operational": 0.15,
        "promoter": 0.10,
    }

    total = 0.0
    for k, w in weights.items():
        total += float(all_scores.get(k, 0)) * w

    # total in [0..10]; scale to [0..100]
    return int(round(total * 10))


def score_risk(
    *,
    risk_factors_text: str,
    financials_text: str | None = None,
    use_llm: bool = True,
) -> RiskScore:
    """Compute a risk score for a DRHP."""

    categories = classify_risk_severity(risk_factors_text)
    score = overall_risk_score(categories)

    reasons: list[str] = [
        f"{k}: {categories.get(k, 0)}/10" for k in ["financial", "regulatory", "litigation", "operational", "promoter"]
    ]

    # Optional: LLM risk summary (non-blocking)
    if use_llm:
        try:
            import config

            if config.GEMINI_API_KEY:
                summary = llm_risk_summary(risk_factors_text)
                if summary:
                    reasons.append(summary)
        except Exception:
            pass

    return RiskScore(score_0_100=score, reasons=reasons)