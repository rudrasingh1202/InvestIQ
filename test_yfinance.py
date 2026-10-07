#!/usr/bin/env python3
"""Standalone yfinance diagnostic script.

DO NOT import any InvestIQ modules.
"""

from __future__ import annotations

import platform
import sys
import time
import traceback
from typing import Any

import requests
import yfinance as yf


def section(title: str) -> None:
    width = 55
    print("\n" + "=" * width)
    print(title)
    print("=" * width)


def subsection(title: str) -> None:
    width = 55
    print("\n" + "-" * width)
    print(title)
    print("-" * width)


def check_url(
    url: str, timeout: int = 15, label: str | None = None
) -> dict[str, Any]:
    label = label or url
    result: dict[str, Any] = {
        "label": label,
        "url": url,
        "reachable": False,
        "status_code": None,
        "response_length": 0,
        "error": None,
    }

    print(f"\nTesting URL: {url}")
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
        )
        result["reachable"] = True
        result["status_code"] = resp.status_code
        result["response_length"] = len(resp.text)
        print(f"  Status Code : {resp.status_code}")
        print(f"  Reachable  : YES")
        print(f"  Response length: {len(resp.text)}")
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        print(f"  Reachable  : NO")
        print(f"  Error      : {type(e).__name__}: {e}")

    return result


def test_symbol(
    label: str, symbol: str, max_retries: int = 1, delay: int = 0
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "label": label,
        "symbol": symbol,
        "success": False,
        "rows": 0,
        "error_type": "N/A",
        "error_message": "N/A",
        "attempts": 0,
    }

    print(f"\nTesting symbol: {symbol}")

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  Attempt {attempt}/{max_retries}...")
            df = yf.download(
                symbol,
                period="6mo",
                auto_adjust=True,
                progress=False,
            )

            if df is not None and not df.empty and len(df) > 0:
                result["success"] = True
                result["rows"] = len(df)
                result["attempts"] = attempt
                print(f"  Result     : SUCCESS")
                print(f"  Rows       : {len(df)}")
                return result
            else:
                result["attempts"] = attempt
                result["error_message"] = "Empty DataFrame returned"
                print(f"  Result     : FAILED")
                print(f"  Reason     : Empty DataFrame returned")

        except Exception as e:
            result["attempts"] = attempt
            result["error_type"] = type(e).__name__
            result["error_message"] = str(e)
            print(f"  Result     : FAILED")
            print(f"  Exception  : {type(e).__name__}")
            print(f"  Message    : {e}")
            traceback.print_exc()

        if attempt < max_retries and delay > 0:
            print(f"  Waiting {delay}s before retry...")
            time.sleep(delay)

    return result


