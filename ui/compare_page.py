"""Peer comparison tab."""

from __future__ import annotations

import streamlit as st


def render_compare_page() -> None:
    """Tab 4: Verdict (APPLY/AVOID) + listing gain + reasons + disclaimer."""

    st.subheader("Verdict")

    if not st.session_state.get("analysis_done"):
        st.write("Upload a PDF and click Analyze to begin.")
        st.markdown(
            """
            <div style="padding: 24px; border-radius: 12px; background: linear-gradient(135deg, #E8FFF6, #D4FFEF); border: 1px solid #00B386;">
              <div style="font-size: 36px; font-weight: 900; color: #FFA726;">APPLY WITH CAUTION</div>
              <div style="color: #6B7280; font-weight: 600; margin-top: 6px;">Listing gain range: Conservative 0.0% | Base 0.0% | Bull 0.0%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    verdict = st.session_state.get("verdict", "APPLY WITH CAUTION")
    base_gain = float(st.session_state.get("base_gain", st.session_state.get("base_case_gain", 0.0)))
    cons_gain = float(st.session_state.get("conservative_gain", 0.0))
    bull_gain = float(st.session_state.get("bull_gain", st.session_state.get("bull_case_gain", 0.0)))
    reasons = st.session_state.get("reasons", st.session_state.get("verdict_reasons", []))
    if not reasons:
        reasons = ["(No reasons generated yet.)"]


    if verdict == "APPLY":
        bg_gradient = "linear-gradient(135deg, #E8FFF6, #D4FFEF)"
        border_color = "#00B386"
        text_color = "#00B386"
    elif verdict == "AVOID":
        bg_gradient = "linear-gradient(135deg, #FFE8EA, #FFD4D8)"
        border_color = "#FF4757"
        text_color = "#FF4757"
    else:
        bg_gradient = "linear-gradient(135deg, #FFF8E8, #FFEFD4)"
        border_color = "#FFA726"
        text_color = "#E58A00"

    st.markdown(
        f"""
        <div style="padding: 24px; border-radius: 12px; background: {bg_gradient}; border: 1px solid {border_color};">
          <div style="font-size: 36px; font-weight: 900; color: {text_color};">{verdict}</div>
          <div style="color: #6B7280; font-weight: 600; margin-top: 6px;">
            Listing gain range: Conservative {cons_gain:.1f}% | Base {base_gain:.1f}% | Bull {bull_gain:.1f}%
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown("### 📥 Download Document")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            "Download the original DRHP/RHP document "
            "for your reference and detailed reading."
        )
    with col2:
        uploaded = st.session_state.get("drhp_file", None)
        if uploaded is not None:
            # Reset file pointer to beginning
            uploaded.seek(0)
            file_bytes = uploaded.read()
            file_name = getattr(uploaded, "name", "DRHP_RHP_Document.pdf")

            st.download_button(
                label="⬇️ Download PDF",
                data=file_bytes,
                file_name=file_name,
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.info("Upload a PDF first to enable download.")

    st.markdown("---")

    st.markdown("### 📊 Listing Gain Factor Analysis")
    st.caption(
        "The listing gain prediction is calculated using a "
        "weighted scoring model based on these key factors:"
    )

    # Get data from session state
    risk_score = float(st.session_state.get('risk_score', 50))
    financial_score = float(
        st.session_state.get('financial_health_score', 50)
    )
    base_gain = float(st.session_state.get('base_gain', 0))
    conservative_gain = float(
        st.session_state.get('conservative_gain', 0)
    )
    bull_gain = float(st.session_state.get('bull_gain', 0))
    de_ratio = float(st.session_state.get('de_ratio', 0))
    revenue_data = st.session_state.get('revenue_data', [0, 0, 0])
    risk_categories = st.session_state.get('risk_categories', {})
    reasons = st.session_state.get('reasons', [])

    # Factor 1: Financial Health
    st.markdown("#### 💰 Financial Health Score")
    col1, col2 = st.columns([1, 3])
    with col1:
        color = (
            "green" if financial_score >= 70
            else "orange" if financial_score >= 40
            else "red"
        )
        st.markdown(
            f"<h2 style='color:{color};margin:0'>"
            f"{financial_score:.0f}/100</h2>",
            unsafe_allow_html=True
        )
    with col2:
        if financial_score >= 70:
            st.success(
                "Strong financial health — positive indicator "
                "for listing gains. Companies with high financial "
                "scores historically list at premium."
            )
        elif financial_score >= 40:
            st.warning(
                "Moderate financial health — neutral impact on "
                "listing. Monitor revenue growth and debt levels "
                "before applying."
            )
        else:
            st.error(
                "Weak financial health — negative indicator. "
                "High risk of listing below issue price. "
                "Consider avoiding."
            )
    st.progress(financial_score / 100)

    st.markdown("---")

    # Factor 2: Risk Score
    st.markdown("#### ⚠️ Overall Risk Score")
    col1, col2 = st.columns([1, 3])
    with col1:
        risk_color = (
            "green" if risk_score <= 40
            else "orange" if risk_score <= 70
            else "red"
        )
        st.markdown(
            f"<h2 style='color:{risk_color};margin:0'>"
            f"{risk_score:.0f}/100</h2>",
            unsafe_allow_html=True
        )
    with col2:
        if risk_score <= 40:
            st.success(
                "Low risk profile — strong positive signal. "
                "Lower risk scores correlate with better "
                "listing day performance."
            )
        elif risk_score <= 70:
            st.warning(
                "Moderate risk — apply with caution. "
                "Ensure you understand the key risk factors "
                "before investing."
            )
        else:
            st.error(
                "High risk profile — significant concern. "
                "Multiple risk factors identified that could "
                "negatively impact listing performance."
            )
    risk_bar_val = max(0.0, min(1.0, risk_score / 100))
    st.progress(risk_bar_val)

    st.markdown("---")

    # Factor 3: Individual Risk Categories
    st.markdown("#### 🔍 Risk Category Breakdown")
    risk_labels = {
        'financial': ('💰 Financial Risk', 0.30),
        'regulatory': ('⚖️ Regulatory Risk', 0.25),
        'litigation': ('⚠️ Litigation Risk', 0.20),
        'operational': ('🔧 Operational Risk', 0.15),
        'promoter': ('👤 Promoter Risk', 0.10),
    }
    for key, (label, weight) in risk_labels.items():
        score = risk_categories.get(key, 0)
        level = (
            "LOW ✅" if score <= 3
            else "MEDIUM ⚠️" if score <= 6
            else "HIGH 🔴"
        )
        col1, col2, col3, col4 = st.columns([2, 1, 4, 1])
        with col1:
            st.caption(label)
        with col2:
            st.caption(f"{score}/10")
        with col3:
            progress_val = max(0.0, min(1.0, score / 10))
            st.progress(progress_val)
        with col4:
            st.caption(level)

    st.markdown("---")

    # Factor 4: Revenue Trend
    st.markdown("#### 📈 Revenue Trend Impact")
    years = st.session_state.get('years', ['FY22', 'FY23', 'FY24'])
    if revenue_data and any(v > 0 for v in revenue_data):
        if len(revenue_data) >= 2 and revenue_data[0] > 0:
            growth = (
                (revenue_data[-1] - revenue_data[0])
                / revenue_data[0] * 100
            )
            if growth > 20:
                st.success(
                    f"Revenue grew {growth:.1f}% over the period "
                    f"({years[0]} to {years[-1]}) — strong growth "
                    f"trajectory is a positive listing signal."
                )
            elif growth > 0:
                st.warning(
                    f"Revenue grew {growth:.1f}% over the period "
                    f"({years[0]} to {years[-1]}) — moderate growth, "
                    f"neutral impact on listing gains."
                )
            else:
                st.error(
                    f"Revenue declined {abs(growth):.1f}% over the "
                    f"period — negative signal for listing performance."
                )
    else:
        st.info(
            "Revenue data not available from document. "
            "Check the Financials tab for extracted data."
        )

    st.markdown("---")
    st.markdown("#### 📊 Valuation Analysis (P/E Ratio)")

    pe_str = st.session_state.get('pe_ratio', 'N/A')
    eps_str = st.session_state.get('eps', 'N/A')
    ronw_str = st.session_state.get('ronw', 'N/A')

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="P/E Ratio",
            value=pe_str if pe_str != 'N/A' else "N/A",
            help="Price to Earnings ratio at issue price"
        )

    with col2:
        st.metric(
            label="EPS (FY25)",
            value=eps_str if eps_str != 'N/A' else "N/A",
            help="Basic Earnings Per Share for latest fiscal year"
        )

    with col3:
        st.metric(
            label="Return on Net Worth",
            value=ronw_str if ronw_str != 'N/A' else "N/A",
            help="RoNW indicates profitability relative to equity"
        )

    # P/E interpretation
    if pe_str and pe_str != 'N/A':
        import re
        pe_num_match = re.search(r'([\d.]+)', pe_str)
        if pe_num_match:
            pe_num = float(pe_num_match.group(1))
            if pe_num < 15:
                st.success(
                    f"✅ P/E of {pe_str} is attractively valued "
                    f"compared to industry peers. "
                    f"Good valuation for investors."
                )
            elif pe_num < 25:
                st.info(
                    f"ℹ️ P/E of {pe_str} is fairly valued. "
                    f"Reasonable pricing relative to earnings."
                )
            elif pe_num < 40:
                st.warning(
                    f"⚠️ P/E of {pe_str} is at premium valuation. "
                    f"Priced for high growth expectations."
                )
            else:
                st.error(
                    f"🔴 P/E of {pe_str} is very high. "
                    f"Significant premium — ensure growth "
                    f"justifies the valuation."
                )
    else:
        st.info(
            "P/E ratio not found in document. "
            "Check Basis of Issue Price section in the document."
        )

    st.markdown("---")

    # Factor 6: Listing Gain Formula Explanation
    st.markdown("#### 🧮 How Listing Gain is Calculated")
    with st.expander("View calculation methodology", expanded=False):
        st.markdown(
            f"""
**Formula used by InvestIQ:**

Base Gain = (Financial Score - Risk Score) × 0.3 + 10
Conservative = Base Gain × 0.5
Bull Case    = Base Gain × 1.8

**Your values:**
- Financial Health Score: **{financial_score:.0f}/100**
- Risk Score: **{risk_score:.0f}/100**
- Base Case Gain: **{base_gain:.1f}%**
- Conservative: **{conservative_gain:.1f}%**
- Bull Case: **{bull_gain:.1f}%**

**Factors that increase listing gain prediction:**
- High financial health score (>70)
- Low risk score (<40)
- Strong revenue growth (>20% CAGR)
- Low debt-to-equity ratio (<1x)
- Positive sector outlook

**Factors that reduce listing gain prediction:**
- High risk score (>60)
- Weak financials
- High debt levels
- Regulatory/litigation risks
- Market conditions

*Note: This is a rule-based estimate.
Actual listing gains depend on market conditions,
GMP, subscription levels, and investor sentiment
which are not captured in the DRHP document alone.*
    """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Factor 7: AI Reasons
    st.markdown("#### 🤖 AI Key Observations")
    if reasons:
        for i, reason in enumerate(reasons, 1):
            if any(x in reason.lower() for x in
                   ['strong', 'positive', 'good', 'healthy', 'growth']):
                st.success(f"✅ {reason}")
            elif any(x in reason.lower() for x in
                     ['high risk', 'debt', 'negative', 'weak', 'decline']):
                st.error(f"🔴 {reason}")
            else:
                st.warning(f"⚠️ {reason}")
    else:
        st.info("Run analysis to see AI observations.")

    st.markdown("---")

    st.caption(
        "Disclaimer: This tool provides informational analysis and does not constitute financial advice. "
        "Verify data and consult a licensed financial advisor before investing."
    )