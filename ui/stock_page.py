import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import os
import sys
import re

print("\n" + "="*50)
print("Checking .env file...")
print("="*50)

try:
    from dotenv import load_dotenv
    load_dotenv()
    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key:
        print("GROQ_API_KEY Found: YES")
        print(f"GROQ_API_KEY Length: {len(groq_key)}")
    else:
        print("GROQ_API_KEY Found: NO")
        print("GROQ_API_KEY Length: 0")
except Exception as e:
    print(f"ERROR loading .env: {e}")
    print("GROQ_API_KEY Found: NO")

print("="*50)
print(f"yfinance version: {yf.__version__}")
print("="*50)

POPULAR_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK",
    "INFY", "ICICIBANK", "SBIN",
    "WIPRO", "ADANIENT",
]


def format_stock_symbol(symbol: str) -> str:
    sym = symbol.strip().upper()
    if sym.endswith(".NS") or sym.endswith(".BO"):
        return sym
    return f"{sym}.NS"


def get_valid_peer_symbol(symbol: str) -> str:
    return format_stock_symbol(symbol)


def _download_with_retry(symbol: str, max_retries: int = 3, delay: int = 2):
    import time
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[DATA] Attempt {attempt}/{max_retries} for {symbol}...")
            df = yf.download(
                symbol,
                period="6mo",
                auto_adjust=True,
                progress=False
            )
            
            if df is not None and not df.empty and len(df) > 0:
                print(f"[DATA] SUCCESS on attempt {attempt} - Rows: {len(df)}")
                return df
            else:
                print(f"[DATA] Attempt {attempt}: Empty data returned")
                
        except Exception as e:
            print(f"[DATA] Attempt {attempt} FAILED: {type(e).__name__}: {str(e)[:200]}")
        
        if attempt < max_retries:
            print(f"[DATA] Waiting {delay} seconds before retry...")
            time.sleep(delay)
    
    print(f"[DATA] FINAL RESULT: FAILED after {max_retries} attempts")
    return None


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_get(info, key, default=None):
    v = info.get(key, default)
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _safe_metric(value):
    try:
        if value is None:
            return None
        f = float(value)
        if f == 0.0:
            return None
        return f
    except (TypeError, ValueError):
        return None


def _is_probable_decimal_pct(value):
    try:
        num = float(value)
    except (TypeError, ValueError):
        return False
    return -1 < num < 1 and num != 0


def _to_pct(value):
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if -1 < num < 1 and num != 0:
        return num * 100
    return num


_PCT_METRICS = {
    'ROE', 'Net Profit Margin', 'Operating Margin',
    'Revenue Growth', 'Earnings Growth', 'EPS Growth',
    'Dividend Yield',
}


def _extract_financial_metrics(ticker):
    metrics = {}

    def _try_extract(bs, fs, cf):
        if bs is not None and not bs.empty and len(bs.columns) >= 1:
            bs_col = bs.columns[0]
            def _bs(key):
                try:
                    v = bs.loc[key, bs_col] if key in bs.index else None
                    return _safe_float(v, None)
                except Exception:
                    return None

            current_assets = _bs('Current Assets')
            current_liabilities = _bs('Current Liabilities')
            shareholder_equity = _bs('Stockholders Equity') or _bs('Stockholders Equity Attributable To Parent')
            total_debt = _bs('Total Debt') or _bs('Long Term Debt') or _bs('Short Term Debt') or _bs('Current Debt')

            if current_assets and current_liabilities and current_liabilities != 0:
                metrics['currentRatio'] = current_assets / current_liabilities

            if total_debt and shareholder_equity and shareholder_equity != 0:
                metrics['debtToEquity'] = total_debt / shareholder_equity

        if fs is not None and not fs.empty and len(fs.columns) >= 1:
            fs_col = fs.columns[0]
            def _fs(key):
                try:
                    v = fs.loc[key, fs_col] if key in fs.index else None
                    return _safe_float(v, None)
                except Exception:
                    return None

            ebit = _fs('EBIT') or _fs('Operating Income') or _fs('EBIT And Equity In Earnings Of Affiliates')
            interest_expense = _fs('Interest Expense') or _fs('Interest Expense On Debt')
            revenue = _fs('Total Revenue') or _fs('Revenue') or _fs('Operating Revenue')
            net_income = _fs('Net Income') or _fs('Net Income Common Stockholders')
            operating_income = _fs('Operating Income') or _fs('EBIT')
            total_assets = _fs('Total Assets')

            if operating_income and revenue and revenue != 0:
                metrics['operatingMargins'] = (operating_income / revenue) * 100

            if net_income and revenue and revenue != 0:
                metrics['profitMargins'] = (net_income / revenue) * 100

            if ebit and interest_expense and interest_expense != 0:
                metrics['interestCoverage'] = ebit / abs(interest_expense)

            if shareholder_equity and net_income and shareholder_equity != 0:
                metrics['returnOnEquity'] = (net_income / shareholder_equity) * 100

            if len(fs.columns) >= 2:
                fs_col_prev = fs.columns[1]
                def _fs_prev(key):
                    try:
                        v = fs.loc[key, fs_col_prev] if key in fs.index else None
                        return _safe_float(v, None)
                    except Exception:
                        return None

                prev_revenue = _fs_prev('Total Revenue') or _fs_prev('Revenue') or _fs_prev('Operating Revenue')
                prev_net_income = _fs_prev('Net Income') or _fs_prev('Net Income Common Stockholders')

                if revenue and prev_revenue and prev_revenue != 0:
                    metrics['revenueGrowth'] = ((revenue - prev_revenue) / abs(prev_revenue)) * 100

                if net_income and prev_net_income and prev_net_income != 0:
                    metrics['earningsGrowth'] = ((net_income - prev_net_income) / abs(prev_net_income)) * 100

        if cf is not None and not cf.empty:
            cf_col = cf.columns[0] if len(cf.columns) > 0 else None
            if cf_col is not None:
                def _cf(key):
                    try:
                        v = cf.loc[key, cf_col] if key in cf.index else None
                        return _safe_float(v, None)
                    except Exception:
                        return None

                operating_cf = _cf('Operating Cash Flow') or _cf('Cash Flow From Operating Activities')
                capex = _cf('Capital Expenditures') or _cf('Capital Expenditure')

                if operating_cf is not None and capex is not None:
                    metrics['freeCashflow'] = operating_cf + capex

    try:
        _try_extract(
            getattr(ticker, 'balance_sheet', None),
            getattr(ticker, 'financials', None),
            getattr(ticker, 'cashflow', None),
        )
    except Exception:
        pass

    try:
        _try_extract(
            getattr(ticker, 'quarterly_balance_sheet', None),
            getattr(ticker, 'quarterly_financials', None),
            getattr(ticker, 'quarterly_cashflow', None),
        )
    except Exception:
        pass

    return metrics


def get_fundamental_metrics(info, ticker=None):
    result = {}

    source_priority = [
        lambda k: _safe_get(info, k),
        lambda k: _safe_get(getattr(ticker, 'info', {}), k) if ticker else None,
        lambda k: _safe_get(getattr(ticker, 'fast_info', {}), k) if ticker else None,
    ]

    if ticker is not None:
        source_priority.extend([
            lambda k: _safe_get(getattr(ticker, 'financial_data', {}), k),
        ])

    basic_keys = {
        'marketCap': None,
        'trailingPE': None,
        'priceToBook': None,
        'returnOnEquity': None,
        'profitMargins': None,
        'operatingMargins': None,
        'revenueGrowth': None,
        'earningsGrowth': None,
        'dividendYield': None,
        'beta': None,
        'pegRatio': None,
        'enterpriseToEbitda': None,
        'debtToEquity': None,
        'currentRatio': None,
        'interestCoverage': None,
        'freeCashflow': None,
        'bookValue': None,
        'epsGrowth': None,
        'averageVolume': None,
    }

    for key in basic_keys:
        val = None
        for source in source_priority:
            try:
                val = source(key)
                if val is not None:
                    break
            except Exception:
                continue
        if val is not None:
            result[key] = val

    if ticker is not None:
        try:
            fin_metrics = _extract_financial_metrics(ticker)
            for key, val in fin_metrics.items():
                if val is not None:
                    result[key] = val
        except Exception:
            pass

    return result