def main() -> None:
    width = 55

    # 1. Environment info
    section("ENVIRONMENT INFO")
    print(f"  Python version  : {sys.version.split()[0]}")
    print(f"  yfinance version: {yf.__version__}")
    print(f"  requests version: {requests.__version__}")
    print(f"  OS              : {platform.system()} {platform.release()}")
    print(f"  Platform        : {platform.platform()}")

    # 2. Internet connectivity
    section("INTERNET CONNECTIVITY")
    yahoo_main = check_url("https://finance.yahoo.com", label="finance.yahoo.com")
    yahoo_api1 = check_url(
        "https://query1.finance.yahoo.com", label="query1.finance.yahoo.com"
    )
    yahoo_api2 = check_url(
        "https://query2.finance.yahoo.com", label="query2.finance.yahoo.com"
    )

    internet_pass = (
        yahoo_main["reachable"]
        and yahoo_api1["reachable"]
        and yahoo_api2["reachable"]
        and yahoo_api1["status_code"] == 200
        and yahoo_api2["status_code"] == 200
    )

    print(f"\nOverall Connectivity: {'PASS' if internet_pass else 'FAIL'}")

    # 3. US stocks
    section("US STOCKS (yf.download)")
    us_results = []
    for label, symbol in [
        ("AAPL", "AAPL"),
        ("MSFT", "MSFT"),
        ("NVDA", "NVDA"),
    ]:
        us_results.append(
            test_symbol(label, symbol, max_retries=2, delay=2)
        )

    us_pass = any(r["success"] for r in us_results)
    print(f"\nUS Stocks Overall: {'PASS' if us_pass else 'FAIL'}")

    # 4. Indian stocks
    section("INDIAN STOCKS (yf.download)")
    nse_results = []
    for label, symbol in [
        ("RELIANCE.NS", "RELIANCE.NS"),
        ("TCS.NS", "TCS.NS"),
        ("INFY.NS", "INFY.NS"),
        ("WIPRO.NS", "WIPRO.NS"),
    ]:
        nse_results.append(
            test_symbol(label, symbol, max_retries=2, delay=2)
        )

    nse_pass = any(r["success"] for r in nse_results)
    print(f"\nIndian Stocks Overall: {'PASS' if nse_pass else 'FAIL'}")

    # 5. NSE index
    section("NSE INDEX (yf.download)")
    index_results = []
    for label, symbol in [
        ("NSE 50 Index", "^NSEI"),
    ]:
        index_results.append(
            test_symbol(label, symbol, max_retries=2, delay=2)
        )

    index_pass = any(r["success"] for r in index_results)
    print(f"\nNSE Index Overall: {'PASS' if index_pass else 'FAIL'}")

    # 6. Raw requests to Yahoo Finance endpoints
    section("RAW REQUESTS TO YAHOO FINANCE ENDPOINTS")
    raw_urls = [
        "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1d",
        "https://query2.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1d",
        "https://query1.finance.yahoo.com/v7/finance/quote?symbols=RELIANCE.NS",
        "https://query2.finance.yahoo.com/v7/finance/quote?symbols=RELIANCE.NS",
    ]
    raw_results = []
    for url in raw_urls:
        raw_results.append(
            check_url(
                url,
                timeout=15,
                label=url.split("/")[2] + url.split("v")[1].split("?")[0],
            )
        )

    # 7. Final diagnostic report
    section("FINAL DIAGNOSTIC REPORT")

    print(f"  Internet Connectivity : {'PASS' if internet_pass else 'FAIL'}")
    print(
        f"  Yahoo Finance Main   : {'PASS' if yahoo_main['reachable'] else 'FAIL'}"
    )
    print(
        f"  Yahoo API query1     : {'PASS' if yahoo_api1['reachable'] else 'FAIL'}"
    )
    print(
        f"  Yahoo API query2     : {'PASS' if yahoo_api2['reachable'] else 'FAIL'}"
    )
    print(f"  US Stocks            : {'PASS' if us_pass else 'FAIL'}")
    print(f"  Indian Stocks        : {'PASS' if nse_pass else 'FAIL'}")
    print(f"  NSE Index            : {'PASS' if index_pass else 'FAIL'}")
    print(f"  yfinance Installation: PASS")

    # Determine root cause
    subsection("DIAGNOSIS")

    failed_checks = []
    if not internet_pass:
        failed_checks.append("internet_connectivity")
    if not yahoo_api1["reachable"] or yahoo_api1["status_code"] != 200:
        failed_checks.append("yahoo_api1")
    if not yahoo_api2["reachable"] or yahoo_api2["status_code"] != 200:
        failed_checks.append("yahoo_api2")
    if not us_pass:
        failed_checks.append("us_stocks")
    if not nse_pass:
        failed_checks.append("indian_stocks")
    if not index_pass:
        failed_checks.append("nse_index")

    if "internet_connectivity" in failed_checks:
        root_cause = "InvestIQ code issue"
        recommendation = "Rare case - yfinance may be failing due to rapid version changes. Pin yfinance==0.2.40 and avoid using direct data access APIs through Yahoo Finance without fallback mechanisms."
    elif "yahoo_api1" in failed_checks or "yahoo_api2" in failed_checks:
        root_cause = "Yahoo endpoint blocked"
        recommendation = "Yahoo API endpoints are returning non-200 status codes. This is likely a network restriction or Yahoo-side change. Use a proxy or alternative data source."
    elif "us_stocks" in failed_checks and "indian_stocks" in failed_checks:
        root_cause = "Yahoo Finance issue"
        recommendation = "All symbols failing - likely a Yahoo Finance service degradation or API change. Check status.investiq.com or wait for restoration."
    elif "us_stocks" in failed_checks and "indian_stocks" not in failed_checks:
        root_cause = "Network issue"
        recommendation = "US symbols failing - possibly IP blocked for US region but Indian API still functional."
    elif "us_stocks" not in failed_checks and "indian_stocks" in failed_checks:
        root_cause = "NSE symbols unsupported"
        recommendation = "US stocks work but NSE stocks fail. Check if yfinance supports .NS symbols in current version or if symbol format changed."
    elif "nse_index" in failed_checks and "indian_stocks" not in failed_checks:
        root_cause = "InvestIQ code issue"
        recommendation = "Index symbols failing but regular stocks work - likely a symbol format requirement change for index tickers."
    else:
        root_cause = "Everything works"
        recommendation = "No action needed"

    print(f"\nRoot Cause: {root_cause}")
    print(f"Recommended Fix: {recommendation}")

    print("\n" + "=" * width)
    print("END OF DIAGNOSTIC REPORT")
    print("=" * width)


if __name__ == "__main__":
    main()
