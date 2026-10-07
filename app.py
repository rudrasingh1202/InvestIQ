"""InvestIQ Streamlit entry point."""

from __future__ import annotations

import streamlit as st

from ui.dashboard import render_dashboard


def main() -> None:
    """Run the InvestIQ Streamlit app."""
    st.set_page_config(
        page_title="InvestIQ",
        page_icon="📈",
        layout="wide",
    )

    render_dashboard()


if __name__ == "__main__":
    main()