def _calculate_rsi(close_series, window=14):
    delta = close_series.diff()
    gain = delta.clip(lower=0).rolling(window=window).mean()
    loss = (-delta.clip(upper=0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _calculate_macd(close_series, fast=12, slow=26, signal=9):
    ema_fast = close_series.ewm(span=fast, adjust=False).mean()
    ema_slow = close_series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _calculate_ema(close_series, span):
    return close_series.ewm(span=span, adjust=False).mean()


def _calculate_sma(close_series, window):
    return close_series.rolling(window=window).mean()


def _calculate_volatility(close_series, window=20):
    returns = close_series.pct_change().dropna()
    if len(returns) < window:
        return 0.0
    return returns.rolling(window=window).std().iloc[-1] * np.sqrt(252) * 100


def _format_number(num):
    if not num:
        return "N/A"
    if num >= 1e12:
        return f"₹{num/1e12:.2f}T"
    elif num >= 1e9:
        return f"₹{num/1e9:.2f}B"
    elif num >= 1e7:
        return f"₹{num/1e7:.2f}Cr"
    elif num >= 1e5:
        return f"₹{num/1e5:.2f}L"
    return f"₹{num:,.0f}"


def format_large_number(num, prefix="₹"):
    if num is None:
        return "N/A"
    try:
        num = float(num)
    except (TypeError, ValueError):
        return "N/A"
    if num >= 1e12:
        return f"{prefix}{num/1e12:.2f}T"
    elif num >= 1e9:
        return f"{prefix}{num/1e9:.2f}B"
    elif num >= 1e7:
        return f"{prefix}{num/1e7:.2f}Cr"
    elif num >= 1e5:
        return f"{prefix}{num/1e5:.2f}L"
    return f"{prefix}{num:,.0f}"


def _fundamental_color_and_label(metric, value):
    if value is None:
        return 'gray', 'UNAVAILABLE'
    try:
        num = float(value)
    except (TypeError, ValueError):
        return 'gray', 'UNAVAILABLE'

    if metric == 'Market Cap':
        if num > 1e12: return 'green', 'LARGE CAP'
        elif num > 1e10: return 'yellow', 'MID CAP'
        elif num > 1e9: return 'orange', 'SMALL CAP'
        else: return 'red', 'MICRO CAP'
    if metric == 'P/E Ratio':
        if num < 15: return 'green', 'ATTRACTIVE'
        elif num < 25: return 'yellow', 'FAIR VALUE'
        elif num < 40: return 'orange', 'EXPENSIVE'
        else: return 'red', 'VERY EXPENSIVE'
    if metric == 'P/B Ratio':
        if num < 1: return 'green', 'UNDERVALUED'
        elif num < 3: return 'yellow', 'ATTRACTIVE'
        elif num < 5: return 'orange', 'FAIR'
        else: return 'red', 'EXPENSIVE'
    if metric == 'ROE':
        if num > 20: return 'green', 'EXCELLENT'
        elif num > 15: return 'yellow', 'GOOD'
        elif num > 10: return 'orange', 'AVERAGE'
        else: return 'red', 'WEAK'
    if metric == 'Net Profit Margin':
        if num > 20: return 'green', 'EXCELLENT'
        elif num > 15: return 'yellow', 'GOOD'
        elif num > 10: return 'orange', 'AVERAGE'
        else: return 'red', 'WEAK'
    if metric == 'Operating Margin':
        if num > 25: return 'green', 'EXCELLENT'
        elif num > 20: return 'yellow', 'GOOD'
        elif num > 15: return 'orange', 'AVERAGE'
        else: return 'red', 'WEAK'
    if metric == 'Debt to Equity':
        if num < 0.5: return 'green', 'HEALTHY'
        elif num < 1.0: return 'yellow', 'GOOD'
        elif num < 2.0: return 'orange', 'MODERATE'
        else: return 'red', 'RISKY'
    if metric == 'Current Ratio':
        if num > 2.0: return 'green', 'HEALTHY'
        elif num > 1.5: return 'yellow', 'ADEQUATE'
        else: return 'red', 'RISKY'
    if metric == 'Interest Coverage':
        if num > 5: return 'green', 'SAFE'
        elif num > 2: return 'yellow', 'ADEQUATE'
        else: return 'red', 'RISKY'
    if metric == 'Revenue Growth':
        if num > 20: return 'green', 'STRONG GROWTH'
        elif num > 10: return 'yellow', 'MODERATE GROWTH'
        elif num > 0: return 'orange', 'WEAK GROWTH'
        else: return 'red', 'NEGATIVE'
    if metric == 'Earnings Growth':
        if num > 20: return 'green', 'STRONG GROWTH'
        elif num > 10: return 'yellow', 'MODERATE GROWTH'
        elif num > 0: return 'orange', 'WEAK GROWTH'
        else: return 'red', 'NEGATIVE'
    if metric == 'EPS Growth':
        if num > 20: return 'green', 'STRONG GROWTH'
        elif num > 10: return 'yellow', 'MODERATE GROWTH'
        elif num > 0: return 'orange', 'WEAK GROWTH'
        else: return 'red', 'NEGATIVE'
    if metric == 'PEG Ratio':
        if num < 1: return 'green', 'UNDERVALUED'
        elif num < 2: return 'yellow', 'FAIR'
        else: return 'red', 'OVERVALUED'
    if metric == 'EV/EBITDA':
        if num < 10: return 'green', 'LOW'
        elif num < 20: return 'yellow', 'FAIR'
        else: return 'red', 'HIGH'
    if metric == 'Dividend Yield':
        if num > 3: return 'green', 'ATTRACTIVE'
        elif num > 1.5: return 'yellow', 'MODERATE'
        else: return 'red', 'LOW'
    if metric == 'Beta':
        if num < 1: return 'green', 'STABLE'
        elif num <= 1.5: return 'yellow', 'MODERATE RISK'
        else: return 'red', 'HIGH VOLATILITY'
    if metric == 'Book Value':
        return 'blue', 'BOOK VALUE'
    if metric == 'Free Cash Flow':
        if num > 0: return 'green', 'POSITIVE'
        else: return 'red', 'NEGATIVE'
    if metric == '52 Week High':
        return 'blue', 'HIGH'
    if metric == '52 Week Low':
        return 'blue', 'LOW'
    if metric == 'Average Volume':
        return 'blue', 'VOLUME'
    return 'gray', 'UNAVAILABLE'


def _render_fundamental_card(label, display_value, numeric_value=None, suffix='', color='gray'):
    color_map = {
        'green': ('#ECFDF5', '#00B386', '#065F46'),
        'yellow': ('#FFFBEB', '#F59E0B', '#92400E'),
        'red': ('#FEF2F2', '#FF4757', '#991B1B'),
        'blue': ('#EFF6FF', '#3B82F6', '#1E40AF'),
        'gray': ('#F9FAFB', '#6B7280', '#374151'),
    }
    bg_color, text_color, border_color = color_map.get(color, color_map['gray'])

    if display_value is None or display_value == 'N/A':
        display_value = 'N/A'
        label_text = ''
    else:
        label_text = _fundamental_color_and_label(label, numeric_value if numeric_value is not None else display_value)[1]

    st.markdown(
        f"""<div style="
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 16px 12px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        ">
            <div style="
                font-size: 11px;
                color: {text_color};
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.6px;
                margin-bottom: 8px;
            ">{label}</div>
            <div style="
                font-size: 22px;
                font-weight: 800;
                color: {border_color};
                margin-bottom: 6px;
            ">{display_value}</div>
            <div style="
                font-size: 10px;
                color: {text_color};
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.6px;
            ">{label_text}</div>
        </div>""",
        unsafe_allow_html=True
    )


def _get_value(info, key, default=None):
    v = info.get(key, default)
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def calculate_stock_health_score(info: dict, rsi_val=50.0, macd_val=0.0, signal_val=0.0, ema20_val=0.0, ema50_val=0.0, curr_price=0.0, volume=0) -> dict:
    score_details = {
        'Valuation': {'score': 0, 'max': 20, 'reason': ''},
        'Financial Health': {'score': 0, 'max': 20, 'reason': ''},
        'Profitability': {'score': 0, 'max': 20, 'reason': ''},
        'Growth': {'score': 0, 'max': 20, 'reason': ''},
        'Technical Strength': {'score': 0, 'max': 20, 'reason': ''},
    }

    pe = _get_value(info, 'trailingPE')
    pb = _get_value(info, 'priceToBook')
    roe = _get_value(info, 'returnOnEquity')
    debt_to_equity = _get_value(info, 'debtToEquity')
    current_ratio = _get_value(info, 'currentRatio')
    profit_margin = _get_value(info, 'profitMargins')
    operating_margin = _get_value(info, 'operatingMargins')
    revenue_growth = _get_value(info, 'revenueGrowth')
    earnings_growth = _get_value(info, 'earningsGrowth')
    beta = _get_value(info, 'beta')
    dividend_yield = _get_value(info, 'dividendYield')
    market_cap = _get_value(info, 'marketCap')
    interest_coverage = _get_value(info, 'interestCoverage')
    eps_growth = _get_value(info, 'epsGrowth')
    free_cashflow = _get_value(info, 'freeCashflow')

    valuation_score = 10
    reasons = []
    if pe is not None:
        if pe < 15: valuation_score += 5; reasons.append("Low P/E")
        elif pe < 25: valuation_score += 3; reasons.append("Fair P/E")
        else: valuation_score -= 3; reasons.append("High P/E")
    if pb is not None:
        if pb < 3: valuation_score += 3; reasons.append("Low P/B")
        elif pb < 5: valuation_score += 1; reasons.append("Fair P/B")
        else: valuation_score -= 2; reasons.append("High P/B")
    if market_cap is not None:
        if market_cap > 1e12: valuation_score += 2; reasons.append("Large Cap")
        elif market_cap > 1e10: valuation_score += 1; reasons.append("Mid Cap")
    valuation_score = max(0, min(20, valuation_score))
    score_details['Valuation']['score'] = valuation_score
    score_details['Valuation']['reason'] = ', '.join(reasons[:3]) if reasons else 'Limited data'

    health_score = 10
    reasons = []
    if debt_to_equity is not None:
        if debt_to_equity < 0.5: health_score += 5; reasons.append("Low Debt")
        elif debt_to_equity < 1.0: health_score += 3; reasons.append("Moderate Debt")
        else: health_score -= 3; reasons.append("High Debt")
    if current_ratio is not None:
        if current_ratio > 2.0: health_score += 3; reasons.append("Strong Liquidity")
        elif current_ratio > 1.5: health_score += 1; reasons.append("Adequate Liquidity")
        else: health_score -= 2; reasons.append("Weak Liquidity")
    if interest_coverage is not None:
        if interest_coverage > 5: health_score += 2; reasons.append("Safe Coverage")
        elif interest_coverage > 2: health_score += 1; reasons.append("Adequate Coverage")
        else: health_score -= 1; reasons.append("Poor Coverage")
    health_score = max(0, min(20, health_score))
    score_details['Financial Health']['score'] = health_score
    score_details['Financial Health']['reason'] = ', '.join(reasons[:3]) if reasons else 'Limited data'

    profit_score = 10
    reasons = []
    if roe is not None:
        if roe > 20: profit_score += 5; reasons.append("High ROE")
        elif roe > 15: profit_score += 3; reasons.append("Good ROE")
        else: profit_score -= 2; reasons.append("Low ROE")
    if profit_margin is not None:
        if profit_margin > 20: profit_score += 2; reasons.append("High Margin")
    if operating_margin is not None:
        if operating_margin > 25: profit_score += 2; reasons.append("High OPM")
    profit_score = max(0, min(20, profit_score))
    score_details['Profitability']['score'] = profit_score
    score_details['Profitability']['reason'] = ', '.join(reasons[:3]) if reasons else 'Limited data'

    growth_score = 10
    reasons = []
    if revenue_growth is not None:
        if revenue_growth > 20: growth_score += 4; reasons.append("High Rev Growth")
        elif revenue_growth > 10: growth_score += 2; reasons.append("Moderate Rev Growth")
        else: growth_score -= 2; reasons.append("Low Rev Growth")
    if earnings_growth is not None:
        if earnings_growth > 20: growth_score += 4; reasons.append("High Earnings Growth")
        elif earnings_growth > 10: growth_score += 2; reasons.append("Moderate Earnings Growth")
        else: growth_score -= 2; reasons.append("Low Earnings Growth")
    if eps_growth is not None:
        if eps_growth > 20: growth_score += 2; reasons.append("High EPS Growth")
    growth_score = max(0, min(20, growth_score))
    score_details['Growth']['score'] = growth_score
    score_details['Growth']['reason'] = ', '.join(reasons[:3]) if reasons else 'Limited data'

    tech_score = 10
    reasons = []
    if 30 <= rsi_val <= 70: tech_score += 3; reasons.append("Healthy RSI")
    elif rsi_val < 30: tech_score += 1; reasons.append("Oversold")
    elif rsi_val > 70: tech_score -= 2; reasons.append("Overbought")
    if macd_val > signal_val: tech_score += 2; reasons.append("Bullish MACD")
    else: tech_score -= 1; reasons.append("Bearish MACD")
    if curr_price > 0 and ema50_val > 0:
        if curr_price > ema50_val: tech_score += 2; reasons.append("Price above EMA50")
        else: tech_score -= 1; reasons.append("Price below EMA50")
    if beta is not None:
        if 0.8 <= beta <= 1.2: tech_score += 1; reasons.append("Stable Beta")
        elif beta > 1.5: tech_score -= 1; reasons.append("High Beta")
    if dividend_yield is not None and dividend_yield > 1.5:
        tech_score += 1; reasons.append("Good Dividend")
    week_position = 50.0
    week_high = _safe_get(info, 'fiftyTwoWeekHigh')
    week_low = _safe_get(info, 'fiftyTwoWeekLow')
    if week_high and week_low and week_high > week_low and curr_price > 0:
        week_position = (curr_price - week_low) / (week_high - week_low) * 100
        if week_position < 30: tech_score += 2; reasons.append("Near 52W low")
        elif week_position > 70: tech_score -= 1; reasons.append("Near 52W high")
    tech_score = max(0, min(20, tech_score))
    score_details['Technical Strength']['score'] = tech_score
    score_details['Technical Strength']['reason'] = ', '.join(reasons[:3]) if reasons else 'Limited data'

    total_score = sum(cat['score'] for cat in score_details.values())
    if total_score >= 90: rating = 'STRONG BUY'; color = 'green'
    elif total_score >= 80: rating = 'BUY'; color = 'light-green'
    elif total_score >= 65: rating = 'ACCUMULATE'; color = 'yellow'
    elif total_score >= 50: rating = 'HOLD'; color = 'orange'
    elif total_score >= 35: rating = 'REDUCE'; color = 'orange'
    else: rating = 'AVOID'; color = 'red'

    return {
        'categories': score_details,
        'total_score': total_score,
        'rating': rating,
        'color': color,
    }


def render_stock_health_score(info: dict, rsi_val=50.0, macd_val=0.0, signal_val=0.0, ema20_val=0.0, ema50_val=0.0, curr_price=0.0, volume=0):
    result = calculate_stock_health_score(info, rsi_val, macd_val, signal_val, ema20_val, ema50_val, curr_price, volume)
    total_score = result['total_score']
    rating = result['rating']
    color = result['color']
    categories = result['categories']

    color_styles = {
        'green': ('#ECFDF5', '#00B386', '#065F46'),
        'light-green': ('#F0FDF9', '#00B386', '#065F46'),
        'yellow': ('#FFFBEB', '#F59E0B', '#92400E'),
        'orange': ('#FFF7ED', '#F97316', '#9A3412'),
        'red': ('#FEF2F2', '#FF4757', '#991B1B'),
    }
    bg_color, text_color, border_color = color_styles.get(color, color_styles['yellow'])

    st.markdown("""
    <style>
    .score-card {
        border-radius: 16px;
        padding: 24px;
        border: 1px solid;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .score-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 18px;
    }
    .score-title {
        font-size: 18px;
        font-weight: 700;
        color: #1A1A1A;
        letter-spacing: -0.3px;
    }
    .score-badge {
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .score-main {
        display: flex;
        align-items: center;
        gap: 24px;
        margin-bottom: 18px;
    }
    .score-circle {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 4px solid;
    }
    .score-number {
        font-size: 36px;
        font-weight: 900;
        line-height: 1;
    }
    .score-total {
        font-size: 12px;
        font-weight: 600;
        opacity: 0.8;
    }
    .score-rating {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .score-subtitle {
        font-size: 13px;
        opacity: 0.85;
        margin-top: 2px;
    }
    .score-breakdown {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
    }
    .breakdown-item {
        flex: 1;
        min-width: 100px;
        background: rgba(255,255,255,0.6);
        border-radius: 10px;
        padding: 12px;
        text-align: center;
    }
    .breakdown-label {
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        opacity: 0.7;
        margin-bottom: 4px;
    }
    .breakdown-score {
        font-size: 20px;
        font-weight: 800;
    }
    .breakdown-reason {
        font-size: 10px;
        opacity: 0.8;
        margin-top: 2px;
    }
    .score-summary {
        margin-top: 16px;
        padding-top: 14px;
        border-top: 1px solid rgba(0,0,0,0.06);
        font-size: 13px;
        line-height: 1.5;
        opacity: 0.85;
    }
    </style>
    """, unsafe_allow_html=True)

    summary_parts = []
    for cat_name, cat_data in categories.items():
        if cat_data['reason'] and cat_data['reason'] != 'Limited data':
            summary_parts.append(cat_data['reason'])
    summary_text = '. '.join(summary_parts[:4]) + '.' if summary_parts else 'Analysis based on available market data.'

    st.markdown(f"""
    <div class="score-card" style="
        background: linear-gradient(135deg, {bg_color}, #FFFFFF);
        border-color: {border_color};
        color: {border_color};
    ">
        <div class="score-header">
            <div class="score-title">INVESTIQ STOCK SCORE</div>
            <div class="score-badge" style="
                background: {text_color};
                color: #FFFFFF;
            ">{rating}</div>
        </div>
        <div class="score-main">
            <div class="score-circle" style="
                border-color: {text_color};
                color: {border_color};
            ">
                <div class="score-number">{total_score}</div>
                <div class="score-total">/ 100</div>
            </div>
            <div>
                <div class="score-rating" style="color: {border_color};">{rating}</div>
                <div class="score-subtitle">AI-Powered Health Rating</div>
            </div>
        </div>
        <div class="score-breakdown">
    """, unsafe_allow_html=True)

    breakdown_cols = st.columns(5)
    for idx, (cat_name, cat_data) in enumerate(categories.items()):
        with breakdown_cols[idx]:
            cat_color = 'green' if cat_data['score'] >= 16 else ('yellow' if cat_data['score'] >= 12 else 'orange' if cat_data['score'] >= 8 else 'red')
            cat_color_styles = {
                'green': '#00B386',
                'yellow': '#F59E0B',
                'orange': '#F97316',
                'red': '#FF4757',
            }
            cat_text_color = cat_color_styles.get(cat_color, '#6B7280')
            st.markdown(f"""
            <div class="breakdown-item">
                <div class="breakdown-label">{cat_name}</div>
                <div class="breakdown-score" style="color: {cat_text_color};">
                    {cat_data['score']}/20
                </div>
                <div class="breakdown-reason">{cat_data['reason'][:25]}{'...' if len(cat_data['reason']) > 25 else ''}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
        </div>
        <div class="score-summary">{summary_text}</div>
    </div>
    """, unsafe_allow_html=True)


def fetch_stock_data(symbol: str):
    import yfinance as yf
    import requests

    session = requests.Session()
    session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept': (
            'text/html,application/xhtml+xml,'
            'application/xml;q=0.9,*/*;q=0.8'
        ),
        'Accept-Language': 'en-US,en;q=0.5',
    })

    ticker = None
    try:
        ticker = yf.Ticker(
            symbol,
            session=session
        )
        hist = ticker.history(period="6mo")
        if not hist.empty:
            info = ticker.info
            print(f"[Stock] Got data: {symbol}")
            return info, hist, ticker
    except Exception as e:
        print(f"[Stock] {symbol} failed: {str(e)[:60]}")

    return None, None, ticker


def render_stock_page():
    print("\n" + "="*60)
    print("[RENDER] render_stock_page() START")
    print("="*60)
    st.markdown("""
<style>
.search-section {
    width: 90%;
    max-width: 900px;
    margin: 0 auto;
    padding-top: 8px;
}
.search-row {
    display: flex;
    align-items: center;
    gap: 12px;
}
.search-row .stTextInput {
    flex: 1;
    min-width: 0;
}
.search-row .stButton {
    flex: 0 0 auto;
}
.search-row .stTextInput > div > div > input {
    border-radius: 10px !important;
    border: 1px solid #E5E7EB !important;
    padding: 14px 16px !important;
    font-size: 15px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.search-row .stTextInput > div > div > input:focus {
    border-color: #00B386 !important;
    box-shadow: 0 0 0 3px rgba(0,179,134,0.15) !important;
}
.search-row .stButton > button {
    border-radius: 10px !important;
    padding: 0 24px !important;
    height: 48px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    white-space: nowrap;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    transition: all 0.2s ease;
    border: none !important;
    margin-top: 0 !important;
}
.search-row .stButton > button:hover {
    box-shadow: 0 4px 12px rgba(0,179,134,0.25) !important;
    transform: translateY(-1px);
}
.search-row .stButton > button:active {
    transform: translateY(0);
}
.popular-section {
    width: 90%;
    max-width: 900px;
    margin: 10px auto 0;
}
.popular-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 4px;
}
.popular-row button {
    border-radius: 8px !important;
    border: 1px solid #E5E7EB !important;
    background: #FFFFFF !important;
    color: #1A1A1A !important;
    font-weight: 600 !important;
    padding: 6px 12px !important;
    font-size: 0.85rem !important;
    transition: all 0.15s ease !important;
}
.popular-row button:hover {
    border-color: #00B386 !important;
    color: #00B386 !important;
    background: #F0FDF9 !important;
}
@media (max-width: 768px) {
    .search-section {
        width: 95%;
        padding-top: 4px;
    }
    .search-row {
        flex-direction: column;
        gap: 10px;
    }
    .search-row .stButton {
        width: 100%;
    }
    .search-row .stButton > button {
        width: 100% !important;
        height: 52px !important;
    }
    .search-row .stTextInput > div > div > input {
        padding: 14px 16px !important;
        font-size: 16px !important;
    }
}
</style>
""", unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("## 🚀 AI-Powered Stock Analyzer")
        st.markdown(
            "**Analyze Stocks with AI-Powered Insights**"
        )

    with col_right:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("AI Modules", "4+")
        with c2:
            st.metric("AI Insights", "30+")

    st.markdown("---")

    st.markdown('<div class="search-section">', unsafe_allow_html=True)
    st.markdown('<div class="search-row">', unsafe_allow_html=True)
    col_input, col_btn = st.columns([5, 1.5])
    with col_input:
        raw_symbol = st.text_input(
            "Enter NSE Stock Symbol",
            placeholder="e.g. RELIANCE, TCS, INFY, HDFCBANK",
            label_visibility="collapsed",
            key="stock_symbol_input"
        ).strip().upper()
    with col_btn:
        analyze_clicked = st.button(
            "🔍 Analyze",
            use_container_width=True,
            type="primary",
            key="stock_analyze_btn"
        )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Popular stocks quick select
    st.markdown('<div class="popular-section">', unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:12px;color:#9CA3AF;"
        "margin-bottom:4px;'>Popular:</div>",
        unsafe_allow_html=True
    )
    st.markdown('<div class="popular-row">', unsafe_allow_html=True)
    pop_cols = st.columns(8)
    for i, stock in enumerate(POPULAR_STOCKS):
        with pop_cols[i]:
            if st.button(
                stock,
                key=f"pop_{stock}",
                use_container_width=True
            ):
                st.session_state['selected_stock'] = stock
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Get symbol from session or input
    if st.session_state.get('selected_stock'):
        raw_symbol = st.session_state['selected_stock']
        st.session_state['selected_stock'] = None

    st.markdown("---")

    if not raw_symbol and not analyze_clicked:
        st.markdown("""
<div style="text-align:center;padding:60px 20px;">
    <div style="font-size:48px;margin-bottom:16px;">📊</div>
    <div style="font-size:20px;font-weight:600;
                color:#1A1A1A;margin-bottom:8px;">
        Enter any NSE stock symbol above
    </div>
    <div style="font-size:14px;color:#6B7280;">
        Get live price, technical indicators, 
        fundamental analysis and AI buy/sell signals
    </div>
</div>
""", unsafe_allow_html=True)
        return

    if raw_symbol:
        final_symbol = format_stock_symbol(raw_symbol)

        print("\n" + "="*50)
        print(f"Original Input:\n{raw_symbol}")
        print(f"Formatted Symbol:\n{final_symbol}")
        print(f"Data Source:\nYahoo Finance")

        # Fetch data using yfinance with browser headers
        with st.spinner("Fetching live stock data..."):
            info, hist, ticker = fetch_stock_data(final_symbol)

        if info is None or hist is None:
            st.error(
                f"Could not fetch data for '{raw_symbol}'. "
                "Try after some time or check symbol."
            )
            return

        print(f"Historical Data: SUCCESS")
        print(f"Rows Returned: {len(hist)}")

        # Flatten multi-level columns if present
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = [col[0] for col in hist.columns]

        # Calculate technical indicators
        with st.spinner("Calculating technical indicators..."):
            close = hist['Close']
            high = hist['High']
            low = hist['Low']
            volume = hist['Volume']

            rsi_series = _calculate_rsi(close)
            macd_line, signal_line, histogram = _calculate_macd(close)
            ema20 = _calculate_ema(close, 20)
            ema50 = _calculate_ema(close, 50)
            sma50 = _calculate_sma(close, 50)
            volatility = _calculate_volatility(close)

            curr_price = _safe_float(close.iloc[-1])
            prev_close = _safe_float(close.iloc[-2]) if len(close) > 1 else curr_price
            open_price = _safe_float(hist['Open'].iloc[-1])
            day_high = _safe_float(high.iloc[-1])
            day_low = _safe_float(low.iloc[-1])
            vol = _safe_int(volume.iloc[-1])

            week_high = _safe_float(high.max())
            week_low = _safe_float(low.min())

            # 52 week data from yfinance
            try:
                fifty_two_week_high = _safe_float(info.get('fiftyTwoWeekHigh', week_high))
                fifty_two_week_low = _safe_float(info.get('fiftyTwoWeekLow', week_low))
                market_cap = _safe_float(info.get('marketCap', 0))
                pe_ratio = _safe_float(info.get('trailingPE', None))
                eps = _safe_float(info.get('trailingEps', None))
                div_yield = _safe_float(info.get('dividendYield', None))
                beta = _safe_float(info.get('beta', None))
                sector = info.get('sector', 'N/A')
                industry = info.get('industry', 'N/A')
                company_name = info.get('longName', raw_symbol)
            except Exception:
                fifty_two_week_high = week_high
                fifty_two_week_low = week_low
                market_cap = 0
                pe_ratio = None
                eps = None
                div_yield = None
                beta = None
                sector = 'N/A'
                industry = 'N/A'
                company_name = raw_symbol

            rsi_val = _safe_float(rsi_series.iloc[-1], 50.0)
            macd_val = _safe_float(macd_line.iloc[-1], 0.0)
            signal_val = _safe_float(signal_line.iloc[-1], 0.0)
            ema20_val = _safe_float(ema20.iloc[-1], curr_price)
            ema50_val = _safe_float(ema50.iloc[-1], curr_price)
            sma50_val = _safe_float(sma50.iloc[-1], curr_price)

            print(f"Current Price: {curr_price}")
            print(f"Technical Indicators: SUCCESS")
            print("="*50)

            extra_metrics = get_fundamental_metrics(info, ticker)

            info_dict = {
                "name": company_name,
                "sector": sector,
                "industry": industry,
                "currentPrice": curr_price,
                "previousClose": prev_close,
                "open": open_price,
                "high": day_high,
                "low": day_low,
                "marketCap": market_cap,
                "fiftyTwoWeekHigh": fifty_two_week_high,
                "fiftyTwoWeekLow": fifty_two_week_low,
                "trailingPE": pe_ratio,
                "volume": vol,
                "trailingEps": eps,
                "dividendYield": div_yield,
                "beta": beta,
            }
            info_dict.update(extra_metrics)

            render_stock_dashboard(
                raw_symbol, info_dict, hist,
                rsi_val, macd_val, signal_val,
                ema20_val, ema50_val, sma50_val,
                volatility,
                ticker
            )

    print("\n" + "="*60)
    print("[RENDER] render_stock_page() END")
    print("="*60)


def render_stock_dashboard(
    symbol: str, info: dict, hist,
    rsi_val: float, macd_val: float, signal_val: float,
    ema20_val: float, ema50_val: float, sma50_val: float,
    volatility: float, ticker=None
):
    import plotly.graph_objects as go

    print("\n" + "="*60)
    print(f"[RENDER] render_stock_dashboard() START symbol={symbol}")
    print("="*60)

    company_name = info.get("name", symbol)
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    curr_price = info.get("currentPrice", 0)
    prev_close = info.get("previousClose", curr_price)
    change = curr_price - prev_close
    change_pct = (change / prev_close * 100) if prev_close else 0.0

    if "selected_stock" not in st.session_state:
        st.session_state["selected_stock"] = symbol
    if "stock_snapshot" not in st.session_state:
        st.session_state["stock_snapshot"] = {}
    if "ai_analysis_result" not in st.session_state:
        st.session_state["ai_analysis_result"] = {}
    if "ai_analysis_loading" not in st.session_state:
        st.session_state["ai_analysis_loading"] = False

    if st.session_state["selected_stock"] != symbol:
        st.session_state["selected_stock"] = symbol
        st.session_state["stock_snapshot"] = {}
        st.session_state["ai_analysis_result"] = {}
        st.session_state["ai_analysis_loading"] = False

    st.markdown(
        f"<h3 style='margin:0;color:#1A1A1A;'>{company_name}</h3>"
        f"<div style='font-size:13px;color:#6B7280;margin-bottom:16px;'>"
        f"{sector} • {industry} • NSE: {symbol}</div>",
        unsafe_allow_html=True
    )

    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Current Price",
            f"₹{curr_price:,.2f}",
            delta=f"{change_pct:+.2f}%",
            delta_color="normal"
        )
    with col2:
        st.metric("Market Cap", format_large_number(info.get('marketCap', 0), prefix="₹"))
    with col3:
        week_high = info.get('fiftyTwoWeekHigh', 0)
        week_low = info.get('fiftyTwoWeekLow', 0)
        st.metric(
            "52W High/Low",
            f"₹{week_high:,.0f}" if week_high else "N/A",
            delta=f"Low: ₹{week_low:,.0f}" if week_low else None
        )
    with col4:
        st.metric(
            "P/E Ratio",
            f"{info.get('trailingPE', 0):.1f}x"
            if info.get('trailingPE') else "N/A"
        )
    with col5:
        st.metric("Volume", _format_number(info.get('volume', 0)))

    st.markdown("---")

    # Price Chart
    st.markdown("#### 📊 Price Chart (6 Months)")

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close'],
        name=symbol,
        increasing_line_color='#00B386',
        decreasing_line_color='#FF4757'
    ))

    close_series = hist['Close']
    chart_ema20 = close_series.ewm(span=20, adjust=False).mean()
    chart_ema50 = close_series.ewm(span=50, adjust=False).mean()

    fig.add_trace(go.Scatter(
        x=hist.index, y=chart_ema20,
        name='EMA 20',
        line=dict(color='#F59E0B', width=1.5)
    ))
    fig.add_trace(go.Scatter(
        x=hist.index, y=chart_ema50,
        name='EMA 50',
        line=dict(color='#8B5CF6', width=1.5)
    ))

    fig.update_layout(
        height=400,
        paper_bgcolor='white',
        plot_bgcolor='#FAFAFA',
        xaxis=dict(gridcolor='#E5E7EB'),
        yaxis=dict(gridcolor='#E5E7EB', title='Price (₹)'),
        showlegend=True,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Technical Indicators
    st.markdown("#### ⚡ Technical Indicators")

    t1, t2, t3 = st.columns(3)

    with t1:
        st.markdown("**RSI (14)**")
        rsi_color = (
            "#FF4757" if rsi_val > 70
            else "#00B386" if rsi_val < 30
            else "#F59E0B"
        )
        rsi_label = (
            "Overbought" if rsi_val > 70
            else "Oversold" if rsi_val < 30
            else "Neutral"
        )
        st.markdown(
            f"<div style='font-size:32px;font-weight:700;"
            f"color:{rsi_color}'>{rsi_val:.1f}</div>"
            f"<div style='color:{rsi_color};font-size:13px;"
            f"font-weight:600'>{rsi_label}</div>",
            unsafe_allow_html=True
        )

    with t2:
        st.markdown("**MACD**")
        macd_bullish = macd_val > signal_val
        macd_color = "#00B386" if macd_bullish else "#FF4757"
        macd_label = "Bullish" if macd_bullish else "Bearish"
        st.markdown(
            f"<div style='font-size:32px;font-weight:700;"
            f"color:{macd_color}'>{macd_val:.2f}</div>"
            f"<div style='color:{macd_color};font-size:13px;"
            f"font-weight:600'>{macd_label} Crossover</div>",
            unsafe_allow_html=True
        )

    with t3:
        st.markdown("**Price vs SMA 50**")
        above = curr_price > sma50_val
        trend_color = "#00B386" if above else "#FF4757"
        trend_label = "Above SMA50 (Bullish)" if above else "Below SMA50 (Bearish)"
        st.markdown(
            f"<div style='font-size:32px;font-weight:700;"
            f"color:{trend_color}'>₹{sma50_val:,.0f}</div>"
            f"<div style='color:{trend_color};font-size:13px;"
            f"font-weight:600'>{trend_label}</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Fundamentals - Smart Dynamic Dashboard
    st.markdown("#### 💼 Advanced Fundamentals")

    fundamental_data = {
        'Valuation': [
            ('Market Cap', info.get('marketCap'), ''),
            ('P/E Ratio', info.get('trailingPE'), 'x'),
            ('P/B Ratio', info.get('priceToBook'), 'x'),
            ('PEG Ratio', info.get('pegRatio'), 'x'),
            ('EV/EBITDA', info.get('enterpriseToEbitda'), 'x'),
        ],
        'Profitability': [
            ('ROE', info.get('returnOnEquity'), '%'),
            ('Net Profit Margin', info.get('profitMargins'), '%'),
            ('Operating Margin', info.get('operatingMargins'), '%'),
        ],
        'Financial Health': [
            ('Debt to Equity', info.get('debtToEquity'), 'x'),
            ('Current Ratio', info.get('currentRatio'), 'x'),
            ('Interest Coverage', info.get('interestCoverage'), 'x'),
        ],
        'Growth': [
            ('Revenue Growth', info.get('revenueGrowth'), '%'),
            ('Earnings Growth', info.get('earningsGrowth'), '%'),
            ('EPS Growth', info.get('epsGrowth'), '%'),
        ],
        'Shareholder': [
            ('Dividend Yield', info.get('dividendYield'), '%'),
            ('Beta', info.get('beta'), 'x'),
            ('Book Value', info.get('bookValue'), '₹'),
            ('Free Cash Flow', info.get('freeCashflow'), ''),
        ],
        'Trading': [
            ('52 Week High', info.get('fiftyTwoWeekHigh'), '₹'),
            ('52 Week Low', info.get('fiftyTwoWeekLow'), '₹'),
            ('Average Volume', info.get('averageVolume'), ''),
        ],
    }

    for category, metrics in fundamental_data.items():
        st.markdown(f"**{category}**")
        cols = st.columns(len(metrics))
        for idx, (label, value, suffix) in enumerate(metrics):
            with cols[idx]:
                if label == 'Market Cap':
                    display_value = format_large_number(value, prefix='₹') if value is not None else 'N/A'
                    numeric_value = value
                elif label == 'Free Cash Flow':
                    if value is None:
                        display_value = 'N/A'
                        numeric_value = None
                    else:
                        if value < 0:
                            display_value = f"-{format_large_number(abs(value), prefix='₹')}"
                        else:
                            display_value = format_large_number(value, prefix='₹')
                        numeric_value = value
                elif label == 'Average Volume':
                    display_value = format_large_number(value, prefix='') if value is not None else 'N/A'
                    numeric_value = value
                else:
                    if value is None:
                        display_value = 'N/A'
                        numeric_value = None
                    else:
                        num = float(value)
                        if label in _PCT_METRICS and _is_probable_decimal_pct(num):
                            num = num * 100
                        display_value = f"{num:.2f}{suffix}" if isinstance(num, float) else f"{num}{suffix}"
                        numeric_value = num
                color, _ = _fundamental_color_and_label(label, numeric_value)
                _render_fundamental_card(label, display_value, numeric_value=numeric_value, suffix='', color=color)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Stock Health Score
    render_stock_health_score(
        info,
        rsi_val=rsi_val,
        macd_val=macd_val,
        signal_val=signal_val,
        ema20_val=ema20_val,
        ema50_val=ema50_val,
        curr_price=curr_price,
        volume=info.get('volume', 0),
    )

    st.markdown("---")

    # Peer Comparison
    peer_rows = _render_peer_comparison_section(info, symbol) or []

    st.markdown("---")

    # AI Verdict
    st.markdown("#### 🤖 AI Investment Analysis")

    prev_stock = st.session_state.get("selected_stock")
    if prev_stock and prev_stock != symbol:
        st.session_state["ai_analysis_result"] = {}
        st.session_state["ai_analysis_loading"] = False
    st.session_state["selected_stock"] = symbol

    if "stock_snapshot" not in st.session_state:
        st.session_state["stock_snapshot"] = {}
    if "ai_analysis_result" not in st.session_state:
        st.session_state["ai_analysis_result"] = {}
    if "ai_analysis_loading" not in st.session_state:
        st.session_state["ai_analysis_loading"] = False

    score_data = calculate_stock_health_score(
        info, rsi_val, macd_val, signal_val, ema20_val, ema50_val, curr_price, info.get('volume', 0)
    )

    ai_container = st.container()

    with ai_container:
        ai_clicked = st.button(
            "Generate AI Buy/Sell Signal",
            type="primary",
            key="ai_stock_btn",
        )

        print(f"[AI] Button widget rendered, clicked={ai_clicked}")

        if ai_clicked:
            print(f"\n{'='*50}")
            print(f"AI button clicked for {symbol}")
            print(f"Data snapshot: price={curr_price}, sector={sector}")
            print(f"Peer rows available: {len(peer_rows) if peer_rows else 0}")
            print(f"AI request started")
            print(f"{'='*50}\n")
            st.session_state["ai_analysis_loading"] = True
            st.session_state["ai_analysis_result"] = {}

        print(f"[AI] State check: loading={st.session_state.get('ai_analysis_loading')}, result_type={type(st.session_state.get('ai_analysis_result'))}, result_keys={list(st.session_state.get('ai_analysis_result', {}).keys())}")

        if st.session_state.get("ai_analysis_loading"):
            print(f"[AI] ENTERING LOADING BRANCH")
            with st.spinner("Running AI analysis..."):
                try:
                    from utils.helpers import call_llm

                    stock_key = f"ai_{symbol}"
                    cached = st.session_state.get("ai_analysis_result", {})
                    print(f"[AI] Cache check: stock_key={stock_key}, cached_key={cached.get('stock_key')}, has_raw={bool(cached.get('raw_response'))}")
                    if cached.get("stock_key") == stock_key and cached.get("raw_response"):
                        ai_response = cached["raw_response"]
                        parsed = cached["parsed"]
                        print(f"[AI] Using CACHED response")
                    else:
                        print(f"[AI] Making fresh API call")
                        prompt = _build_ai_prompt(info, symbol, peer_rows, score_data, technical_text=(
                            f"- RSI (14): {rsi_val:.1f}\n"
                            f"- MACD: {macd_val:.2f} vs Signal: {signal_val:.2f}\n"
                            f"- EMA 20: ₹{ema20_val:,.2f}\n"
                            f"- EMA 50: ₹{ema50_val:,.2f}\n"
                            f"- SMA 50: ₹{sma50_val:,.2f}\n"
                            f"- Trend: {'Uptrend' if curr_price > sma50_val else 'Downtrend'}\n"
                            + (f"- 52W High: ₹{info.get('fiftyTwoWeekHigh', 0):,.0f}\n" if info.get('fiftyTwoWeekHigh') else "- 52W High: N/A\n")
                            + (f"- 52W Low: ₹{info.get('fiftyTwoWeekLow', 0):,.0f}\n" if info.get('fiftyTwoWeekLow') else "- 52W Low: N/A\n")
                            + f"- Volatility: {volatility:.1f}%\n"
                        ))

                        ai_response = call_llm(
                            prompt,
                            system_prompt=(
                                "You are a SEBI-registered research analyst. "
                                "Always provide structured, actionable investment analysis. "
                                "Format your response exactly as requested with clear section headers. "
                                "Be concise and data-driven."
                            ),
                            max_tokens=500,
                        )

                        parsed = _parse_ai_response(ai_response)

                        st.session_state["ai_analysis_result"] = {
                            "stock_key": stock_key,
                            "raw_response": ai_response,
                            "parsed": parsed,
                        }

                        print(f"[AI] API response received: verdict={parsed.get('verdict')}, confidence={parsed.get('confidence')}")

                    print(f"[AI] Rendering result directly (no placeholder)")

                    if ai_response:
                        print(f"[AI] Calling _render_ai_verdict_card")
                        _render_ai_verdict_card(parsed, symbol)
                        print(f"[AI] _render_ai_verdict_card completed")
                    else:
                        print(f"[AI] No response, showing warning")
                        st.warning("AI analysis temporarily unavailable. Please try again.")

                    st.session_state["ai_analysis_loading"] = False
                    print(f"[AI] Render complete, loading=False")

                except Exception as e:
                    st.warning("AI analysis temporarily unavailable. Please try again.")
                    st.session_state["ai_analysis_loading"] = False

                    print(f"\n{'='*50}")
                    print(f"AI Analysis: FAILED for {symbol}")
                    print(f"ERROR: {str(e)[:200]}")
                    print(f"{'='*50}\n")

            print(f"[AI] EXITED LOADING BRANCH")

        elif st.session_state.get("ai_analysis_result", {}).get("stock_key") == f"ai_{symbol}":
            print(f"[AI] ENTERING CACHE BRANCH")
            cached = st.session_state["ai_analysis_result"]
            if cached.get("raw_response"):
                print(f"[AI] Rendering from cache directly")
                _render_ai_verdict_card(cached.get("parsed", {}), symbol)
                print(f"[AI] Cache render complete")
            print(f"[AI] EXITED CACHE BRANCH")

        else:
            print(f"[AI] ENTERING IDLE BRANCH")
            st.markdown("*Click the button to generate AI analysis.*")
            print(f"[AI] EXITED IDLE BRANCH")

    print("\n" + "="*60)
    print(f"[RENDER] render_stock_dashboard() END symbol={symbol}")
    print("="*60)

PEER_COMPARISON_MAP = {
    'RELIANCE': ['ONGC', 'IOC', 'BPCL', 'HPCL', 'GAIL', 'OIL'],
    'TCS': ['INFY', 'WIPRO', 'HCLTECH', 'LTIM', 'TECHM'],
    'INFY': ['TCS', 'WIPRO', 'HCLTECH', 'LTIM', 'TECHM'],
    'HDFCBANK': ['ICICIBANK', 'AXISBANK', 'KOTAKBANK', 'SBIN', 'INDUSINDBK'],
    'ICICIBANK': ['HDFCBANK', 'AXISBANK', 'KOTAKBANK', 'SBIN', 'INDUSINDBK'],
    'SBIN': ['HDFCBANK', 'ICICIBANK', 'AXISBANK', 'KOTAKBANK', 'INDUSINDBK'],
    'WIPRO': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'LTIM', 'TECHM'],
    'ADANIENT': ['TATAMOTORS', 'MAHINDRA', 'BAJAJ-AUTO', 'HEROMOTOCO', 'EICHERMOT'],
    'HAL': ['BEL', 'BDL', 'BEML', 'GRSE', 'COCHINSHIP'],
    'BEL': ['HAL', 'BDL', 'BEML', 'GRSE', 'COCHINSHIP'],
    'DMART': ['TRENT', 'SHOPERSTOP', 'RELIANCERET', 'ABFRL', 'FABINDIA'],
    'TRENT': ['DMART', 'SHOPERSTOP', 'RELIANCERET', 'ABFRL', 'FABINDIA'],
    'MARUTI': ['TATAMOTORS', 'MAHINDRA', 'BAJAJ-AUTO', 'HEROMOTOCO', 'EICHERMOT'],
    'TATAMOTORS': ['MARUTI', 'MAHINDRA', 'BAJAJ-AUTO', 'HEROMOTOCO', 'EICHERMOT'],
    'ITC': ['HINDUNILVR', 'NESTLEIND', 'BRITANNIA', 'DABUR', 'MARICO'],
    'HINDUNILVR': ['ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR', 'MARICO'],
    'SUNPHARMA': ['DRREDDY', 'CIPLA', 'DIVISLAB', 'AUROPHARMA', 'LUPIN'],
    'DRREDDY': ['SUNPHARMA', 'CIPLA', 'DIVISLAB', 'AUROPHARMA', 'LUPIN'],
    'LT': ['INFY', 'TCS', 'WIPRO', 'HCLTECH', 'TECHM'],
    'HCLTECH': ['TCS', 'INFY', 'WIPRO', 'LTIM', 'TECHM'],
    'LTIM': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM'],
    'TECHM': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'LTIM'],
    'POWERGRID': ['NTPC', 'TATAPOWER', 'ADANIPOWER', 'TORNTPOWER'],
    'NTPC': ['POWERGRID', 'TATAPOWER', 'ADANIPOWER', 'TORNTPOWER'],
    'TATAPOWER': ['POWERGRID', 'NTPC', 'ADANIPOWER', 'TORNTPOWER'],
    'ONGC': ['RELIANCE', 'IOC', 'BPCL', 'HPCL', 'GAIL'],
    'IOC': ['RELIANCE', 'ONGC', 'BPCL', 'HPCL', 'GAIL'],
    'BPCL': ['RELIANCE', 'ONGC', 'IOC', 'HPCL', 'GAIL'],
    'HPCL': ['RELIANCE', 'ONGC', 'IOC', 'BPCL', 'GAIL'],
    'GAIL': ['RELIANCE', 'ONGC', 'IOC', 'BPCL', 'HPCL'],
    'KOTAKBANK': ['HDFCBANK', 'ICICIBANK', 'AXISBANK', 'SBIN', 'INDUSINDBK'],
    'AXISBANK': ['HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'SBIN', 'INDUSINDBK'],
    'NESTLEIND': ['GRASIM', 'TATACONSUM', 'ITC', 'HINDUNILVR', 'BRITANNIA'],
    'BRITANNIA': ['GRASIM', 'TATACONSUM', 'ITC', 'HINDUNILVR', 'NESTLEIND'],
    'DABUR': ['GRASIM', 'TATACONSUM', 'ITC', 'HINDUNILVR', 'MARICO'],
    'MARICO': ['GRASIM', 'TATACONSUM', 'ITC', 'HINDUNILVR', 'DABUR'],
    'CIPLA': ['SUNPHARMA', 'DRREDDY', 'DIVISLAB', 'AUROPHARMA', 'LUPIN'],
    'AUROPHARMA': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'LUPIN'],
    'LUPIN': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'AUROPHARMA'],
    'JSWSTEEL': ['TATASTEEL', 'SAIL', 'JINDALSTEEL', 'NMDC', 'MOIL'],
    'TATASTEEL': ['JSWSTEEL', 'SAIL', 'JINDALSTEEL', 'NMDC', 'MOIL'],
    'HINDALCO': ['VEDL', 'HINDZINC', 'NATIONALUM', 'ALUMINIUM'],
    'VEDL': ['HINDALCO', 'HINDZINC', 'NATIONALUM', 'ALUMINIUM'],
    'HINDZINC': ['HINDALCO', 'VEDL', 'NATIONALUM', 'ALUMINIUM'],
    'NATIONALUM': ['HINDALCO', 'VEDL', 'HINDZINC', 'ALUMINIUM'],
    'ALUMINIUM': ['HINDALCO', 'VEDL', 'HINDZINC', 'NATIONALUM'],
    'GODREJCP': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR'],
    'PIDILITIND': ['GODREJCP', 'HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA'],
    'COLPAL': ['GODREJCP', 'PIDILITIND', 'HINDUNILVR', 'ITC', 'NESTLEIND'],
    'MCDOWELL-N': ['UBL', 'KINGFISHER', 'MOHITIND'],
    'UBL': ['MCDOWELL-N', 'KINGFISHER', 'MOHITIND'],
    'ZOMATO': ['SWIGGY', 'DUNZO', 'BLINKIT'],
    'PAYTM': ['PHONEPE', 'GPAY', 'MOBIKWIK', 'FREECHARGE'],
    'NYKAA': ['MYKAJARIAN', 'PURPLEDIGITAL'],
    'POLYCAB': ['KEI', 'FINOLEX', 'APOLLO'],
    'INDUSTOWER': ['TATACOMM', 'BSOFT', 'NELCO', 'HFCL', 'STERLITE'],
    'IDEA': ['JIO', 'VODAFONE', 'AIRTEL', 'BSNL'],
    'IRCTC': ['IRFC', 'RAILTEL', 'CONCOR', 'SCI', 'COALINDIA'],
    'SJVN': ['NHPC', 'POWERGRID', 'NTPC', 'TATAPOWER', 'ADANIPOWER'],
    'TATACONSUM': ['GRASIM', 'ITC', 'HINDUNILVR', 'NESTLEIND', 'BRITANNIA'],
}


