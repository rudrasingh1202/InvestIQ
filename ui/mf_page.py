import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging

from ui.mf_allocator import get_allocation


def _render_star_rating(rating: int) -> str:
    return "⭐" * rating + "☆" * (5 - rating)


def _render_fund_card(fund: dict, category: str, weight: float):
    st.markdown(f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    ">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div style="flex:1;">
                <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:4px;">
                    {fund['name']}
                </div>
                <div style="font-size:12px;color:#6B7280;margin-bottom:6px;">
                    {fund['amc']} • {fund['category']} • {_render_star_rating(fund['rating'])}
                </div>
                <div style="font-size:12px;color:#6B7280;margin-bottom:6px;">
                    Risk: <span style="color:#111827;font-weight:600;">{fund['risk']}</span> •
                    Expense: <span style="color:#111827;font-weight:600;">{fund['expense_ratio']}%</span> •
                    AUM: <span style="color:#111827;font-weight:600;">₹{fund['aum_cr']:,}Cr</span> •
                    Min SIP: <span style="color:#111827;font-weight:600;">₹{fund['min_sip']:,}</span>
                </div>
                <div style="display:flex;gap:16px;margin-bottom:8px;">
                    <div style="font-size:12px;color:#6B7280;">3Y CAGR: <span style="color:#00B386;font-weight:700;">{fund['cagr_3y']}%</span></div>
                    <div style="font-size:12px;color:#6B7280;">5Y CAGR: <span style="color:#00B386;font-weight:700;">{fund['cagr_5y']}%</span></div>
                </div>
                <div style="font-size:12px;color:#4B5563;line-height:1.5;font-style:italic;">
                    "{fund['insight']}"
                </div>
            </div>
            <div style="
                background: linear-gradient(135deg, #ECFDF5, #FFFFFF);
                color: #065F46;
                font-weight: 800;
                font-size: 18px;
                padding: 10px 14px;
                border-radius: 12px;
                border: 1px solid #00B386;
                margin-left: 12px;
                white-space: nowrap;
            ">{weight:.0f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_allocation_card(category: str, weight: float, color: str, icon: str):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color}15, #FFFFFF);
        border: 1px solid {color}30;
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    ">
        <div style="font-size:24px;margin-bottom:6px;">{icon}</div>
        <div style="font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:4px;">
            {category}
        </div>
        <div style="font-size:28px;font-weight:900;color:{color};margin-bottom:2px;">{weight:.0f}%</div>
        <div style="font-size:10px;color:#9CA3AF;">Allocation</div>
    </div>
    """, unsafe_allow_html=True)


def render_mf_page():
    print("\n" + "="*60)
    print("[RENDER] render_mf_page() START")
    print("="*60)

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    .mf-wrapper {
        font-family: 'Inter', sans-serif;
    }
    .mf-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 16px;
    }
    .mf-section-title {
        font-size: 18px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 12px;
    }
    .mf-divider {
        border: none;
        border-top: 1px solid #E5E7EB;
        margin: 24px 0;
    }
    .mf-metric-card {
        background: #F8FAF9;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .mf-metric-value {
        font-size: 22px;
        font-weight: 800;
        color: #00B386;
        margin-bottom: 4px;
    }
    .mf-metric-label {
        font-size: 11px;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
    }
    .mf-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .mf-badge-high { background: #ECFDF5; color: #00B386; }
    .mf-badge-moderate { background: #FFFBEB; color: #D97706; }
    .mf-badge-low { background: #FEF2F2; color: #DC2626; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="mf-wrapper">', unsafe_allow_html=True)

    if "mf_result" not in st.session_state:
        st.session_state["mf_result"] = None
    if "mf_profile" not in st.session_state:
        st.session_state["mf_profile"] = None

    if st.session_state["mf_result"] is None:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.markdown("## 🚀 AI-Powered MF Advisor")
            st.markdown("**AI-Powered Portfolio Allocation & Fund Recommendations**")
        with col_right:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("AI Modules", "6+")
            with c2:
                st.metric("Funds Analyzed", "25+")

        st.markdown("---")

        with st.form("mf_form"):
            st.markdown('<div class="mf-card">', unsafe_allow_html=True)
            st.markdown('<div class="mf-section-title">💰 Investment Profile</div>', unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                amount = st.number_input(
                    "Investment Amount (₹)",
                    min_value=500,
                    max_value=10000000,
                    value=10000,
                    step=500,
                    key="mf_amount",
                )
                horizon = st.selectbox(
                    "Investment Horizon",
                    ["<1 Year", "1-3 Years", "3-5 Years", "5-10 Years", "10+ Years"],
                    index=2,
                    key="mf_horizon",
                )
                goal = st.selectbox(
                    "Investment Goal",
                    [
                        "Wealth Creation",
                        "Retirement",
                        "Child Education",
                        "House Purchase",
                        "Emergency Fund",
                        "Passive Income",
                        "Tax Saving",
                        "Capital Preservation",
                    ],
                    index=0,
                    key="mf_goal",
                )
            with c2:
                invest_type = st.radio(
                    "Investment Type",
                    ["SIP", "Lump Sum"],
                    horizontal=True,
                    key="mf_type",
                )
                risk = st.selectbox(
                    "Risk Appetite",
                    ["Low", "Moderate", "High"],
                    index=1,
                    key="mf_risk",
                )
                existing = st.radio(
                    "Existing Investor?",
                    ["Yes", "No"],
                    horizontal=True,
                    index=1,
                    key="mf_existing",
                )

            age = st.number_input(
                "Age (optional)",
                min_value=18,
                max_value=100,
                value=35,
                step=1,
                key="mf_age",
            )

            st.markdown('</div>', unsafe_allow_html=True)

            submitted = st.form_submit_button(
                "🚀 Generate Strategy",
                type="primary",
                use_container_width=True,
            )

            if submitted:
                profile = {
                    "amount": amount,
                    "invest_type": invest_type,
                    "horizon": horizon,
                    "risk_appetite": risk,
                    "risk": risk,
                    "goal": goal,
                    "existing_investor": existing,
                    "age": age,
                }
                try:
                    with st.spinner("AI is crafting your personalized investment strategy..."):
                        result = get_allocation(profile)
                except Exception:
                    logging.exception("MF strategy generation failed")
                    st.session_state["mf_result"] = None
                    st.session_state["mf_profile"] = None
                    st.error(
                        "⚠️ Unable to generate your investment strategy at the moment. "
                        "Please verify your inputs and try again."
                    )
                    st.stop()
                st.session_state["mf_result"] = result
                st.session_state["mf_profile"] = profile
                st.rerun()
    else:
        try:
            result = st.session_state["mf_result"]
            profile = st.session_state["mf_profile"]

            invest_type = profile.get("invest_type", "SIP")
            amount = float(profile.get("amount", 10000))
            h_years = {
                "<1 Year": 0.5,
                "1-3 Years": 2,
                "3-5 Years": 4,
                "5-10 Years": 7,
                "10+ Years": 12,
            }.get(profile.get("horizon", "3-5 Years"), 4)
            cagr_rate = result["expected_cagr"] / 100

            if invest_type == "Lump Sum":
                total_invested = amount
                projected_value = amount * ((1 + cagr_rate) ** h_years)
                estimated_gain = projected_value - total_invested
            else:
                months = int(h_years * 12)
                monthly = amount
                total_invested = monthly * months
                monthly_cagr = cagr_rate / 12
                if monthly_cagr > 0:
                    projected_value = monthly * (((1 + monthly_cagr) ** months - 1) / monthly_cagr)
                else:
                    projected_value = total_invested
                estimated_gain = projected_value - total_invested

            col_left, col_right = st.columns([2, 1])
            with col_left:
                st.markdown("## 🚀 AI-Powered MF Advisor")
                st.markdown("**AI-Powered Portfolio Allocation & Fund Recommendations**")
            with col_right:
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("AI Modules", "6+")
                with c2:
                    st.metric("Funds Analyzed", "250+")

            st.markdown("---")

            st.markdown('<div class="mf-card">', unsafe_allow_html=True)
            st.markdown('<div class="mf-section-title">📊 Asset Allocation</div>', unsafe_allow_html=True)

            alloc = result["allocation"]
            cat_colors = {
                "Large Cap": "#00B386",
                "Mid Cap": "#3B82F6",
                "Small Cap": "#8B5CF6",
                "Flexi Cap": "#F59E0B",
                "Multi Cap": "#EC4899",
                "ELSS": "#DC2626",
                "Debt Fund": "#6366F1",
                "Liquid Fund": "#06B6D4",
                "Hybrid Fund": "#F97316",
                "Gold ETF": "#D97706",
                "Dividend Yield": "#10B981",
            }
            cat_icons = {
                "Large Cap": "🏛️",
                "Mid Cap": "📈",
                "Small Cap": "🚀",
                "Flexi Cap": "🎯",
                "Multi Cap": "🌐",
                "ELSS": "🧾",
                "Debt Fund": "🏦",
                "Liquid Fund": "💧",
                "Hybrid Fund": "🔀",
                "Gold ETF": "🥇",
                "Dividend Yield": "💵",
            }

            cards_per_row = 4
            cats = list(alloc.items())
            for i in range(0, len(cats), cards_per_row):
                row = cats[i:i + cards_per_row]
                cols = st.columns(len(row))
                for col, (cat, wt) in zip(cols, row):
                    with col:
                        color = cat_colors.get(cat, "#00B386")
                        icon = cat_icons.get(cat, "📊")
                        _render_allocation_card(cat, wt, color, icon)

            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="mf-card">', unsafe_allow_html=True)
            st.markdown('<div class="mf-section-title">🎯 Recommended Funds</div>', unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size:12px;color:#6B7280;margin-bottom:12px;'>"
                "AI-curated funds for each category based on performance, risk, and your profile."
                "</div>",
                unsafe_allow_html=True,
            )

            for cat, funds in result["recommended_funds"].items():
                wt = alloc.get(cat, 0)
                color = cat_colors.get(cat, "#00B386")
                st.markdown(f"<div style='font-size:14px;font-weight:700;color:{color};margin:12px 0 6px;'>{cat} ({wt:.0f}%)</div>", unsafe_allow_html=True)
                for fund in funds:
                    _render_fund_card(fund, cat, wt / len(funds))

            st.markdown('</div>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Estimated CAGR", f"{result['expected_cagr']:.1f}%")
            with col2:
                st.markdown(f"""
                <div class="mf-metric-card">
                    <div class="mf-metric-value">₹{projected_value:,.0f}</div>
                    <div class="mf-metric-label">Projected Value</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="mf-metric-card">
                    <div class="mf-metric-value">₹{estimated_gain:,.0f}</div>
                    <div class="mf-metric-label">Estimated Gain</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="mf-card">', unsafe_allow_html=True)
            st.markdown('<div class="mf-section-title">📈 Investment Projection</div>', unsafe_allow_html=True)

            months = int({
                "<1 Year": 12,
                "1-3 Years": 36,
                "3-5 Years": 60,
                "5-10 Years": 120,
                "10+ Years": 180,
            }.get(profile.get("horizon", "3-5 Years"), 60))

            if invest_type == "Lump Sum":
                invested = [amount] + [amount] * months
                projected = [amount * ((1 + cagr_rate) ** (m / 12)) for m in range(months + 1)]
                chart_df = pd.DataFrame({
                    "Month": list(range(0, months + 1)),
                    "Invested": invested,
                    "Projected": projected,
                })
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=chart_df["Month"], y=chart_df["Invested"],
                    mode="lines", name="Total Invested",
                    line=dict(color="#6B7280", width=2, dash="dot"),
                ))
                fig.add_trace(go.Scatter(
                    x=chart_df["Month"], y=chart_df["Projected"],
                    mode="lines", name="Projected Value",
                    line=dict(color="#00B386", width=3),
                    fill="tozeroy",
                    fillcolor="rgba(0,179,134,0.08)",
                ))
            else:
                monthly = amount
                invested = [monthly * m for m in range(1, months + 1)]
                projected = []
                monthly_cagr = cagr_rate / 12
                for m in range(1, months + 1):
                    fv = monthly * (((1 + monthly_cagr) ** m - 1) / monthly_cagr) if monthly_cagr > 0 else monthly * m
                    projected.append(fv)

                chart_df = pd.DataFrame({
                    "Month": list(range(1, months + 1)),
                    "Invested": invested,
                    "Projected": projected,
                })
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=chart_df["Month"], y=chart_df["Invested"],
                    mode="lines", name="Total Invested",
                    line=dict(color="#6B7280", width=2, dash="dot"),
                ))
                fig.add_trace(go.Scatter(
                    x=chart_df["Month"], y=chart_df["Projected"],
                    mode="lines", name="Projected Value",
                    line=dict(color="#00B386", width=3),
                    fill="tozeroy",
                    fillcolor="rgba(0,179,134,0.08)",
                ))
            fig.update_layout(
                height=320,
                paper_bgcolor="white",
                plot_bgcolor="#FAFAFA",
                xaxis=dict(gridcolor="#E5E7EB", title="Month"),
                yaxis=dict(gridcolor="#E5E7EB", title="Value (₹)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="mf-card">', unsafe_allow_html=True)
            st.markdown('<div class="mf-section-title">📋 Summary</div>', unsafe_allow_html=True)

            s1, s2, s3, s4 = st.columns(4)
            with s1:
                label1 = "Monthly Investment" if invest_type == "SIP" else "Lump Sum Investment"
                st.markdown(f"""
                <div class="mf-metric-card">
                    <div class="mf-metric-value">₹{amount:,.0f}</div>
                    <div class="mf-metric-label">{label1}</div>
                </div>
                """, unsafe_allow_html=True)
            with s2:
                st.markdown(f"""
                <div class="mf-metric-card">
                    <div class="mf-metric-value">{result['expected_cagr']:.1f}%</div>
                    <div class="mf-metric-label">Expected CAGR</div>
                </div>
                """, unsafe_allow_html=True)
            with s3:
                risk_class = "mf-badge-high" if result["risk_score"] >= 7 else "mf-badge-moderate" if result["risk_score"] >= 4 else "mf-badge-low"
                st.markdown(f"""
                <div class="mf-metric-card">
                    <div class="mf-metric-value" style="font-size:18px;">{result['risk_score']}/10</div>
                    <div class="mf-metric-label">Risk Score</span></div>
                    <div style="margin-top:6px;"><span class="mf-badge {risk_class}">{profile.get('risk', 'Moderate')}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with s4:
                st.markdown(f"""
                <div class="mf-metric-card">
                    <div class="mf-metric-value">{result['diversification_score']}/10</div>
                    <div class="mf-metric-label">Diversification</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="mf-divider"></div>', unsafe_allow_html=True)

            d1, d2, d3, d4 = st.columns(4)
            with d1:
                st.markdown(f"""
                <div class="mf-metric-card">
                    <div class="mf-metric-value">{result['recommended_period']}</div>
                    <div class="mf-metric-label">Holding Period</div>
                </div>
                """, unsafe_allow_html=True)
            with d2:
                quality_class = "mf-badge-high" if result["portfolio_quality"] == "Excellent" else "mf-badge-moderate"
                st.markdown(f"""
                <div class="mf-metric-card">
                    <div class="mf-metric-value" style="font-size:16px;">{result['portfolio_quality']}</div>
                    <div class="mf-metric-label">Portfolio Quality</div>
                    <div style="margin-top:6px;"><span class="mf-badge {quality_class}">{result['ai_confidence']} Confidence</span></div>
                </div>
                """, unsafe_allow_html=True)
            with d3:
                st.markdown(f"""
                <div class="mf-metric-card">
                    <div class="mf-metric-value">₹{total_invested:,.0f}</div>
                    <div class="mf-metric-label">Total Investment</div>
                </div>
                """, unsafe_allow_html=True)
            with d4:
                st.markdown(f"""
                <div class="mf-metric-card">
                    <div class="mf-metric-value">₹{estimated_gain:,.0f}</div>
                    <div class="mf-metric-label">Estimated Gain</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="mf-card">', unsafe_allow_html=True)
            st.markdown('<div class="mf-section-title">🧠 Why This Strategy?</div>', unsafe_allow_html=True)
            for r in result["rationale"]:
                st.markdown(f"<div style='font-size:14px;color:#374151;margin-bottom:6px;'>✓ {r}</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="mf-card">', unsafe_allow_html=True)
            st.markdown('<div class="mf-section-title">💡 Portfolio Insights</div>', unsafe_allow_html=True)
            for ins in result["insights"]:
                st.markdown(f"<div style='font-size:14px;color:#374151;margin-bottom:6px;'>• {ins}</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if st.button("🔄 Recalculate", use_container_width=True, key="mf_recalc"):
                st.session_state["mf_result"] = None
                st.rerun()
        except Exception:
            logging.exception("MF strategy rendering failed")
            st.session_state["mf_result"] = None
            st.session_state["mf_profile"] = None
            st.error(
                "⚠️ Unable to generate your investment strategy at the moment. "
                "Please verify your inputs and try again."
            )
            st.stop()

    st.markdown('</div>', unsafe_allow_html=True)

    print("\n" + "="*60)
    print("[RENDER] render_mf_page() END")
    print("="*60)
