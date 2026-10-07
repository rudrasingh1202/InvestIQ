"""Risk score tab."""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def render_risk_page() -> None:
    """Tab 3: Risk Analysis (risk gauge, cards, LLM summary)."""

    st.subheader("Risk Analysis")
    st.caption("Plotly + placeholders. Connect risk scoring later.")

    risk_score = int(st.session_state.get("risk_score_0_100", 0))

    # Gauge
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=risk_score,
            title={"text": "Overall Risk Score (0-100)"},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#6B7280"},
                "bar": {"color": "#FF4757"},
                "bgcolor": "#F8FAF9",
                "borderwidth": 1,
                "bordercolor": "#E5E7EB",
                "steps": [
                    {"range": [0, 40], "color": "#D4FFEF"},
                    {"range": [40, 70], "color": "#FFF3D4"},
                    {"range": [70, 100], "color": "#FFD4D8"},
                ],
                "threshold": {
                    "line": {"color": "#FF4757", "width": 4},
                    "thickness": 0.75,
                    "value": risk_score,
                },
            },
        )
    )
    fig.update_layout(
        plot_bgcolor='#FFFFFF',
        paper_bgcolor='#FFFFFF',
        font_color='#1A1A1A'
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")


    if not st.session_state.get("analysis_done"):
        st.write("Upload a PDF and click Analyze to begin.")
        return

    risk_cats = st.session_state.get('risk_categories', {})
    labels = {
        'financial': 'Financial Risk',
        'regulatory': 'Regulatory Risk',
        'litigation': 'Litigation Risk',
        'operational': 'Operational Risk',
        'promoter': 'Promoter Risk'
    }

    for key, label in labels.items():
        score = risk_cats.get(key, 0)
        if score <= 3:
            color = '#00B386'
            level = 'LOW'
        elif score <= 6:
            color = '#FFA726'
            level = 'MEDIUM'
        else:
            color = '#FF4757'
            level = 'HIGH'

        col1, col2, col3 = st.columns([3, 6, 1])
        with col1:
            st.markdown(f"**{label}**")
        with col2:
            st.progress(score / 10)
        with col3:
            st.markdown(
                f"<span style='color:{color};font-weight:bold'>"
                f"{level}</span>",
                unsafe_allow_html=True
            )
        st.caption(f"Score: {score}/10")
        st.divider()

    # LLM risk summary
    summary = st.session_state.get('risk_summary', '')
    if summary and len(summary) > 20 and 'unavailable' not in summary.lower() and 'error' not in summary.lower():
        lines = summary.split('\n')
        cleaned_lines = []
        for line in lines:
            words = line.split()
            if len(words) > 15 and len(set(words)) < 3:
                continue
            cleaned_lines.append(line)
        clean_summary = '\n'.join(cleaned_lines).strip()
        if clean_summary:
            with st.expander("AI Risk Assessment (expand)", expanded=True):
                st.markdown(clean_summary)


    st.markdown("---")

    st.info(
        "💡 **Tip:** Use the **Ask DRHP** tab to ask specific "
        "questions about risk factors mentioned in the document."
    )