def _get_peers(symbol: str):
    base = symbol.replace('.NS', '').replace('.BO', '')
    return PEER_COMPARISON_MAP.get(base, [])


def _peer_score(peer):
    score = 50
    reasons = []
    pe = peer.get('trailingPE')
    pb = peer.get('priceToBook')
    roe = peer.get('returnOnEquity')
    rev = peer.get('revenueGrowth')
    ear = peer.get('earningsGrowth')
    div = peer.get('dividendYield')
    de = peer.get('debtToEquity')
    cr = peer.get('currentRatio')
    fcf = peer.get('freeCashflow')
    beta = peer.get('beta')

    if pe is not None:
        if pe < 15: score += 4; reasons.append("Low P/E")
        elif pe < 25: score += 2; reasons.append("Fair P/E")
        else: score -= 2; reasons.append("High P/E")
    if pb is not None:
        if pb < 2: score += 3; reasons.append("Low P/B")
        elif pb < 4: score += 1; reasons.append("Fair P/B")
        else: score -= 1; reasons.append("High P/B")
    if roe is not None:
        if roe > 20: score += 4; reasons.append("High ROE")
        elif roe > 15: score += 2; reasons.append("Good ROE")
        else: score -= 1; reasons.append("Low ROE")
    if rev is not None:
        if rev > 20: score += 3; reasons.append("Strong Growth")
        elif rev > 10: score += 1; reasons.append("Moderate Growth")
        else: score -= 1; reasons.append("Weak Growth")
    if ear is not None:
        if ear > 20: score += 3; reasons.append("Strong Earnings")
        elif ear > 10: score += 1; reasons.append("Moderate Earnings")
        else: score -= 1; reasons.append("Weak Earnings")
    if div is not None:
        if div > 2: score += 1; reasons.append("Good Dividend")
        elif div < 0.5: score -= 1; reasons.append("Low Dividend")
    if de is not None:
        if de < 0.5: score += 2; reasons.append("Low Debt")
        elif de < 1.5: score += 1; reasons.append("Moderate Debt")
        else: score -= 2; reasons.append("High Debt")
    if cr is not None:
        if cr > 2.0: score += 1; reasons.append("Healthy Liquidity")
        elif cr < 1.2: score -= 1; reasons.append("Weak Liquidity")
    if fcf is not None and fcf > 0: score += 1; reasons.append("Positive FCF")
    elif fcf is not None: score -= 1; reasons.append("Negative FCF")
    if beta is not None:
        if 0.8 <= beta <= 1.2: score += 1; reasons.append("Stable Beta")
        elif beta > 1.5: score -= 1; reasons.append("High Beta")
    return max(0, min(100, score)), reasons


