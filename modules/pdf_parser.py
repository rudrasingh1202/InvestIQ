"""PDF parsing utilities.

This module is responsible for extracting text and basic page-level
metadata from DRHP PDFs.

Logic is intentionally left as placeholders for scaffolding.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParsedPDF:
    """Container for extracted PDF artifacts."""

    text: str
    pages: list[str]
    metadata: dict[str, Any]


def extract_text_from_pdf(file_path: str) -> ParsedPDF:
    """Extract full text and pages from a PDF.

    Scaffolding implementation to support basic extraction paths:
    - Use pdfplumber for text extraction.
    - If extracted text for a page is empty, try OCR fallback via pytesseract.

    Note:
        This function is intentionally lightweight; it can be extended later
        with PyMuPDF fallback and more robust OCR preprocessing.

    Args:
        file_path: Absolute or relative path to a PDF file.

    Returns:
        ParsedPDF: extracted text and page artifacts.
    """

    import pdfplumber

    pages: list[str] = []
    full_text_parts: list[str] = []

    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

            # OCR fallback for image-based pages
            if not text.strip():
                try:
                    from PIL import Image
                    import pytesseract

                    # pdfplumber provides a raster via to_image
                    pil_img = page.to_image(resolution=300)
                    img = pil_img.original
                    if isinstance(img, Image.Image):
                        text = pytesseract.image_to_string(img)
                    else:
                        text = ""
                except Exception:
                    text = ""


            pages.append(text)
            full_text_parts.append(text)

    full_text = "\n".join(full_text_parts).strip()
    metadata: dict[str, Any] = {"source": file_path}

    return ParsedPDF(text=full_text, pages=pages, metadata=metadata)


def extract_text_by_page(pdf_path: str) -> dict[int, str]:
    """Extract text for each page.

    Args:
        pdf_path: PDF file path.

    Returns:
        Mapping from 1-based page number to extracted text.
    """

    parsed = extract_text_from_pdf(pdf_path)
    return {idx + 1: txt for idx, txt in enumerate(parsed.pages)}


def extract_tables(pdf_path: str) -> list["pd.DataFrame"]:
    """Extract tables from a PDF using pdfplumber.

    Expected implementation details:
    - Use page.extract_tables()
    - Convert each table to a pandas DataFrame.

    Returns:
        List of DataFrames (empty list if none found).
    """

    import pandas as pd
    import pdfplumber

    tables: list[pd.DataFrame] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                extracted = page.extract_tables()
            except Exception:
                extracted = []

            for tbl in extracted or []:
                # pdfplumber returns a list of rows; attempt to treat first row as header
                if not tbl:
                    continue
                header = tbl[0] if any(cell is not None for cell in tbl[0]) else None
                if header is not None:
                    rows = tbl[1:]
                    # Replace None headers with blank strings
                    header = [str(h).strip() if h is not None else "" for h in header]
                    df = pd.DataFrame(rows, columns=header)
                else:
                    df = pd.DataFrame(tbl)
                tables.append(df)

    return tables


def detect_sections(text_by_page: dict[int, str]) -> dict[str, str]:
    """Detect key DRHP sections using regex heading boundaries.

    The function is heuristic-based: it concatenates text between
    detected heading boundaries.

    Args:
        text_by_page: Mapping of page number -> extracted page text.

    Returns:
        dict with keys:
        ['risk_factors', 'financials', 'objects_of_issue',
         'promoter_info', 'industry_overview', 'legal_proceedings']
        containing clean text strings.
    """

    import re

    section_patterns: dict[str, list[re.Pattern[str]]] = {
        "risk_factors": [
            re.compile(r"\bRISK\s+FACTORS\b", re.IGNORECASE),
            re.compile(r"\bRisk\s+Factors\b", re.IGNORECASE),
        ],
        "financials": [
            re.compile(r"\bFINANCIAL\s+STATEMENTS\b", re.IGNORECASE),
            re.compile(r"\bFinancial\s+Statements\b", re.IGNORECASE),
            re.compile(r"\bFINANCIALS\b", re.IGNORECASE),
        ],
        "objects_of_issue": [
            re.compile(r"\bOBJECTS\s+OF\s+THE\s+ISSUE\b", re.IGNORECASE),
            re.compile(r"\bObjects\s+of\s+the\s+Issue\b", re.IGNORECASE),
            re.compile(r"\bObjects\s+of\s+Issue\b", re.IGNORECASE),
        ],
        "promoter_info": [
            re.compile(r"\bPROMOTERS\b", re.IGNORECASE),
            re.compile(r"\bPromoter(s)?\b", re.IGNORECASE),
        ],
        "industry_overview": [
            re.compile(r"\bINDUSTRY\s+OVERVIEW\b", re.IGNORECASE),
            re.compile(r"\bIndustry\s+Overview\b", re.IGNORECASE),
            re.compile(r"\bINDUSTRY\b", re.IGNORECASE),
        ],
        "legal_proceedings": [
            re.compile(r"\bLEGAL\s+PROCEEDINGS\b", re.IGNORECASE),
            re.compile(r"\bLegal\s+Proceedings\b", re.IGNORECASE),
        ],
    }

    # Flatten all pages with page separators for boundary detection
    page_items = sorted(text_by_page.items(), key=lambda x: x[0])

    # Find earliest start page per section
    starts: dict[str, int] = {}
    for page_num, txt in page_items:
        hay = txt or ""
        if not hay.strip():
            continue
        for section, patterns in section_patterns.items():
            if section in starts:
                continue
            if any(p.search(hay) for p in patterns):
                starts[section] = page_num

    # Create end boundaries: next section start page among all sections
    results: dict[str, str] = {}
    for section, start_page in starts.items():
        # Find next boundary after start
        boundary_pages = [p for s, p in starts.items() if s != section and p > start_page]
        end_page = min(boundary_pages) - 1 if boundary_pages else None

        collected: list[str] = []
        for page_num, txt in page_items:
            if page_num < start_page:
                continue
            if end_page is not None and page_num > end_page:
                break
            collected.append((txt or "").strip())

        results[section] = "\n".join([c for c in collected if c]).strip()

    # Ensure all expected keys exist
    expected_keys = [
        "risk_factors",
        "financials",
        "objects_of_issue",
        "promoter_info",
        "industry_overview",
        "legal_proceedings",
    ]
    for k in expected_keys:
        results.setdefault(k, "")

    return results


