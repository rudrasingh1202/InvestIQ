#!/usr/bin/env python3
"""Standalone yfinance diagnostic script for InvestIQ.

DO NOT modify any InvestIQ application files.
This script is for diagnosis only.
"""

from __future__ import annotations

import platform
import sys
import time
import traceback
from typing import Any

import requests
import yfinance as yf

REPORT_WIDTH = 50


def section(title: str) -> None:
    print("\n" + "=" * REPORT_WIDTH)
    print(title)
    print("=" * REPORT_WIDTH)


def subsection(title: str) -> None:
    print("\n" + "-" * REPORT_WIDTH)
    print(title)
    print("-" * REPORT_WIDTH)


def print_result(label: str, result: str) -> None:
    print(f"{label}: {result}")


def test_symbol(label: str, symbol: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "label": label,
        "symbol": symbol,
        "success": False,
        "rows": 0,
        "error_type": "N/A",
        "error_message": "N/A",
    }

    print(f"\nTesting: {symbol}")
    try:
        df = yf.download(
            symbol,
            period="6mo",
            auto_adjust=True,
            progress=False,
        )

        if df is not None and not df.empty and len(df) > 0:
            result["success"] = True
            result["rows"] = len(df)
            print_result("Result", "SUCCESS")
            print_result("Rows Returned", str(len(df)))
        else:
            result["success"] = False
            result["rows"] = 0
            print_result("Result", "FAILED")
            print_result("Rows Returned", "0")
            print_result("Reason", "Empty DataFrame returned")

    except Exception as e:
        result["success"] = False
        result["error_type"] = type(e).__name__
        result["error_message"] = str(e)
        print_result("Result", "FAILED")
        print_result("Exception Type", type(e).__name__)
        print_result("Exception Message", str(e)[:300])

    return result


