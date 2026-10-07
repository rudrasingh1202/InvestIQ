"""My Portfolio UI for InvestIQ - Clean Rebuild."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

import streamlit as st
import yfinance as yf

from modules.portfolio import (
    add_holding,
    authenticate_user,
    calculate_portfolio_health,
    delete_holding,
    get_holdings,
    register_user,
    update_holding,
)

try:
    from ui.stock_page import format_stock_symbol
except ImportError:
    def format_stock_symbol(symbol: str) -> str:
        sym = symbol.strip().upper()
        if sym.endswith(".NS") or sym.endswith(".BO"):
            return sym
        return f"{sym}.NS"


def _inject_portfolio_styles() -> None:
    """Inject CSS styles for portfolio UI."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        .portfolio-wrapper {
            font-family: 'Inter', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 16px 40px;
        }

        /* Top header bar */
        .portfolio-topbar {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding: 8px 0 4px 0;
            gap: 12px;
        }
        .portfolio-user-chip {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            color: #374151;
            font-weight: 600;
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            padding: 6px 14px;
            border-radius: 999px;
        }

        /* Portfolio header */
        .portfolio-header {
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid #E5E7EB;
        }
        .portfolio-title {
            font-size: 28px;
            font-weight: 800;
            color: #111827;
            letter-spacing: -0.5px;
            margin: 0;
        }
        .portfolio-subtitle {
            font-size: 14px;
            color: #6B7280;
            margin-top: 6px;
        }

        /* Summary metrics grid */
        .summary-grid {
            display: flex;
            gap: 16px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .summary-card {
            flex: 1;
            min-width: 150px;
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 14px;
            padding: 18px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            transition: transform .15s ease, box-shadow .15s ease;
        }
        .summary-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        }
        .summary-label {
            font-size: 11px;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .summary-value {
            font-size: 22px;
            font-weight: 800;
            color: #111827;
            letter-spacing: -0.3px;
        }
        .summary-value.green { color: #00B386; }
        .summary-value.red { color: #FF4757; }

        /* Health widget */
        .health-widget {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .health-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .health-score-circle {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 5px solid;
            margin: 0 auto 12px;
        }
        .health-score-number {
            font-size: 32px;
            font-weight: 900;
            line-height: 1;
        }
        .health-score-total {
            font-size: 11px;
            font-weight: 600;
            opacity: 0.8;
        }
        .health-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }

        /* Market widget */
        .market-widget {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            height: 100%;
        }
        .market-status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #00B386;
            display: inline-block;
            margin-right: 6px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* Holdings section */
        .holdings-section { margin-top: 20px; }
        .holdings-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }
        .holdings-title {
            font-size: 18px;
            font-weight: 700;
            color: #111827;
        }
        .holding-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            transition: transform .12s ease, box-shadow .12s ease;
        }
        .holding-card:hover { box-shadow: 0 6px 18px rgba(0,0,0,0.05); }
        .holding-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 12px;
        }
        .holding-symbol {
            font-size: 16px;
            font-weight: 700;
            color: #111827;
        }
        .holding-name {
            font-size: 12px;
            color: #6B7280;
            margin-top: 2px;
        }
        .holding-date {
            font-size: 11px;
            color: #9CA3AF;
            margin-top: 4px;
        }
        .holding-metrics {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }
        .holding-metric { font-size: 13px; color: #4B5563; }
        .holding-metric strong { color: #111827; }
        .holding-actions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }

        /* Add holding section */
        .add-section {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            margin-bottom: 20px;
        }
        .add-section-title {
            font-size: 15px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 12px;
        }

        /* Insights */
        .insight-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 14px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .insight-label {
            font-size: 11px;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.7px;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .insight-value {
            font-size: 20px;
            font-weight: 800;
            color: #111827;
        }
        .insight-value.green { color: #00B386; }
        .insight-value.red { color: #FF4757; }
        .insight-delta {
            font-size: 12px;
            color: #6B7280;
            margin-top: 4px;
        }

        /* Auth page */
        .auth-wrapper {
            min-height: 70vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px 16px;
        }
        .auth-card {
            width: 100%;
            max-width: 420px;
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 20px;
            padding: 36px;
            box-shadow: 0 8px 28px rgba(0,0,0,0.06);
        }
        .auth-icon-row {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 14px;
        }
        .auth-icon {
            width: 48px;
            height: 48px;
            border-radius: 14px;
            background: linear-gradient(135deg, #ECFDF5, #FFFFFF);
            border: 1px solid #00B386;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            color: #065F46;
        }
        .auth-title {
            font-size: 22px;
            font-weight: 800;
            color: #111827;
            text-align: center;
            margin-bottom: 6px;
        }
        .auth-subtitle {
            font-size: 13px;
            color: #6B7280;
            text-align: center;
            margin-bottom: 24px;
            line-height: 1.5;
        }

        /* Empty state */
        .empty-state { text-align: center; padding: 48px 20px; }
        .empty-icon { font-size: 48px; margin-bottom: 12px; }
        .empty-title {
            font-size: 18px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 8px;
        }
        .empty-text { font-size: 14px; color: #6B7280; }

        /* Logout button */
        #portfolio_logout_btn > button {
            background-color: #F9FAFB;
            color: #6B7280;
            border: 1px solid #E5E7EB;
            border-radius: 999px;
            padding: 6px 16px;
            font-weight: 600;
            font-size: 13px;
            transition: all 0.2s;
        }
        #portfolio_logout_btn > button:hover {
            background-color: #FEF2F2;
            color: #DC2626;
            border-color: #FECACA;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_auth_page() -> None:
    """Render the login/register page."""
    _inject_portfolio_styles()

    import os as _os
    if not _os.getenv("MONGODB_URI"):
        st.markdown(
            """
            <div class="auth-wrapper">
                <div class="auth-card">
                    <div class="auth-icon-row"><div class="auth-icon">🔐</div></div>
                    <div class="auth-title">My Portfolio</div>
                    <div class="auth-subtitle">MongoDB configuration required</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.warning(
            "MongoDB is not configured. Please set the **MONGODB_URI** environment variable "
            "in your `.env` file to enable the Portfolio module."
        )
        st.info(
            "Add the following to your `.env` file:\n\n"
            "```\n"
            "MONGODB_URI=your_mongodb_connection_string\n"
            "MONGODB_DATABASE=investiq\n"
            "MONGODB_USERS_COLLECTION=users\n"
            "MONGODB_PORTFOLIO_COLLECTION=portfolios\n"
            "```"
        )
        return

    st.markdown(
        """
        <div class="auth-wrapper">
            <div class="auth-card">
                <div class="auth-icon-row"><div class="auth-icon">💼</div></div>
                <div class="auth-title">My Portfolio</div>
                <div class="auth-subtitle">Track your investments. Monitor performance. Understand your portfolio.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    ok, user_id, status = authenticate_user(username, password)
                    if ok:
                        st.session_state["portfolio_user_id"] = user_id
                        st.session_state["portfolio_username"] = username
                        st.success("Login successful!")
                        time.sleep(0.5)
                        st.rerun()
                    elif status == "db_unavailable":
                        st.error("Database connection unavailable. Please try again.")
                    else:
                        st.error("Incorrect username or password.")

    with tab_register:
        with st.form("register_form", clear_on_submit=True):
            new_user = st.text_input("Username", key="reg_user")
            new_pass = st.text_input("Password", type="password", key="reg_pass")
            confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm")
            submitted = st.form_submit_button("Register", type="primary", use_container_width=True)
            if submitted:
                if not new_user or not new_pass or not confirm_pass:
                    st.error("All fields are required.")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(new_user, new_pass)
                    if ok:
                        st.success("Registration successful! Please login.")
                    else:
                        st.error(msg)


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_current_price(symbol: str) -> float | None:
    """Fetch current price from yfinance with caching."""
    try:
        formatted = format_stock_symbol(symbol)
        ticker = yf.Ticker(formatted)
        hist = ticker.history(period="5d")
        if hist is not None and not hist.empty:
            price = float(hist["Close"].iloc[-1])
            return price
        info = ticker.info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if price:
            return float(price)
    except Exception:
        pass
    return None


def _get_current_price(symbol: str) -> float | None:
    """Get current price with session caching."""
    cache_key = f"price_{symbol}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    price = _fetch_current_price(symbol)
    if price is not None:
        st.session_state[cache_key] = price
    return price


def _render_holding_card(holding: dict[str, Any], user_id: str) -> None:
    """Render a single holding card with metrics and actions."""
    symbol = holding.get("symbol", "")
    stock_name = holding.get("stock_name", symbol)
    buy_price = holding.get("buy_price", 0.0)
    quantity = holding.get("quantity", 0)
    buy_date = holding.get("buy_date", "")
    holding_id = holding.get("_id", "")

    current_price = _get_current_price(symbol)
    invested = buy_price * quantity
    current_value = (current_price * quantity) if current_price is not None else None
    pnl = (current_value - invested) if current_value is not None else None
    pnl_pct = ((current_price - buy_price) / buy_price * 100) if current_price is not None and buy_price > 0 else None

    pnl_color = "#00B386" if (pnl is not None and pnl >= 0) else "#FF4757"
    pnl_sign = "+" if (pnl is not None and pnl >= 0) else ""
    pnl_pct_sign = "+" if (pnl_pct is not None and pnl_pct >= 0) else ""

    st.markdown(
        f"""
        <div class="holding-card">
            <div class="holding-header">
                <div>
                    <div class="holding-symbol">{symbol}</div>
                    <div class="holding-name">{stock_name}</div>
                    <div class="holding-date">{buy_date}</div>
                </div>
            </div>
            <div class="holding-metrics">
                <div class="holding-metric"><strong>Buy:</strong> ₹{buy_price:,.2f}</div>
                <div class="holding-metric"><strong>Qty:</strong> {quantity}</div>
                <div class="holding-metric"><strong>Current:</strong> {"₹{:,.2f}".format(current_price) if current_price is not None else "N/A"}</div>
                <div class="holding-metric" style="color:{pnl_color};font-weight:700;">
                    <strong>P&L:</strong> {pnl_sign if pnl is not None else ""}{"₹{:,.0f}".format(pnl) if pnl is not None else "N/A"}
                </div>
                <div class="holding-metric" style="color:{pnl_color};">
                    <strong>P&L %:</strong> {pnl_pct_sign if pnl_pct is not None else ""}{"{:.2f}%".format(pnl_pct) if pnl_pct is not None else "N/A"}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    act1, act2, act3 = st.columns(3)
    with act1:
        if st.button("Edit", key=f"edit_btn_{holding_id}", use_container_width=True):
            st.session_state[f"editing_{holding_id}"] = True
            st.rerun()
    with act2:
        if st.button("Delete", key=f"del_{holding_id}", use_container_width=True):
            ok, msg = delete_holding(holding_id, user_id)
            if ok:
                _invalidate_price_cache()
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    with act3:
        st.write("")

    if st.session_state.get(f"editing_{holding_id}"):
        with st.form(key=f"edit_form_{holding_id}"):
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                e_symbol = st.text_input("Symbol", value=symbol, key=f"esym_{holding_id}")
                e_name = st.text_input("Stock Name", value=stock_name, key=f"ename_{holding_id}")
            with e_col2:
                e_price = st.number_input("Buy Price", value=float(buy_price), min_value=0.01, step=0.01, key=f"eprice_{holding_id}")
                e_qty = st.number_input("Quantity", value=int(quantity), min_value=1, step=1, key=f"eqty_{holding_id}")
            e_date = st.date_input("Buy Date", value=datetime.strptime(buy_date, "%Y-%m-%d").date() if buy_date else datetime.now().date(), key=f"edate_{holding_id}")
            save_clicked = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
            cancel_clicked = st.form_submit_button("Cancel", use_container_width=True)
            if cancel_clicked:
                st.session_state[f"editing_{holding_id}"] = False
                st.rerun()
            if save_clicked:
                ok, msg = update_holding(
                    holding_id, user_id,
                    e_symbol, e_name, e_price, e_qty, e_date.strftime("%Y-%m-%d")
                )
                if ok:
                    _invalidate_price_cache()
                    st.session_state[f"editing_{holding_id}"] = False
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


def _invalidate_price_cache() -> None:
    """Clear all price caches from session state."""
    keys_to_del = [k for k in st.session_state if k.startswith("price_")]
    for k in keys_to_del:
        del st.session_state[k]


def _render_add_holding(user_id: str) -> None:
    """Render the add holding form."""
    with st.expander("➕ Add Holding", expanded=False):
        with st.form("add_holding_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                symbol = st.text_input("Stock Symbol", placeholder="e.g. TCS, INFY, RELIANCE")
                stock_name = st.text_input("Stock Name", placeholder="e.g. Tata Consultancy Services")
            with c2:
                buy_price = st.number_input("Buy Price (₹)", min_value=0.01, step=0.01)
                quantity = st.number_input("Quantity", min_value=1, step=1)
            buy_date = st.date_input("Buy Date", value=datetime.now().date())
            submitted = st.form_submit_button("Add Holding", type="primary", use_container_width=True)
            if submitted:
                if not symbol or not stock_name:
                    st.error("Stock symbol and name are required.")
                else:
                    ok, msg = add_holding(
                        user_id, symbol, stock_name,
                        buy_price, quantity, buy_date.strftime("%Y-%m-%d")
                    )
                    if ok:
                        _invalidate_price_cache()
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


def _render_summary(holdings: list[dict[str, Any]]) -> None:
    """Render portfolio summary metrics."""
    total_invested = 0.0
    total_current = 0.0
    for h in holdings:
        bp = h.get("buy_price", 0.0)
        qty = h.get("quantity", 0)
        total_invested += bp * qty
        cp = _get_current_price(h.get("symbol", ""))
        if cp is not None:
            total_current += cp * qty

    pnl = total_current - total_invested
    pnl_pct = (pnl / total_invested * 100) if total_invested > 0 else 0.0

    pnl_sign = "+" if pnl >= 0 else ""
    pct_sign = "+" if pnl_pct >= 0 else ""
    pnl_class = "green" if pnl >= 0 else "red"
    pct_class = "green" if pnl_pct >= 0 else "red"

    st.markdown(
        f"""
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-label">Total Invested</div>
                <div class="summary-value">₹{total_invested:,.0f}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Current Value</div>
                <div class="summary-value">₹{total_current:,.0f}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Total P&L</div>
                <div class="summary-value {pnl_class}">{pnl_sign}₹{pnl:,.0f}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Return</div>
                <div class="summary-value {pct_class}">{pct_sign}{pnl_pct:.2f}%</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Holdings</div>
                <div class="summary-value">{len(holdings)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_insights(holdings: list[dict[str, Any]]) -> None:
    """Render portfolio insights."""
    if not holdings:
        return

    enriched = []
    for h in holdings:
        cp = _get_current_price(h.get("symbol", ""))
        invested = h.get("buy_price", 0) * h.get("quantity", 0)
        current = (cp * h.get("quantity", 0)) if cp is not None else None
        pnl = (current - invested) if current is not None else None
        enriched.append({
            "symbol": h.get("symbol", ""),
            "stock_name": h.get("stock_name", h.get("symbol", "")),
            "invested": invested,
            "current": current if current is not None else invested,
            "pnl": pnl if pnl is not None else 0.0,
            "quantity": h.get("quantity", 0),
        })

    total_current = sum(item["current"] for item in enriched)
    top = max(enriched, key=lambda x: x["pnl"])
    worst = min(enriched, key=lambda x: x["pnl"])
    largest = max(enriched, key=lambda x: x["current"])
    top_weight = largest["current"] / total_current if total_current > 0 else 0.0
    profitable = sum(1 for item in enriched if item["pnl"] > 0)
    loss_making = sum(1 for item in enriched if item["pnl"] < 0)

    st.markdown(
        """
        <div style="margin-top: 20px;">
            <div class="holdings-title">📋 Portfolio Insights</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Top Performer", f"{top['symbol']}", f"+₹{top['pnl']:,.0f}")
    with c2:
        st.metric("Worst Performer", f"{worst['symbol']}", f"₹{worst['pnl']:,.0f}")
    with c3:
        st.metric("Largest Holding", f"{largest['symbol']}", f"{top_weight*100:.1f}%")

    c4, c5, c6 = st.columns(3)
    with c4:
        st.metric("Profitable", str(profitable))
    with c5:
        st.metric("Loss-Making", str(loss_making))
    with c6:
        st.metric("Holdings", str(len(holdings)))


def _render_health_section(holdings: list[dict[str, Any]]) -> None:
    """Render the portfolio health score section."""
    current_prices = {}
    for h in holdings:
        cp = _get_current_price(h.get("symbol", ""))
        if cp is not None:
            current_prices[h.get("symbol", "")] = cp
    result = calculate_portfolio_health(holdings, current_prices=current_prices)
    score = result["score"]
    risk_level = result["risk_level"]
    risk_color = result["risk_color"]
    strengths = result.get("strengths", [])
    improvements = result.get("improvements", [])

    color_map = {
        "green": ("#ECFDF5", "#00B386", "#065F46"),
        "yellow": ("#FFFBEB", "#F59E0B", "#92400E"),
        "red": ("#FEF2F2", "#FF4757", "#991B1B"),
        "gray": ("#F9FAFB", "#6B7280", "#374151"),
    }
    bg, text, border = color_map.get(risk_color, color_map["gray"])

    st.markdown(
        f"""
        <div class="health-widget" style="
            background: linear-gradient(135deg, {bg}, #FFFFFF);
            border-color: {border};
            margin-top: 20px;
        ">
            <div class="health-header">
                <div style="font-size: 16px; font-weight: 700; color: #111827;">
                    🩺 Portfolio Health Score
                </div>
                <span class="health-badge" style="background: {text}; color: #FFFFFF;">{risk_level}</span>
            </div>
            <div class="health-score-circle" style="border-color: {text}; color: {border};">
                <div class="health-score-number" style="color:{border};">{score}</div>
                <div class="health-score-total">/ 100</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if strengths:
        st.markdown("**Strengths**")
        for s in strengths:
            st.markdown(f"<div style='color:#065F46;font-size:14px;'>✓ {s}</div>", unsafe_allow_html=True)

    if improvements:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("**Areas to Improve**")
        for imp in improvements:
            st.markdown(f"<div style='color:#92400E;font-size:14px;'>⚠ {imp}</div>", unsafe_allow_html=True)


def _render_market_widget(holdings: list[dict[str, Any]]) -> None:
    """Render the market data status widget."""
    num_with_data = sum(1 for h in holdings if _get_current_price(h.get("symbol", "")) is not None)
    total = len(holdings)

    st.markdown(
        f"""
        <div class="market-widget" style="margin-top: 20px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                <span class="market-status-dot"></span>
                <span style="font-size:14px;font-weight:700;color:#111827;">Market Data</span>
            </div>
            <div style="font-size:13px;color:#6B7280;line-height:1.5;">
                Current portfolio values based on available market data.<br/>
                <strong style="color:#111827;">{num_with_data}/{total}</strong> holdings with live price updates.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_portfolio_page() -> None:
    """Main entry point for the Portfolio page."""
    _inject_portfolio_styles()

    user_id = st.session_state.get("portfolio_user_id")
    username = st.session_state.get("portfolio_username", "")

    if not user_id:
        _render_auth_page()
        return

    st.markdown('<div class="portfolio-wrapper">', unsafe_allow_html=True)

    # Compact top-right header with username and logout
    st.markdown(
        f"""
        <div class="portfolio-topbar">
            <div class="portfolio-user-chip">👤 {username}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, logout_col = st.columns([4, 1])
    with logout_col:
        if st.button("Logout", key="portfolio_logout_btn"):
            for key in list(st.session_state.keys()):
                if key.startswith("portfolio_") or key.startswith("price_") or key.startswith("edit_") or key.startswith("editing_"):
                    del st.session_state[key]
            st.success("Logged out successfully.")
            st.rerun()

    # Portfolio header section
    st.markdown(
        """
        <div class="portfolio-header">
            <div>
                <div class="portfolio-title">💼 My Portfolio</div>
                <div class="portfolio-subtitle">Track, analyze and monitor your investment portfolio.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    holdings = get_holdings(user_id)

    _render_summary(holdings)
    _render_add_holding(user_id)

    if not holdings:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <div class="empty-title">Your portfolio is empty</div>
                <div class="empty-text">Add your first holding to start tracking your investments.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"<div class='holdings-title'>{len(holdings)} Holdings</div>", unsafe_allow_html=True)
        for holding in holdings:
            _render_holding_card(holding, user_id)

    _render_insights(holdings)

    # Health Score toggle button
    button_label = "Hide Health Score" if st.session_state.get("portfolio_health_visible") else "Portfolio Health Score"
    if st.button(button_label, key="toggle_health_score", type="primary", use_container_width=True):
        st.session_state["portfolio_health_visible"] = not st.session_state.get("portfolio_health_visible", False)
        st.rerun()

    # Show health section only when toggled on
    if st.session_state.get("portfolio_health_visible"):
        _render_health_section(holdings)
        _render_market_widget(holdings)

    st.markdown('</div>', unsafe_allow_html=True)