def _peer_rating(score):
    if score >= 90: return 'STRONG BUY', 'green'
    if score >= 80: return 'BUY', 'light-green'
    if score >= 65: return 'ACCUMULATE', 'yellow'
    if score >= 50: return 'HOLD', 'orange'
    if score >= 35: return 'REDUCE', 'orange'
    return 'AVOID', 'red'


def _get_metric_color(metric, value, avg=None):
    if value is None:
        return 'gray'
    try:
        num = float(value)
    except (TypeError, ValueError):
        return 'gray'

    if avg is not None and not np.isnan(avg):
        if metric in ['P/E Ratio', 'P/B Ratio', 'Debt/Equity', 'PEG Ratio', 'EV/EBITDA']:
            if num < avg * 0.9: return 'green'
            elif num > avg * 1.1: return 'red'
            else: return 'yellow'
        elif metric in ['ROE', 'Net Profit Margin', 'Operating Margin']:
            if num > 20: return 'green'
            elif num > 15: return 'yellow'
            else: return 'red'
        elif metric in ['Revenue Growth', 'PAT Growth', 'EPS Growth']:
            if num > 20: return 'green'
            elif num > 10: return 'yellow'
            elif num > 0: return 'orange'
            else: return 'red'
        elif metric == 'Dividend Yield':
            if num > 3: return 'green'
            elif num > 1.5: return 'yellow'
            else: return 'red'
        elif metric == 'Market Cap':
            if num > 1e12: return 'green'
            elif num > 1e10: return 'yellow'
            elif num > 1e9: return 'orange'
            else: return 'red'

    if metric == 'Market Cap':
        if num > 1e12: return 'green'
        elif num > 1e10: return 'yellow'
        elif num > 1e9: return 'orange'
        else: return 'red'
    if metric == 'P/E Ratio':
        if num < 15: return 'green'
        elif num < 25: return 'yellow'
        elif num < 40: return 'orange'
        else: return 'red'
    if metric == 'P/B Ratio':
        if num < 1: return 'green'
        elif num < 3: return 'yellow'
        elif num < 5: return 'orange'
        else: return 'red'
    if metric == 'ROE':
        if num > 20: return 'green'
        elif num > 15: return 'yellow'
        elif num > 10: return 'orange'
        else: return 'red'
    if metric == 'Revenue Growth':
        if num > 20: return 'green'
        elif num > 10: return 'yellow'
        elif num > 0: return 'orange'
        else: return 'red'
    if metric == 'PAT Growth':
        if num > 20: return 'green'
        elif num > 10: return 'yellow'
        elif num > 0: return 'orange'
        else: return 'red'
    if metric == 'EPS Growth':
        if num > 20: return 'green'
        elif num > 10: return 'yellow'
        elif num > 0: return 'orange'
        else: return 'red'
    if metric == 'PEG Ratio':
        if num < 1: return 'green'
        elif num < 2: return 'yellow'
        else: return 'red'
    if metric == 'EV/EBITDA':
        if num < 10: return 'green'
        elif num < 20: return 'yellow'
        else: return 'red'
    if metric == 'Dividend Yield':
        if num > 3: return 'green'
        elif num > 1.5: return 'yellow'
        else: return 'red'
    if metric == 'Beta':
        if num < 1: return 'green'
        elif num <= 1.5: return 'yellow'
        else: return 'red'
    if metric == 'Free Cash Flow':
        if num > 0: return 'green'
        else: return 'red'
    if metric == 'Net Profit Margin':
        if num > 20: return 'green'
        elif num > 15: return 'yellow'
        elif num > 10: return 'orange'
        else: return 'red'
    if metric == 'Operating Margin':
        if num > 25: return 'green'
        elif num > 20: return 'yellow'
        elif num > 15: return 'orange'
        else: return 'red'
    if metric == 'Current Ratio':
        if num > 2.0: return 'green'
        elif num > 1.5: return 'yellow'
        else: return 'red'
    if metric == 'Interest Coverage':
        if num > 5: return 'green'
        elif num > 2: return 'yellow'
        else: return 'red'
    if metric == 'Debt/Equity':
        if num < 0.5: return 'green'
        elif num < 1.0: return 'yellow'
        elif num < 2.0: return 'orange'
        else: return 'red'
    return 'gray'


