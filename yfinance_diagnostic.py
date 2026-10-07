#!/usr/bin/env python3
"""Standalone Yahoo Finance diagnostic script.

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
    width = 60
    print("\n" + "=" * width)
    print(title)
    print("=" * width)


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
        print(f"  Status Code    : {resp.status_code}")
        print(f"  Reachable      : YES")
        print(f"  Response length: {len(resp.text)}")
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        print(f"  Reachable      : NO")
        print(f"  Error          : {type(e).__name__}: {e}")

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
    width = 60

    # TEST 1: Environment info
    section("TEST 1: ENVIRONMENT INFO")
    print(f"  Python version  : {sys.version.split()[0]}")
    print(f"  yfinance version: {yf.__version__}")
    print(f"  requests version: {requests.__version__}")
    print(f"  OS              : {platform.system()} {platform.release()}")
    print(f"  Platform        : {platform.platform()}")

    # TEST 2: Internet connectivity
    section("TEST 2: INTERNET CONNECTIVITY")
    yahoo_main = check_url(
        "https://finance.yahoo.com", label="finance.yahoo.com"
    )

    # TEST 3: Yahoo API endpoints
    section("TEST 3: YAHOO API ENDPOINTS")
    yahoo_api1 = check_url(
        "https://query1.finance.yahoo.com",
        label="query1.finance.yahoo.com",
    )
    yahoo_api2 = check_url(
        "https://query2.finance.yahoo.com",
        label="query2.finance.yahoo.com",
    )

    # TEST 4: US stocks
    section("TEST 4: US STOCKS (yf.download)")
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

    # TEST 5: Indian stocks
    section("TEST 5: INDIAN STOCKS (yf.download)")
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

    # TEST 6: Indian indices
    section("TEST 6: INDIAN INDICES (yf.download)")
    index_results = []
    for label, symbol in [
        ("NSE 50 Index", "^NSEI"),
        ("BSE Sensex", "^BSESN"),
    ]:
        index_results.append(
            test_symbol(label, symbol, max_retries=2, delay=2)
        )

    index_pass = any(r["success"] for r in index_results)
    print(f"\nIndian Indices Overall: {'PASS' if index_pass else 'FAIL'}")

    # TEST 7: Raw endpoint checks
    section("TEST 7: RAW YAHOO ENDPOINT CHECKS")
    raw_urls = [
        "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1d",
        "https://query2.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1d",
        "https://query1.finance.yahoo.com/v7/finance/quote?symbols=RELIANCE.NS",
        "https://query2.finance.yahoo.com/v7/finance/quote?symbols=RELIANCE.NS",
    ]
    raw_results = []
    for url in raw_urls:
        raw_results.append(
            check_url(url, timeout=15, label=url.split("/")[2])
        )

    # TEST 8: Final diagnostic report
    section("TEST 8: FINAL DIAGNOSTIC REPORT")

    internet_pass = (
        yahoo_main["reachable"]
        and yahoo_api1["reachable"]
        and yahoo_api2["reachable"]
    )

    api_pass = (
        yahoo_api1.get("status_code") == 200
        and yahoo_api2.get("status_code") == 200
    )

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
    print(f"  Indian Indices       : {'PASS' if index_pass else 'FAIL'}")
    print(f"  yfinance Installation: PASS")

    # Determine root cause
    if not internet_pass:
        root_cause = "Network issue"
        recommendation = "Yahoo Finance is unreachable from this machine. Check internet connection, firewall, or VPN."
    elif not api_pass:
        root_cause = "Yahoo Finance API endpoints are blocked"
        recommendation = "Main site is reachable, but API endpoints are failing. Possible Yahoo-side change, regional block, or auth/crumb requirement change."
    elif us_pass and not nse_pass:
        root_cause = "NSE data unavailable"
        recommendation = "US stocks work, but NSE stocks/indices fail. Yahoo Finance may have changed/deprecated NSE symbol support."
    elif not us_pass and not nse_pass:
        root_cause = "Yahoo Finance issue / yfinance issue"
        recommendation = "All symbols fail despite endpoints being reachable. yfinance may be incompatible with current Yahoo API responses."
    else:
        root_cause = "Yahoo Finance works"
        recommendation = "No action needed."

    print("\n" + "-" * width)
    print("DIAGNOSIS")
    print("-" * width)
    print(f"  Root Cause      : {root_cause}")
    print(f"  Recommended Fix : {recommendation}")

    # Detailed failure info
    print("\n" + "-" * width)
    print("DETAILED FAILURE INFO")
    print("-" * width)
    for r in us_results + nse_results + index_results:
        if not r["success"]:
            print(f"\n  {r['label']} ({r['symbol']}):")
            print(f"    Attempts      : {r['attempts']}")
            print(f"    Error Type    : {r['error_type']}")
            print(f"    Error Message : {r['error_message'][:200]}")

    print("\n" + "=" * width)
    print("END OF DIAGNOSTIC REPORT")
    print("=" * width)


if __name__ == "__main__":
    main()