def test_symbol_with_retry(
    label: str, symbol: str, max_retries: int = 3, delay: int = 2
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

    print(f"\nTesting: {symbol}")
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[DEBUG] Attempt {attempt}/{max_retries}...")
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
                print_result("Result", "SUCCESS")
                print_result("Rows Returned", str(len(df)))
                return result
            else:
                print(f"[DEBUG] Attempt {attempt}: Empty DataFrame returned")

        except Exception as e:
            result["attempts"] = attempt
            result["error_type"] = type(e).__name__
            result["error_message"] = str(e)
            print(f"[DEBUG] Attempt {attempt} FAILED: {type(e).__name__}: {str(e)[:200]}")
            traceback.print_exc()

        if attempt < max_retries:
            print(f"[DEBUG] Waiting {delay} seconds before retry...")
            time.sleep(delay)

    result["success"] = False
    result["rows"] = 0
    print_result("Result", "FAILED")
    print_result("Final Status", f"Failed after {max_retries} attempts")
    return result


def check_url(url: str, timeout: int = 10) -> dict[str, Any]:
    result: dict[str, Any] = {
        "url": url,
        "reachable": False,
        "status_code": "N/A",
        "error": "N/A",
    }

    print(f"\nTesting URL: {url}")
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        result["reachable"] = True
        result["status_code"] = resp.status_code
        print_result("Status Code", str(resp.status_code))
        print_result("Reachable", "YES")
    except requests.exceptions.ConnectionError as e:
        result["error"] = f"ConnectionError: {e}"
        print_result("Reachable", "NO")
        print_result("Error", result["error"])
    except requests.exceptions.Timeout as e:
        result["error"] = f"Timeout: {e}"
        print_result("Reachable", "NO")
        print_result("Error", result["error"])
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        print_result("Reachable", "NO")
        print_result("Error", result["error"])

    return result


def main() -> None:
    print("=" * REPORT_WIDTH)
    print("YFINANCE DIAGNOSTIC REPORT")
    print("=" * REPORT_WIDTH)

    # Environment info
    section("ENVIRONMENT INFO")
    print_result("yfinance version", yf.__version__)
    print_result("Python version", sys.version.split()[0])
    print_result("Operating System", f"{platform.system()} {platform.release()}")
    print_result("Platform", platform.platform())

    # Internet connectivity
    section("INTERNET CONNECTIVITY")
    yahoo_main = check_url("https://finance.yahoo.com")
    yahoo_api1 = check_url("https://query1.finance.yahoo.com")
    yahoo_api2 = check_url("https://query2.finance.yahoo.com")

    internet_pass = yahoo_main["reachable"] and yahoo_api1["reachable"] and yahoo_api2["reachable"]
    print_result("\nOverall Connectivity", "PASS" if internet_pass else "FAIL")

    # US Stocks
    section("US STOCKS")
    us_stocks = [
        ("AAPL", "AAPL"),
        ("MSFT", "MSFT"),
        ("NVDA", "NVDA"),
    ]
    us_results = []
    for label, symbol in us_stocks:
        us_results.append(test_symbol_with_retry(label, symbol, max_retries=3, delay=2))
    us_pass = any(r["success"] for r in us_results)
    print_result("\nUS Stocks Overall", "PASS" if us_pass else "FAIL")

    # NSE Stocks
    section("NSE STOCKS")
    nse_stocks = [
        ("RELIANCE.NS", "RELIANCE.NS"),
        ("TCS.NS", "TCS.NS"),
        ("WIPRO.NS", "WIPRO.NS"),
        ("INFY.NS", "INFY.NS"),
    ]
    nse_results = []
    for label, symbol in nse_stocks:
        nse_results.append(test_symbol_with_retry(label, symbol, max_retries=3, delay=2))
    nse_pass = any(r["success"] for r in nse_results)
    print_result("\nNSE Stocks Overall", "PASS" if nse_pass else "FAIL")

    # Symbol format tests
    section("SYMBOL FORMAT TESTS")
    symbol_tests = [
        ("RELIANCE.NS", "RELIANCE.NS"),
        ("RELIANCE.BO", "RELIANCE.BO"),
        ("AAPL", "AAPL"),
        ("^NSEI", "^NSEI"),
        ("^BSESN", "^BSESN"),
    ]
    symbol_results = []
    for label, symbol in symbol_tests:
        symbol_results.append(test_symbol(label, symbol))

    # Raw exception logging
    section("RAW EXCEPTION LOGGING")
    print("Logging raw exceptions for NSE stocks...")
    for label, symbol in [("RELIANCE.NS", "RELIANCE.NS"), ("TCS.NS", "TCS.NS")]:
        try:
            df = yf.download(symbol, period="6mo", auto_adjust=True, progress=False)
            if df.empty:
                print(f"\n{symbol}: Empty DataFrame returned (no exception raised)")
        except Exception as e:
            print(f"\n{symbol} Exception:")
            print(f"  Type: {type(e).__name__}")
            print(f"  Message: {e}")
            print(f"  Args: {e.args}")
            traceback.print_exc()

    # Final diagnostic report
    section("FINAL DIAGNOSTIC REPORT")

    print_result("Internet Connectivity", "PASS" if internet_pass else "FAIL")
    print_result("Yahoo Finance Reachable", "PASS" if yahoo_main["reachable"] else "FAIL")
    print_result("Yahoo API query1", "PASS" if yahoo_api1["reachable"] else "FAIL")
    print_result("Yahoo API query2", "PASS" if yahoo_api2["reachable"] else "FAIL")
    print_result("US Stocks", "PASS" if us_pass else "FAIL")
    print_result("NSE Stocks", "PASS" if nse_pass else "FAIL")
    print_result("yfinance Installation", "PASS")

    # Determine root cause
    subsection("DIAGNOSIS")

    if not internet_pass:
        possible_cause = "Network Issue - Internet connectivity or Yahoo Finance endpoints blocked"
        recommended_fix = "Check network, firewall, VPN, or ISP restrictions"
    elif us_pass and not nse_pass:
        possible_cause = "Symbol/Endpoint Issue - US stocks work but NSE stocks fail"
        recommended_fix = "Yahoo Finance may have changed NSE symbol format or endpoint. Check Yahoo Finance documentation for current NSE symbol conventions."
    elif not us_pass and not nse_pass:
        possible_cause = "API Issue - Both US and NSE stocks failing"
        recommended_fix = "Yahoo Finance API may be temporarily down or deprecated. Consider alternative data sources or wait for service restoration."
    else:
        possible_cause = "Unknown - Both US and NSE stocks working"
        recommended_fix = "No action needed"

    print_result("Possible Root Cause", possible_cause)
    print_result("Recommended Fix", recommended_fix)

    # Detailed failure info
    subsection("DETAILED FAILURE INFO")
    for r in nse_results:
        if not r["success"]:
            print(f"\n{r['label']} ({r['symbol']}):")
            print(f"  Attempts: {r['attempts']}")
            print(f"  Error Type: {r['error_type']}")
            print(f"  Error Message: {r['error_message'][:200]}")

    print("\n" + "=" * REPORT_WIDTH)
    print("END OF DIAGNOSTIC REPORT")
    print("=" * REPORT_WIDTH)


if __name__ == "__main__":
    main()