DEBUG_MODE = False

SECTION_HEADINGS = [
    'STRENGTHS', 'WEAKNESSES', 'SECTOR POSITION', 'COMPETITIVE ADVANTAGE',
    'COMPETITIVE ADVANTAGES', 'RISK FACTORS', 'RISK FACTOR', 'AI VERDICT',
    'VERDICT', 'WHY INVEST', 'PEER COMPARISON', 'INVESTMENT THESIS'
]


def parse_peer_ai_response(text):
    sections = {}
    current = None
    buf = []

    for raw_line in text.split('\n'):
        line = raw_line.strip()
        upper = line.upper()

        matched = None
        for heading in SECTION_HEADINGS:
            if upper == heading or upper.startswith(heading + ':') or upper.startswith(heading + ' '):
                matched = heading
                break

        if matched:
            if current and buf:
                if current in ('AI VERDICT', 'VERDICT'):
                    sections[current] = buf
                else:
                    sections[current] = _normalize_items(buf)
            current = matched
            buf = []
            continue

        if line:
            buf.append(line)

    if current and buf:
        if current in ('AI VERDICT', 'VERDICT'):
            sections[current] = buf
        else:
            sections[current] = _normalize_items(buf)

    return sections


def _normalize_items(lines):
    raw = ' '.join(lines)
    raw = re.sub(r'^\d+[\.\)]\s*', '', raw, flags=re.MULTILINE)
    parts = re.split(r'(?:\d+[\.\)]\s*|\n+|,\s*|\s+and\s+|\.\s+)', raw)
    items = []
    for p in parts:
        p = p.strip()
        p = re.sub(r'^[-•*]\s*', '', p)
        if p:
            items.append(p)
    return items


def render_ai_section(title, items, icon='•'):
    st.markdown(f"**{title}**")
    st.markdown("---")
    for item in items:
        st.markdown(f"{icon} {item}")
    st.markdown("")


def render_ai_verdict(verdict, score, reasons):
    verdict_colors = {
        'BUY': ('#ECFDF5', '#00B386', '#065F46'),
        'HOLD': ('#FFFBEB', '#F59E0B', '#92400E'),
        'SELL': ('#FEF2F2', '#FF4757', '#991B1B'),
    }
    v = verdict.upper()
    bg, text, border = verdict_colors.get(v, verdict_colors['HOLD'])

    st.markdown(f"""
    <div style="background:{bg}; border:1px solid {border}; border-radius:12px; padding:16px; margin:12px 0;">
        <div style="font-size:20px; font-weight:800; color:{border}; margin-bottom:4px;">{v}</div>
        <div style="font-size:14px; color:#374151; margin-bottom:8px;">Confidence Score: <b>{score}</b> / 100</div>
    </div>
    """, unsafe_allow_html=True)

    if reasons:
        st.markdown("**Why Invest?**")
        st.markdown("---")
        for r in reasons:
            st.markdown(f"• {r}")


def _render_peer_ai_insights(info, peer_rows, symbol):
    print("="*50)
    print("AI RESPONSE RECEIVED BY UI")
    print("RENDERING AI INSIGHTS TAB")
    print("="*50)

    main_name = info.get('longName', symbol)
    sector = info.get('sector', 'N/A')

    if not st.session_state.get('peer_ai'):
        peer_summary = []
        for peer in peer_rows[:5]:
            name = peer.get('name', peer.get('symbol'))
            score, reasons = _peer_score(peer)
            rating, _ = _peer_rating(score)
            peer_summary.append(f"- {name}: {rating} ({score}/100)")

        peer_insights_prompt = f"""You are a SEBI-registered investment analyst. Compare {main_name} with its sector peers and provide insights.

Stock: {main_name} ({symbol})
Sector: {sector}

Peer Comparison:
{chr(10).join(peer_summary)}

Provide concise AI insights:

STRENGTHS:
1. ...
2. ...

WEAKNESSES:
1. ...
2. ...

SECTOR POSITION:
...

COMPETITIVE ADVANTAGE:
...

RISK FACTORS:
...

AI VERDICT:
...

Keep it under 150 words. Be specific."""

        try:
            from utils.helpers import call_llm

            ai_peer_response = call_llm(
                peer_insights_prompt,
                system_prompt="You are a SEBI-registered research analyst specializing in sector comparison and peer analysis.",
                max_tokens=400
            )
            print("="*50)
            print("AI RESPONSE GENERATED")
            print(ai_peer_response)
            print("="*50)

            st.session_state['peer_ai'] = ai_peer_response
        except Exception as e:
            error_msg = f"Peer insights temporarily unavailable: {str(e)[:80]}"
            st.session_state['peer_ai'] = error_msg
            print(f"AI insights error: {error_msg}")

    ai_text = st.session_state.get('peer_ai', '')
    if not ai_text:
        st.warning("Unable to generate AI Insights currently.")
        st.caption("Please try again later.")
        return

    print(f"Rendering AI insights: {str(ai_text)[:200]}")

    parsed = parse_peer_ai_response(ai_text)

    if not parsed:
        st.warning("AI peer insights temporarily unavailable. Please try again.")
        return

    section_order = [
        'STRENGTHS', 'WEAKNESSES', 'SECTOR POSITION',
        'COMPETITIVE ADVANTAGE', 'COMPETITIVE ADVANTAGES',
        'RISK FACTORS', 'RISK FACTOR', 'WHY INVEST',
        'PEER COMPARISON', 'INVESTMENT THESIS'
    ]
    icon_map = {
        'STRENGTHS': '✓',
        'WEAKNESSES': '✗',
        'SECTOR POSITION': '•',
        'COMPETITIVE ADVANTAGE': '•',
        'COMPETITIVE ADVANTAGES': '•',
        'RISK FACTORS': '•',
        'RISK FACTOR': '•',
        'WHY INVEST': '•',
        'PEER COMPARISON': '•',
        'INVESTMENT THESIS': '•',
    }

    rendered = set()
    for section in section_order:
        if section not in parsed or section in rendered:
            continue
        rendered.add(section)
        items = parsed[section]
        if section in ('AI VERDICT', 'VERDICT'):
            verdict = 'HOLD'
            score = '50'
            reasons = []
            skip_headers = {'REASON', 'WHY INVEST', 'CONFIDENCE', 'SCORE'}

            for item in items:
                upper = item.upper()

                if 'BUY' in upper and len(upper) < 15:
                    verdict = 'BUY'
                    m = re.search(r'(\d+)', item)
                    if m and score == '50':
                        score = m.group(1)
                    continue
                elif 'HOLD' in upper and len(upper) < 15:
                    verdict = 'HOLD'
                    m = re.search(r'(\d+)', item)
                    if m and score == '50':
                        score = m.group(1)
                    continue
                elif 'SELL' in upper and len(upper) < 15:
                    verdict = 'SELL'
                    m = re.search(r'(\d+)', item)
                    if m and score == '50':
                        score = m.group(1)
                    continue

                m = re.search(r'(\d+)', item)
                if m and score == '50':
                    score = m.group(1)

                if any(h in upper for h in skip_headers):
                    continue

                if item.strip():
                    cleaned = re.sub(r'^[-•*]\s*', '', item).strip()
                    if cleaned:
                        reasons.append(cleaned)

            render_ai_verdict(verdict, score, reasons)
        else:
            icon = icon_map.get(section, '•')
            render_ai_section(section, items, icon)

    if DEBUG_MODE and ai_text:
        st.markdown("**Raw AI Response**")
        with st.expander("View Raw AI Response"):
            st.write(ai_text)


