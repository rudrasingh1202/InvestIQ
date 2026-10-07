"""Extract key sections from DRHP documents.

This module identifies and extracts:
- Risk Factors
- Financials
- Objects of Issue

Logic is intentionally placeholder.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DRHPSections:
    """Extracted DRHP sections."""

    risk_factors: str
    financials: str
    objects_of_issue: str


def extract_sections(drhp_text: str) -> DRHPSections:
    """Extract major DRHP sections from the full DRHP text.

    Minimal working implementation based on keyword boundaries.

    Heuristic approach:
    - Find start marker for each section.
    - Slice until the next likely section marker.

    This is enough to unblock end-to-end PDF upload → risk scoring.
    """

    import re

    text = drhp_text or ""

    def slice_between(start_regex: str, end_regexes: list[str]) -> str:
        m = re.search(start_regex, text, flags=re.IGNORECASE)
        if not m:
            return ""
        start_idx = m.start()

        end_idx = None
        for er in end_regexes:
            m2 = re.search(er, text[m.end():], flags=re.IGNORECASE)
            if m2:
                candidate = m.end() + m2.start()
                if end_idx is None or candidate < end_idx:
                    end_idx = candidate

        return text[start_idx:end_idx].strip() if end_idx is not None else text[start_idx:].strip()

    risk_factors = slice_between(
        r"\bRISK\s+FACTORS\b|\bRisk\s+Factors\b",
        [
            r"\bFINANCIAL\s+STATEMENTS\b|\bFinancial\s+Statements\b|\bFINANCIALS\b",
            r"\bOBJECTS\s+OF\s+THE\s+ISSUE\b|\bObjects\s+of\s+the\s+Issue\b|\bObjects\s+of\s+Issue\b",
        ],
    )

    financials = slice_between(
        r"\bFINANCIAL\s+STATEMENTS\b|\bFinancial\s+Statements\b|\bFINANCIALS\b",
        [
            r"\bOBJECTS\s+OF\s+THE\s+ISSUE\b|\bObjects\s+of\s+the\s+Issue\b|\bObjects\s+of\s+Issue\b",
            r"\bRISK\s+FACTORS\b|\bRisk\s+Factors\b",
        ],
    )

    objects_of_issue = slice_between(
        r"\bOBJECTS\s+OF\s+THE\s+ISSUE\b|\bObjects\s+of\s+the\s+Issue\b|\bObjects\s+of\s+Issue\b",
        [
            r"\bRISK\s+FACTORS\b|\bRisk\s+Factors\b",
            r"\bFINANCIAL\s+STATEMENTS\b|\bFinancial\s+Statements\b|\bFINANCIALS\b",
        ],
    )

    return DRHPSections(
        risk_factors=risk_factors,
        financials=financials,
        objects_of_issue=objects_of_issue,
    )


def detect_doc_type(text: str) -> str:
    sample = text[:5000].lower()
    drhp_score = sum(1 for w in [
        'draft red herring prospectus', 'this draft', 
        'drhp', 'subject to sebi observations'
    ] if w in sample)
    rhp_score = sum(1 for w in [
        'red herring prospectus', 'price band of',
        'bid/offer opening date', 'floor price',
        'cap price', 'offer price', 'bid amount'
    ] if w in sample)
    
    if drhp_score > rhp_score:
        return 'DRHP'
    elif rhp_score > 0:
        return 'RHP'
    return 'Prospectus'


def extract_price_band(text: str, doc_type: str = None) -> str:
    import re
    search_text = text[:50000]
    
    patterns = [
        r'[Pp]rice\s+[Bb]and[^₹\d]{0,20}[₹Rs\.]*\s*(\d+)\s*(?:to|[-–])\s*[₹Rs\.]*\s*(\d+)',
        r'[₹Rs\.]+\s*(\d+)\s*(?:to|[-–])\s*[₹Rs\.]+\s*(\d+)\s*per\s+[Ee]quity',
        r'[Ff]loor\s+[Pp]rice[^₹\d]{0,30}[₹Rs\.]*\s*(\d+)',
        r'[Cc]ap\s+[Pp]rice[^₹\d]{0,30}[₹Rs\.]*\s*(\d+)',
        r'(\d{2,4})\s*(?:to|[-–])\s*(\d{2,4})\s*per\s+[Ee]quity\s+[Ss]hare',
        r'[Bb]id\s+[Pp]rice[^₹\d]{0,20}[₹Rs\.]*\s*(\d+)\s*(?:to|[-–])\s*[₹Rs\.]*\s*(\d+)',
        r'[Oo]ffer\s+[Pp]rice[^₹\d]{0,20}[₹Rs\.]*\s*(\d+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        if matches:
            match = matches[0]
            if isinstance(match, tuple) and len(match) >= 2:
                low, high = match[0], match[1]
                if low and high and 1 <= int(low) <= 10000:
                    return f"₹{low} - ₹{high} per share"
            elif isinstance(match, str) and match:
                if 1 <= int(match) <= 10000:
                    return f"₹{match} per share"
    
    if doc_type == 'DRHP':
        return "Not yet set (DRHP stage)"
    return "Not disclosed in document"


def extract_issue_size(text: str) -> str:
    import re
    search_text = text[:50000]
    
    crore_patterns = [
        r'[Aa]ggregating\s+(?:up\s+)?to\s*[₹Rs\.]*\s*([\d,]+(?:\.\d+)?)\s*[Cc]rore',
        r'[Tt]otal\s+[Ii]ssue\s+[Ss]ize\s*[:\-]?\s*[₹Rs\.]*\s*([\d,]+(?:\.\d+)?)\s*[Cc]rore',
        r'[Ff]resh\s+[Ii]ssue[^.]{0,80}[₹Rs\.]*\s*([\d,]+(?:\.\d+)?)\s*[Cc]rore',
        r'[Oo]ffer\s+[Ff]or\s+[Ss]ale[^.]{0,80}[₹Rs\.]*\s*([\d,]+(?:\.\d+)?)\s*[Cc]rore',
        r'[Rr]aise[^.]{0,50}[₹Rs\.]*\s*([\d,]+(?:\.\d+)?)\s*[Cc]rore',
        r'[₹Rs\.]+\s*([\d,]+(?:\.\d+)?)\s*[Cc]rores?\b',
    ]
    
    found_amounts = []
    for pattern in crore_patterns:
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        for m in matches:
            amt = float(m.replace(',', ''))
            if amt > 1:
                found_amounts.append(amt)
    
    if found_amounts:
        largest = max(found_amounts)
        return f"₹{largest:,.0f} Crore"
    
    share_patterns = [
        r'[Uu]p\s+to\s+([\d,]+)\s*[Ee]quity\s+[Ss]hares',
        r'[Aa]ggregating[^.]{0,30}([\d,]+)\s*[Ee]quity\s+[Ss]hares',
        r'[Ff]resh\s+[Ii]ssue[^.]{0,50}([\d,]+)\s*[Ee]quity\s+[Ss]hares',
    ]
    for pattern in share_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            return f"{match.group(1)} Equity Shares"
    
    return "Not disclosed in document"


def extract_issue_dates(text: str, doc_type: str = None) -> str:
    import re
    search_text = text[:50000]
    
    open_patterns = [
        r'[Bb]id\s*/?\s*[Oo]ffer\s+[Oo]pen(?:ing)?\s+[Dd]ate\s*[:\-]?\s*(\w+\s+\d{1,2},?\s*\d{4})',
        r'[Bb]id\s*/?\s*[Oo]ffer\s+[Oo]pen(?:ing)?\s+[Dd]ate\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'[Ii]ssue\s+[Oo]pen(?:s|ing)?\s*(?:on|date)?\s*[:\-]?\s*(\w+\s+\d{1,2},?\s*\d{4})',
        r'[Ii]ssue\s+[Oo]pen(?:s|ing)?\s*(?:on|date)?\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'[Oo]pening\s+[Dd]ate\s*[:\-]?\s*(\w+\s+\d{1,2},?\s*\d{4})',
        r'[Oo]pening\s+[Dd]ate\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{1,2}\s+\w+\s+202[4-9])[^\n]{0,30}[Oo]pen',
        r'[Oo]pen[^\n]{0,30}(\d{1,2}\s+\w+\s+202[4-9])',
    ]
    
    close_patterns = [
        r'[Bb]id\s*/?\s*[Oo]ffer\s+[Cc]los(?:e|ing)\s+[Dd]ate\s*[:\-]?\s*(\w+\s+\d{1,2},?\s*\d{4})',
        r'[Bb]id\s*/?\s*[Oo]ffer\s+[Cc]los(?:e|ing)\s+[Dd]ate\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'[Ii]ssue\s+[Cc]los(?:e|ing|es)\s*(?:on|date)?\s*[:\-]?\s*(\w+\s+\d{1,2},?\s*\d{4})',
        r'[Cc]losing\s+[Dd]ate\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    
    open_date = None
    close_date = None
    
    for pattern in open_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            open_date = match.group(1).strip()
            break
    
    for pattern in close_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            close_date = match.group(1).strip()
            break
    
    if open_date and close_date:
        return f"{open_date} to {close_date}"
    elif open_date:
        return f"Opens: {open_date}"
    elif close_date:
        return f"Closes: {close_date}"
    
    if doc_type == 'DRHP':
        return "Not yet announced (DRHP stage)"
    return "Not disclosed in document"


