"""AI insights tab."""

from __future__ import annotations

import streamlit as st


def render_insights_page() -> None:
    """Tab 1: Overview (company, issue, objects of issue, AI one-para summary)."""

    st.subheader("Overview")

    if not st.session_state.get("analysis_done"):
        st.info("Upload a DRHP/RHP PDF and click Analyze to see details.")
        return

    # Must read from session_state after Analyze
    st.write("**Company:** ", st.session_state.get("company_name", "Not disclosed in document"))
    st.write("**Sector:** ", st.session_state.get("sector", "Not disclosed in document"))
    st.write("**Issue Size:** ", st.session_state.get("issue_size", "Not disclosed in document"))
    st.write("**Price Band:** ", st.session_state.get("price_band", "Not disclosed in document"))
    st.write("**Issue Dates:** ", st.session_state.get("issue_dates", "Not disclosed in document"))

    web_source = st.session_state.get('web_data_source')
    if web_source:
        st.caption(
            f"ℹ️ Some fields fetched live from {web_source} "
            f"as they were not yet announced in the document."
        )


    st.markdown("---")

    st.write("**Objects of Issue (Summary):**")
    st.write(st.session_state.get("objects_of_issue", "Not disclosed in document"))

    st.write("**AI One-Paragraph Summary:**")
    summary = st.session_state.get("ai_summary", "")
    if not summary:
        st.caption("Click Analyze to generate summary.")
    elif any(x in summary for x in ["API Error", "error", "timed out",
                                   "Connection", "Insufficient"]):
        st.warning(summary)
        st.caption("Check VS Code terminal for details.")
    else:
        st.write(summary)