def _render_peer_card(peer, score, rating, color):
    color_styles = {
        'green': ('#ECFDF5', '#00B386', '#065F46'),
        'light-green': ('#F0FDF9', '#00B386', '#065F46'),
        'yellow': ('#FFFBEB', '#F59E0B', '#92400E'),
        'orange': ('#FFF7ED', '#F97316', '#9A3412'),
        'red': ('#FEF2F2', '#FF4757', '#991B1B'),
    }
    bg, text, border = color_styles.get(color, color_styles['yellow'])

    price = format_large_number(peer.get('currentPrice'), prefix='₹')
    mcap = format_large_number(peer.get('marketCap'), prefix='')
    pe = f"{peer.get('trailingPE', 0):.1f}x" if peer.get('trailingPE') else 'N/A'
    pb = f"{peer.get('priceToBook', 0):.2f}x" if peer.get('priceToBook') else 'N/A'
    roe = f"{peer.get('returnOnEquity', 0):.1f}%" if peer.get('returnOnEquity') else 'N/A'
    rev = f"{peer.get('revenueGrowth', 0):.1f}%" if peer.get('revenueGrowth') else 'N/A'
    earn = f"{peer.get('earningsGrowth', 0):.1f}%" if peer.get('earningsGrowth') else 'N/A'
    div = f"{peer.get('dividendYield', 0)*100:.2f}%" if peer.get('dividendYield') else 'N/A'

    color_styles = {
        'green': ('#ECFDF5', '#00B386', '#065F46'),
        'light-green': ('#F0FDF9', '#00B386', '#065F46'),
        'yellow': ('#FFFBEB', '#F59E0B', '#92400E'),
        'orange': ('#FFF7ED', '#F97316', '#9A3412'),
        'red': ('#FEF2F2', '#FF4757', '#991B1B'),
    }

    metrics_colors = {
        'P/E': _get_metric_color('P/E Ratio', peer.get('trailingPE')),
        'P/B': _get_metric_color('P/B Ratio', peer.get('priceToBook')),
        'ROE': _get_metric_color('ROE', peer.get('returnOnEquity')),
        'Rev': _get_metric_color('Revenue Growth', peer.get('revenueGrowth')),
        'PAT': _get_metric_color('PAT Growth', peer.get('earningsGrowth')),
        'Div': _get_metric_color('Dividend Yield', peer.get('dividendYield')),
    }

    def _metric_style(metric_key):
        c = metrics_colors.get(metric_key, 'gray')
        if c in color_styles:
            bg, text, border = color_styles[c]
            return f"background:{bg}; color:{border}; border:1px solid {border};"
        return ""

    price = format_large_number(peer.get('currentPrice'), prefix='₹')
    mcap = format_large_number(peer.get('marketCap'), prefix='')
    pe = f"{peer.get('trailingPE', 0):.1f}x" if peer.get('trailingPE') else 'N/A'
    pb = f"{peer.get('priceToBook', 0):.2f}x" if peer.get('priceToBook') else 'N/A'
    roe = f"{peer.get('returnOnEquity', 0):.1f}%" if peer.get('returnOnEquity') else 'N/A'
    rev = f"{peer.get('revenueGrowth', 0):.1f}%" if peer.get('revenueGrowth') else 'N/A'
    earn = f"{peer.get('earningsGrowth', 0):.1f}%" if peer.get('earningsGrowth') else 'N/A'
    div = f"{peer.get('dividendYield', 0)*100:.2f}%" if peer.get('dividendYield') else 'N/A'

    st.markdown(f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        min-width: 220px;
        flex: 1;
    ">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
            <div style="font-size:16px; font-weight:700; color:#1A1A1A;">{peer.get('name', peer.get('symbol'))}</div>
            <div style="
                background: {text};
                color: #FFFFFF;
                padding: 3px 10px;
                border-radius: 20px;
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">{rating}</div>
        </div>
        <div style="display:flex; gap:16px; margin-bottom:12px;">
            <div>
                <div style="font-size:11px; color:#6B7280; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">Price</div>
                <div style="font-size:18px; font-weight:800; color:#1A1A1A;">{price}</div>
            </div>
            <div>
                <div style="font-size:11px; color:#6B7280; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">Mkt Cap</div>
                <div style="font-size:18px; font-weight:800; color:#1A1A1A;">{mcap}</div>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px;">
            <div style="font-size:12px; padding:6px; border-radius:6px; {_metric_style('P/E')}">P/E: <b>{pe}</b></div>
            <div style="font-size:12px; padding:6px; border-radius:6px; {_metric_style('P/B')}">P/B: <b>{pb}</b></div>
            <div style="font-size:12px; padding:6px; border-radius:6px; {_metric_style('ROE')}">ROE: <b>{roe}</b></div>
            <div style="font-size:12px; padding:6px; border-radius:6px; {_metric_style('Rev')}">Rev Growth: <b>{rev}</b></div>
            <div style="font-size:12px; padding:6px; border-radius:6px; {_metric_style('PAT')}">Earn Growth: <b>{earn}</b></div>
            <div style="font-size:12px; padding:6px; border-radius:6px; {_metric_style('Div')}">Div Yield: <b>{div}</b></div>
        </div>
        <div style="
            background: linear-gradient(135deg, {bg}, #FFFFFF);
            border: 1px solid {border};
            border-radius: 12px;
            padding: 10px;
            text-align: center;
        ">
            <div style="font-size:11px; color:#6B7280; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">InvestIQ Score</div>
            <div style="font-size:28px; font-weight:900; color:{border};">{score}</div>
            <div style="font-size:11px; color:#6B7280;">/ 100</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _fetch_peer_data(peers, info, hist):
    peer_rows = []
    success_count = 0
    fail_count = 0

    for peer in peers:
        peer_symbol = get_valid_peer_symbol(peer)
        print("\n" + "="*50)
        print(f"Peer Comparison Logs")
        print(f"Original Peer: {peer}")
        print(f"Formatted Symbol: {peer_symbol}")
        print(f"Fetching....")

        try:
            p_info, p_hist, p_ticker = fetch_stock_data(peer_symbol)
            if p_info is None or p_hist is None:
                print(f"Failed: No data returned for {peer_symbol}")
                fail_count += 1
                continue

            p_metrics = get_fundamental_metrics(p_info, p_ticker)

            p_curr = _safe_float(p_info.get('currentPrice', p_hist['Close'].iloc[-1] if not p_hist.empty else 0))
            p_prev = _safe_float(p_info.get('previousClose', p_hist['Close'].iloc[-2] if len(p_hist) > 1 else p_curr))
            p_change = p_curr - p_prev
            p_change_pct = (p_change / p_prev * 100) if p_prev else 0.0

            peer_rows.append({
                'symbol': peer,
                'name': p_info.get('longName', peer),
                'sector': p_info.get('sector', info.get('sector', 'N/A')),
                'industry': p_info.get('industry', info.get('industry', 'N/A')),
                'currentPrice': p_curr,
                'changePct': p_change_pct,
                'marketCap': _safe_metric(p_metrics.get('marketCap')),
                'trailingPE': _safe_metric(p_metrics.get('trailingPE')),
                'priceToBook': _safe_metric(p_metrics.get('priceToBook')),
                'returnOnEquity': _safe_metric(p_metrics.get('returnOnEquity')),
                'profitMargins': _safe_metric(p_metrics.get('profitMargins')),
                'operatingMargins': _safe_metric(p_metrics.get('operatingMargins')),
                'revenueGrowth': _safe_metric(p_metrics.get('revenueGrowth')),
                'earningsGrowth': _safe_metric(p_metrics.get('earningsGrowth')),
                'dividendYield': _safe_metric(p_metrics.get('dividendYield')),
                'beta': _safe_metric(p_metrics.get('beta')),
                'debtToEquity': _safe_metric(p_metrics.get('debtToEquity')),
                'currentRatio': _safe_metric(p_metrics.get('currentRatio')),
                'enterpriseToEbitda': _safe_metric(p_metrics.get('enterpriseToEbitda')),
                'pegRatio': _safe_metric(p_metrics.get('pegRatio')),
                'interestCoverage': _safe_metric(p_metrics.get('interestCoverage')),
                'freeCashflow': _safe_metric(p_metrics.get('freeCashflow')),
                'bookValue': _safe_metric(p_metrics.get('bookValue')),
                'averageVolume': _safe_metric(p_metrics.get('averageVolume')),
                'fiftyTwoWeekHigh': _safe_metric(p_metrics.get('fiftyTwoWeekHigh')),
                'fiftyTwoWeekLow': _safe_metric(p_metrics.get('fiftyTwoWeekLow')),
            })
            print(f"Success.")
            success_count += 1
        except Exception as e:
            print(f"Failed: {str(e)[:60]}")
            fail_count += 1
            continue

    print(f"\nPeer Fetch Summary: {success_count} success, {fail_count} failed")
    print("="*50)
    return peer_rows


def _parse_ai_response(text):
    result = {
        'verdict': 'HOLD',
        'confidence': '50',
        'target': 'N/A',
        'stop_loss': 'N/A',
        'basis': [],
        'reasons': [],
        'risks': [],
        'summary': '',
    }

    if not text:
        return result

    lines_text = text.split('\n')
    current_section = None

    for line in lines_text:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        upper = line_stripped.upper()

        if upper.startswith('VERDICT:'):
            result['verdict'] = line_stripped.split(':', 1)[1].strip().upper()
            if result['verdict'] not in ['BUY', 'SELL', 'HOLD']:
                result['verdict'] = 'HOLD'
        elif upper.startswith('CONFIDENCE:'):
            raw = line_stripped.split(':', 1)[1].strip()
            if '/' in raw:
                result['confidence'] = raw.split('/')[0]
            elif '%' in raw:
                result['confidence'] = raw.replace('%', '')
            else:
                digits = ''.join(filter(str.isdigit, raw))
                if digits:
                    result['confidence'] = digits
        elif upper.startswith('TARGET PRICE:') or (upper.startswith('TARGET:') and not upper.startswith('TARGET PRICE:')):
            result['target'] = line_stripped.split(':', 1)[1].strip()
        elif upper.startswith('STOP LOSS:'):
            result['stop_loss'] = line_stripped.split(':', 1)[1].strip()
        elif upper.startswith('BASIS:') or upper.startswith('METHODOLOGY:'):
            current_section = 'basis'
        elif upper.startswith('KEY REASONS') or upper.startswith('REASONS') or upper.startswith('WHY THIS VERDICT'):
            current_section = 'reasons'
        elif upper.startswith('KEY RISKS') or upper.startswith('RISKS'):
            current_section = 'risks'
        elif upper.startswith('FINAL SUMMARY') or upper.startswith('SUMMARY'):
            current_section = 'summary'
        elif line_stripped.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•')):
            item = line_stripped.lstrip('12345.-• ').strip()
            if item:
                if current_section == 'basis':
                    result['basis'].append(item)
                elif current_section == 'reasons':
                    result['reasons'].append(item)
                elif current_section == 'risks':
                    result['risks'].append(item)
        elif current_section == 'summary' and line_stripped:
            result['summary'] += (' ' if result['summary'] else '') + line_stripped

    return result


def _render_ai_verdict_card(data, symbol):
    print("="*60)
    print(f"[AI RENDER] _render_ai_verdict_card START for {symbol}")
    print(f"[AI RENDER] Input data keys: {list(data.keys()) if data else 'None'}")
    print(f"[AI RENDER] verdict={data.get('verdict')}, confidence={data.get('confidence')}, target={data.get('target')}, stop_loss={data.get('stop_loss')}")
    print(f"[AI RENDER] basis count={len(data.get('basis', []))}, reasons count={len(data.get('reasons', []))}, risks count={len(data.get('risks', []))}")
    print("="*60)

    verdict = data.get('verdict', 'HOLD')
    confidence = data.get('confidence', '50')
    target = data.get('target', 'N/A')
    stop_loss = data.get('stop_loss', 'N/A')
    basis = data.get('basis', [])
    reasons = data.get('reasons', [])
    risks = data.get('risks', [])
    summary = data.get('summary', '')

    print(f"[AI RENDER] Step 1: Variables extracted")

    confidence_display = confidence
    if confidence_display.isdigit():
        confidence_display = f"{confidence_display}/100"

    print(f"[AI RENDER] Step 2: Confidence display prepared: {confidence_display}")

    color_map = {
        'BUY': ('#ECFDF5', '#00B386', '#065F46', 'BUY'),
        'HOLD': ('#FFFBEB', '#F59E0B', '#92400E', 'HOLD'),
        'SELL': ('#FEF2F2', '#FF4757', '#991B1B', 'SELL'),
    }
    bg, text, border, label = color_map.get(verdict, color_map['HOLD'])

    print(f"[AI RENDER] Step 3: Color map prepared, label={label}")

    try:
        print(f"[AI RENDER] Step 4: Rendering title")
        st.markdown("---")
        st.markdown("#### AI Investment Verdict")
        print(f"[AI RENDER] Step 4: Title rendered")

        print(f"[AI RENDER] Step 5: Rendering metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Verdict", label)
        with col2:
            st.metric("Confidence", confidence_display)
        with col3:
            st.metric("Target Price", target)

        col4, col5 = st.columns(2)
        with col4:
            st.metric("Stop Loss", stop_loss)
        with col5:
            st.metric("Risk Profile", data.get('risk_level', 'Medium'))
        print(f"[AI RENDER] Step 5: Metrics rendered")

        if basis:
            print(f"[AI RENDER] Step 6: Rendering basis ({len(basis)} items)")
            st.markdown("**Methodology / Basis**")
            for b in basis[:5]:
                st.markdown(f"- {b}")
            print(f"[AI RENDER] Step 6: Basis rendered")

        if reasons:
            print(f"[AI RENDER] Step 7: Rendering reasons ({len(reasons)} items)")
            st.markdown("**Why This Verdict**")
            for r in reasons[:5]:
                st.markdown(f"- {r}")
            print(f"[AI RENDER] Step 7: Reasons rendered")

        if risks:
            print(f"[AI RENDER] Step 8: Rendering risks ({len(risks)} items)")
            st.markdown("**Key Risks**")
            for r in risks[:4]:
                st.markdown(f"- {r}")
            print(f"[AI RENDER] Step 8: Risks rendered")

        if summary:
            print(f"[AI RENDER] Step 9: Rendering summary")
            st.markdown("**Final Summary**")
            st.markdown(f"{summary}")
            print(f"[AI RENDER] Step 9: Summary rendered")

        st.markdown("---")
        print(f"[AI RENDER] Step 10: Final separator rendered")

    except Exception as e:
        print(f"[AI RENDER] ERROR during rendering: {str(e)}")
        import traceback
        traceback.print_exc()
        st.error(f"Rendering error: {str(e)}")

    print(f"[AI RENDER] _render_ai_verdict_card COMPLETE for {symbol}")
    print("="*60)


def _build_ai_prompt(info, symbol, peer_rows, score_data, technical_text=""):
    company_name = info.get("name", symbol)
    sector = info.get("sector", "N/A")
    curr_price = info.get("currentPrice", 0)

    pe = info.get('trailingPE')
    pb = info.get('priceToBook')
    roe = info.get('returnOnEquity')
    profit_margin = info.get('profitMargins')
    operating_margin = info.get('operatingMargins')
    revenue_growth = info.get('revenueGrowth')
    earnings_growth = info.get('earningsGrowth')
    eps_growth = info.get('epsGrowth')
    dividend_yield = info.get('dividendYield')
    debt_to_equity = info.get('debtToEquity')
    current_ratio = info.get('currentRatio')
    interest_coverage = info.get('interestCoverage')
    free_cashflow = info.get('freeCashflow')
    beta = info.get('beta')
    book_value = info.get('bookValue')
    market_cap = info.get('marketCap')

    fundamentals_text = f"""
P/E Ratio: {pe if pe is not None else 'N/A'}
P/B Ratio: {pb if pb is not None else 'N/A'}
ROE: {roe if roe is not None else 'N/A'}%
Net Profit Margin: {profit_margin if profit_margin is not None else 'N/A'}%
Operating Margin: {operating_margin if operating_margin is not None else 'N/A'}%
Revenue Growth: {revenue_growth if revenue_growth is not None else 'N/A'}%
Earnings Growth: {earnings_growth if earnings_growth is not None else 'N/A'}%
EPS Growth: {eps_growth if eps_growth is not None else 'N/A'}%
Dividend Yield: {dividend_yield if dividend_yield is not None else 'N/A'}%
Debt to Equity: {debt_to_equity if debt_to_equity is not None else 'N/A'}
Current Ratio: {current_ratio if current_ratio is not None else 'N/A'}
Interest Coverage: {interest_coverage if interest_coverage is not None else 'N/A'}
Free Cash Flow: {free_cashflow if free_cashflow is not None else 'N/A'}
Beta: {beta if beta is not None else 'N/A'}
Book Value: {book_value if book_value is not None else 'N/A'}
Market Cap: {market_cap if market_cap is not None else 'N/A'}
"""

    peer_text = "Peer Comparison: No peer data available."
    if peer_rows:
        peer_text = "Peer Comparison (Sector Peers):\n"
        for peer in peer_rows[:5]:
            name = peer.get('name', peer.get('symbol', 'N/A'))
            p_pe = peer.get('trailingPE')
            p_pb = peer.get('priceToBook')
            p_roe = peer.get('returnOnEquity')
            p_rev = peer.get('revenueGrowth')
            p_div = peer.get('dividendYield')
            p_de = peer.get('debtToEquity')
            peer_text += (
                f"- {name}: P/E {f'{p_pe:.1f}' if p_pe is not None else 'N/A'}, "
                f"P/B {f'{p_pb:.2f}' if p_pb is not None else 'N/A'}, "
                f"ROE {f'{p_roe:.1f}%' if p_roe is not None else 'N/A'}, "
                f"Rev Growth {f'{p_rev:.1f}%' if p_rev is not None else 'N/A'}, "
                f"Div {f'{p_div*100:.2f}%' if p_div is not None else 'N/A'}, "
                f"D/E {f'{p_de:.2f}' if p_de is not None else 'N/A'}\n"
            )

    score_text = "Stock Health Score: N/A"
    if score_data:
        total = score_data.get('total_score', 'N/A')
        rating = score_data.get('rating', 'N/A')
        cats = score_data.get('categories', {})
        score_text = f"Stock Health Score: {total}/100 ({rating})\n"
        for cat_name, cat_data in cats.items():
            score_text += f"- {cat_name}: {cat_data.get('score', 0)}/{cat_data.get('max', 20)} ({cat_data.get('reason', 'N/A')})\n"

    prompt = f"""You are a SEBI-registered investment analyst. Analyze this NSE stock and give a structured investment verdict.

Stock: {company_name} ({symbol})
Sector: {sector}
Current Price: ₹{curr_price:.2f}

Fundamental Metrics:
{fundamentals_text}

{score_text}

{peer_text}

Technical Indicators:
{technical_text}

Provide a structured investment verdict using exactly this format:

VERDICT: [BUY / HOLD / SELL]
CONFIDENCE: [X/100]
TARGET: [₹X,XXX]
STOP LOSS: [₹X,XXX]

METHODOLOGY:
- Valuation vs peers
- Technical trend
- Fundamentals
- Stock score

WHY THIS VERDICT:
- Reason 1
- Reason 2
- Reason 3

KEY RISKS:
- Risk 1
- Risk 2

FINAL SUMMARY:
- One short paragraph explaining why this verdict was given.

Total response must be under 200 words. Be specific with numbers. Base your verdict on peer comparison, sector averages, fundamentals, technical trend, and stock health score. Do not include any market sources or analyst recommendations."""

    return prompt


def _render_peer_comparison_section(info, symbol):
    st.markdown("---")
    st.markdown("#### 🏆 Peer Comparison")

    peers = _get_peers(symbol)
    if not peers:
        st.caption("Peer comparison not available for this stock.")
        return

    with st.spinner("Fetching peer stocks..."):
        peer_rows = _fetch_peer_data(peers, info, None)

    total_peers = len(peers)
    loaded_peers = len(peer_rows)

    if loaded_peers == 0:
        st.caption("No peer data available currently. Please try again later.")
        return
    elif loaded_peers < total_peers:
        st.caption(f"{loaded_peers} out of {total_peers} peer stocks loaded successfully.")
    else:
        st.caption(f"All {total_peers} peer stocks loaded successfully.")

    main_row = {
        'symbol': symbol,
        'name': info.get('longName', symbol),
        'sector': info.get('sector', 'N/A'),
        'industry': info.get('industry', 'N/A'),
        'currentPrice': info.get('currentPrice', 0),
        'changePct': 0.0,
        'marketCap': _safe_metric(info.get('marketCap')),
        'trailingPE': _safe_metric(info.get('trailingPE')),
        'priceToBook': _safe_metric(info.get('priceToBook')),
        'returnOnEquity': _safe_metric(info.get('returnOnEquity')),
        'profitMargins': _safe_metric(info.get('profitMargins')),
        'operatingMargins': _safe_metric(info.get('operatingMargins')),
        'revenueGrowth': _safe_metric(info.get('revenueGrowth')),
        'earningsGrowth': _safe_metric(info.get('earningsGrowth')),
        'dividendYield': _safe_metric(info.get('dividendYield')),
        'beta': _safe_metric(info.get('beta')),
        'debtToEquity': _safe_metric(info.get('debtToEquity')),
        'currentRatio': _safe_metric(info.get('currentRatio')),
        'enterpriseToEbitda': _safe_metric(info.get('enterpriseToEbitda')),
        'pegRatio': _safe_metric(info.get('pegRatio')),
        'interestCoverage': _safe_metric(info.get('interestCoverage')),
        'freeCashflow': _safe_metric(info.get('freeCashflow')),
        'bookValue': _safe_metric(info.get('bookValue')),
        'averageVolume': _safe_metric(info.get('averageVolume')),
        'fiftyTwoWeekHigh': _safe_metric(info.get('fiftyTwoWeekHigh')),
        'fiftyTwoWeekLow': _safe_metric(info.get('fiftyTwoWeekLow')),
    }

    all_rows = [main_row] + peer_rows
    sector = info.get('sector', 'N/A')
    st.markdown(f"**{sector} Sector Peers**")

    peer_tabs = st.tabs(["Scoreboard", "Peer Cards"])

    with peer_tabs[0]:
        metrics = [
            ('Market Cap', 'marketCap', ''),
            ('P/E Ratio', 'trailingPE', 'x'),
            ('P/B Ratio', 'priceToBook', 'x'),
            ('ROE', 'returnOnEquity', '%'),
            ('Revenue Growth', 'revenueGrowth', '%'),
            ('PAT Growth', 'earningsGrowth', '%'),
            ('Dividend Yield', 'dividendYield', '%'),
            ('Debt/Equity', 'debtToEquity', 'x'),
        ]

        for metric_name, key, suffix in metrics:
            vals = [row.get(key) for row in all_rows if row.get(key) is not None]
            avgs = sum(vals) / len(vals) if vals else None

            st.markdown(f"**{metric_name}**")
            cols = st.columns(len(all_rows) + 1)

            with cols[0]:
                avg_display = format_large_number(avgs, prefix='') if avgs is not None else 'N/A'
                if suffix == 'x' and avgs is not None:
                    avg_display = f"{avgs:.2f}x"
                elif suffix == '%' and avgs is not None:
                    avg_display = f"{avgs:.1f}%"
                st.markdown(f"""
                <div style="text-align:center; padding:10px; background:#F8FAF9; border-radius:10px; border:1px solid #E5E7EB;">
                    <div style="font-size:11px; color:#6B7280; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">Sector Avg</div>
                    <div style="font-size:18px; font-weight:800; color:#1A1A1A;">{avg_display}</div>
                </div>
                """, unsafe_allow_html=True)

            for idx, row in enumerate(all_rows):
                with cols[idx + 1]:
                    val = row.get(key)
                    display = 'N/A'
                    color = 'gray'
                    if val is not None:
                        if key == 'marketCap':
                            display = format_large_number(val, prefix='')
                            color, _ = _fundamental_color_and_label('Market Cap', val)
                        elif suffix == 'x':
                            display = f"{val:.2f}x"
                            color, _ = _fundamental_color_and_label(metric_name, val)
                        elif suffix == '%':
                            display = f"{val:.1f}%"
                            color, _ = _fundamental_color_and_label(metric_name, val)
                        else:
                            display = f"{val:.2f}"
                            color, _ = _fundamental_color_and_label(metric_name, val)

                        if avgs is not None:
                            if key in ['trailingPE', 'priceToBook', 'debtToEquity']:
                                if val < avgs * 0.9: color = 'green'
                                elif val > avgs * 1.1: color = 'red'
                                else: color = 'yellow'
                            elif key in ['returnOnEquity', 'profitMargins', 'operatingMargins', 'revenueGrowth', 'earningsGrowth']:
                                if val > avgs * 1.1: color = 'green'
                                elif val < avgs * 0.9: color = 'red'
                                else: color = 'yellow'
                            elif key == 'dividendYield':
                                if val > avgs * 1.2: color = 'green'
                                elif val < avgs * 0.8: color = 'red'
                                else: color = 'yellow'
                            elif key == 'marketCap':
                                 if val > avgs * 1.5: color = 'blue'
                                 elif val < avgs * 0.5: color = 'gray'
                                 else: color = 'yellow'

                            color_styles = {
                                'green': ('#ECFDF5', '#00B386', '#065F46'),
                                'light-green': ('#F0FDF9', '#00B386', '#065F46'),
                                'yellow': ('#FFFBEB', '#F59E0B', '#92400E'),
                                'orange': ('#FFF7ED', '#F97316', '#9A3412'),
                                'red': ('#FEF2F2', '#FF4757', '#991B1B'),
                                'blue': ('#EFF6FF', '#3B82F6', '#1E40AF'),
                                'gray': ('#F9FAFB', '#6B7280', '#374151'),
                            }
                            card_bg, card_text, card_border = color_styles.get(color, color_styles['gray'])
                            
                            st.markdown(f"""
                            <div style="text-align:center; padding:8px; background:{card_bg}; border-radius:8px; border:1px solid {card_border};">
                                <div style="font-size:10px; color:{card_text}; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">{row.get('symbol')}</div>
                                <div style="font-size:16px; font-weight:800; color:{card_border};">{display}</div>
                            </div>
                            """, unsafe_allow_html=True)

    with peer_tabs[1]:
        st.markdown("<div style='display:flex; overflow-x:auto; gap:16px; padding-bottom:8px;'>", unsafe_allow_html=True)
        for peer in all_rows:
            score, reasons = _peer_score(peer)
            rating, color = _peer_rating(score)
            _render_peer_card(peer, score, rating, color)
        st.markdown("</div>", unsafe_allow_html=True)

    return peer_rows
