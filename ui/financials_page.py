"""Financial overview tab."""

from __future__ import annotations

import streamlit as st


def render_financials_page() -> None:
    """Tab 2: Financials (plotly charts + financial health score)."""

    st.subheader("Financials")
    years = st.session_state.get('years', ['FY23', 'FY24', 'FY25'])
    unit = st.session_state.get('revenue_unit', 'Lakhs')
    st.caption(
        f"Financial data extracted from document "
        f"({years[0]}-{years[-1]}) | Values in ₹ {unit}"
    )

    import plotly.graph_objects as go

    if not st.session_state.get("analysis_done"):
        st.write("Upload a PDF and click Analyze to begin.")
        return

    col1, col2, col3, col4, col5 = st.columns(5)

    revenue = st.session_state.get('latest_revenue', 0)
    unit = st.session_state.get('revenue_unit', 'Lakhs')
    rev_growth = st.session_state.get('revenue_growth', 0)
    pat = st.session_state.get('latest_pat', 0)
    pat_margin = st.session_state.get('pat_margin_pct', 0)
    pat_growth = st.session_state.get('pat_growth', 0)
    fh_score = st.session_state.get('financial_health_score', 0)
    eps = st.session_state.get('eps', 0)

    with col1:
        st.metric(
            label=f"Revenue ({unit})",
            value=f"₹{revenue:,.1f}",
            delta=f"{rev_growth:+.1f}% YoY" if rev_growth else None
        )
    with col2:
        st.metric(
            label="Net Profit (PAT)",
            value=f"₹{pat:,.1f} {unit}",
            delta=f"{pat_growth:+.1f}% YoY" if pat_growth else None
        )
    with col3:
        st.metric(
            label="PAT Margin",
            value=f"{pat_margin:.1f}%",
            delta="vs industry avg" if pat_margin else None
        )
    with col4:
        st.metric(
            label="Financial Health",
            value=f"{fh_score}/100",
            delta="Score"
        )
    with col5:
        cagr = st.session_state.get('revenue_cagr', 0)
        st.metric(
            "Revenue CAGR (3Y)",
            f"{cagr:.1f}%" if cagr else "N/A"
        )

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        pe = st.session_state.get('pe_ratio', 'N/A')
        st.metric(
            label="P/E Ratio",
            value=pe,
            help="Price to Earnings ratio from Basis of Issue Price section"
        )

    with col6:
        eps_val = st.session_state.get('eps', 'N/A')
        st.metric(
            label="EPS (Basic)",
            value=eps_val,
            help="Earnings Per Share from restated financials"
        )

    with col7:
        ronw_val = st.session_state.get('ronw', 'N/A')
        st.metric(
            label="Return on Net Worth",
            value=ronw_val,
            help="RONW from Basis of Issue Price section"
        )

    with col8:
        nav_val = st.session_state.get('nav', 'N/A')
        st.metric(
            label="NAV per Share",
            value=nav_val,
            help="Net Asset Value per share"
        )

    st.markdown("---")

    years = st.session_state.get("years", ["FY22", "FY23", "FY24"])
    revenue_data = st.session_state.get("revenue_data", [0, 0, 0])
    pat_margin_data = st.session_state.get("pat_margin_data", [0, 0, 0])

    col1, col2, col3 = st.columns(3)

    with col1:
        fig1 = go.Figure()
        fig1.add_bar(x=years, y=revenue_data, marker_color='#00B386')
        fig1.update_layout(
            title="Revenue Trend" + (" (Estimated)" if st.session_state.get("financials_estimated") else ""),
            plot_bgcolor='#FFFFFF',
            paper_bgcolor='#FFFFFF',
            font_color='#1A1A1A',
            xaxis=dict(gridcolor='#E5E7EB', color='#6B7280'),
            yaxis=dict(gridcolor='#E5E7EB', color='#6B7280')
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_scatter(x=years, y=pat_margin_data, mode="lines+markers", line=dict(color='#00B386', width=3))
        fig2.update_layout(
            title="PAT Margin" + (" (Estimated)" if st.session_state.get("financials_estimated") else ""),
            plot_bgcolor='#FFFFFF',
            paper_bgcolor='#FFFFFF',
            font_color='#1A1A1A',
            xaxis=dict(gridcolor='#E5E7EB', color='#6B7280'),
            yaxis=dict(gridcolor='#E5E7EB', color='#6B7280')
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        pe_str = st.session_state.get('pe_ratio', 'N/A')
        pe_val = 0.0
        if pe_str and pe_str != 'N/A':
            import re
            pe_match = re.search(r'([\d.]+)', pe_str)
            if pe_match:
                try:
                    pe_val = float(pe_match.group(1))
                except:
                    pe_val = 0.0

        fig_pe = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pe_val,
            title={"text": "P/E Ratio", "font": {"size": 14}},
            number={"suffix": "x", "font": {"size": 28}},
            gauge={
                "axis": {
                    "range": [0, 50],
                    "tickwidth": 1,
                    "tickcolor": "#6B7280"
                },
                "bar": {"color": "#00B386"},
                "bgcolor": "#F8FAF9",
                "borderwidth": 1,
                "bordercolor": "#E5E7EB",
                "steps": [
                    {"range": [0, 15], "color": "#D4FFEF"},
                    {"range": [15, 30], "color": "#FFF3D4"},
                    {"range": [30, 50], "color": "#FFD4D8"}
                ],
                "threshold": {
                    "line": {"color": "#00B386", "width": 3},
                    "thickness": 0.75,
                    "value": pe_val
                }
            }
        ))
        fig_pe.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1A1A1A')
        )
        st.plotly_chart(fig_pe, use_container_width=True)

        if pe_val > 0:
            if pe_val < 15:
                st.success(f"P/E of {pe_val:.1f}x — Attractively valued vs peers")
            elif pe_val < 25:
                st.info(f"P/E of {pe_val:.1f}x — Fairly valued")
            else:
                st.warning(f"P/E of {pe_val:.1f}x — Premium valuation")
        else:
            st.caption("P/E ratio not found in document")

    st.markdown("---")

    score = int(st.session_state.get("financial_health_score", 0))
    color = "#00B386" if score >= 70 else ("#FFA726" if score >= 40 else "#FF4757")

    st.markdown(
        f"""
        <div style="padding: 24px; border-radius: 12px; background: linear-gradient(135deg, #E8FFF6, #D4FFEF); border: 1px solid #00B386;">
          <div style="font-size: 48px; font-weight: 800; color: {color}; line-height:1;">{score}</div>
          <div style="color: #6B7280;">Financial Health Score (0-100)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )