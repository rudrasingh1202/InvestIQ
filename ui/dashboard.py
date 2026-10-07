"""Main dashboard layout."""

from __future__ import annotations

import streamlit as st

from ui.upload_page import render_upload_page
from ui.insights_page import render_insights_page
from ui.financials_page import render_financials_page
from ui.risk_page import render_risk_page
from ui.compare_page import render_compare_page


def render_dashboard() -> None:
    """Render the multi-tab InvestIQ dashboard (5 tabs + sidebar)."""

    st.markdown(
        """
        <style>
        /* Main app background */
        .stApp {
            background-color: #FFFFFF;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #F8FAF9;
            border-right: 1px solid #E5E7EB;
        }

        /* Cards/containers */
        div[data-testid="stVerticalBlock"] > div {
            background-color: #FFFFFF;
        }

        /* Buttons - Groww style green */
        .stButton > button {
            background-color: #00B386;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.6rem 1.5rem;
            font-weight: 600;
            transition: all 0.2s;
        }
        .stButton > button:hover {
            background-color: #00D09C;
            box-shadow: 0 4px 12px rgba(0,179,134,0.3);
        }

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            border-bottom: 1px solid #E5E7EB;
        }
        .stTabs [data-baseweb="tab"] {
            color: #6B7280;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            color: #00B386 !important;
            border-bottom: 2px solid #00B386 !important;
        }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background-color: #F8FAF9;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        div[data-testid="stMetricValue"] {
            color: #1A1A1A;
            font-weight: 700;
        }
        div[data-testid="stMetricLabel"] {
            color: #6B7280;
        }

        /* File uploader */
        [data-testid="stFileUploader"] {
            background-color: #F8FAF9;
            border: 2px dashed #00B386;
            border-radius: 12px;
            padding: 1rem;
        }

        /* Text input */
        .stTextInput > div > div > input {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            color: #1A1A1A;
        }
        .stTextInput > div > div > input:focus {
            border-color: #00B386;
            box-shadow: 0 0 0 1px #00B386;
        }

        /* Selectbox */
        .stSelectbox > div > div {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
        }

        /* Headings */
        h1, h2, h3 {
            color: #1A1A1A;
            font-weight: 700;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background-color: #F8FAF9;
            border-radius: 8px;
            color: #1A1A1A;
        }

        /* Chat messages */
        [data-testid="stChatMessage"] {
            background-color: #F8FAF9;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
        }

        /* Hide Streamlit's default deploy button and menu */
        #MainMenu { visibility: hidden; }
        header [data-testid="stToolbar"] { visibility: hidden; }
        .stDeployButton { display: none; }
        footer { visibility: hidden; }
        header { visibility: hidden; }

        /* Hide Streamlit status widget (Running... / Stop) */
        [data-testid="stStatusWidget"] { visibility: hidden; }

        /* Sidebar spacing */
        [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }

        /* Analyze button - full width */
        .stButton > button { 
            width: 100%;
            font-size: 15px;
            padding: 0.75rem 1.5rem;
            margin-top: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Initialize navigation state
    if 'show_landing' not in st.session_state:
        st.session_state['show_landing'] = True
    if 'current_module' not in st.session_state:
        st.session_state['current_module'] = None

    # Route to correct page
    if st.session_state.get('show_landing', True):
        from ui.landing_page import render_landing_page
        render_landing_page()
        return

    current = st.session_state.get('current_module', 'ipo')

    if current == 'portfolio':
        with st.sidebar:
            st.markdown("""
            <div style="
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 8px 4px 16px 4px;
            ">
                <img src="https://img.icons8.com/color/48/combo-chart--v1.png" width="40" />
                <span style="
                    font-size: 24px;
                    font-weight: 900;
                    color: #111827;
                    letter-spacing: -0.5px;
                ">Invest<span style="color: #00B386;">IQ</span></span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🏠 Home", use_container_width=True):
                st.session_state['show_landing'] = True
                st.session_state['current_module'] = None
                st.rerun()
            if st.button("💼 My Portfolio",
                         use_container_width=True):
                st.session_state['current_module'] = 'portfolio'
                st.rerun()
            st.markdown("---")
            if st.button("🏠 Back to Home",
                         use_container_width=True,
                         key="portfolio_home_btn"):
                st.session_state['show_landing'] = True
                st.session_state['current_module'] = None
                st.rerun()
        from ui.portfolio_page import render_portfolio_page
        render_portfolio_page()
        return

    if current == 'mf':
        with st.sidebar:
            st.markdown("""
            <div style="
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 8px 4px 16px 4px;
            ">
                <img src="https://img.icons8.com/color/48/combo-chart--v1.png" width="40" />
                <span style="
                    font-size: 24px;
                    font-weight: 900;
                    color: #111827;
                    letter-spacing: -0.5px;
                ">Invest<span style="color: #00B386;">IQ</span></span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🏠 Home", use_container_width=True):
                st.session_state['show_landing'] = True
                st.session_state['current_module'] = None
                st.rerun()
            if st.button("📄 IPO Intelligence",
                         use_container_width=True):
                st.session_state['current_module'] = 'ipo'
                st.rerun()
            if st.button("📈 Stock Analyzer",
                         use_container_width=True):
                st.session_state['current_module'] = 'stock'
                st.rerun()
            st.markdown("---")
            if st.button("🏠 Back to Home",
                         use_container_width=True,
                         key="mf_home_btn"):
                st.session_state['show_landing'] = True
                st.session_state['current_module'] = None
                st.rerun()
        from ui.mf_page import render_mf_page
        render_mf_page()
        return

    if current == 'stock':
        with st.sidebar:
            st.markdown("""
            <div style="
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 8px 4px 16px 4px;
            ">
                <img src="https://img.icons8.com/color/48/combo-chart--v1.png" width="40" />
                <span style="
                    font-size: 24px;
                    font-weight: 900;
                    color: #111827;
                    letter-spacing: -0.5px;
                ">Invest<span style="color: #00B386;">IQ</span></span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🏠 Home", use_container_width=True):
                st.session_state['show_landing'] = True
                st.session_state['current_module'] = None
                st.rerun()
            if st.button("📄 IPO Intelligence",
                         use_container_width=True):
                st.session_state['current_module'] = 'ipo'
                st.rerun()
            if st.button("📈 Stock Analyzer",
                         use_container_width=True):
                st.session_state['current_module'] = 'stock'
                st.rerun()
            st.markdown("---")
            if st.button("🏠 Back to Home",
                         use_container_width=True,
                         key="stock_home_btn"):
                st.session_state['show_landing'] = True
                st.session_state['current_module'] = None
                st.rerun()
        from ui.stock_page import render_stock_page
        render_stock_page()
        return

    # Default: IPO module
    render_upload_page()

    with st.sidebar:
        if st.button("📈 Stock Analyzer",
                     use_container_width=True):
            st.session_state['current_module'] = 'stock'
            st.rerun()
        if st.button("💰 MF Advisor",
                     use_container_width=True):
            st.session_state['current_module'] = 'mf'
            st.rerun()
        st.markdown("---")
        if st.button("🏠 Back to Home",
                     use_container_width=True,
                     key="ipo_home_btn"):
            st.session_state['show_landing'] = True
            st.session_state['current_module'] = None
            st.rerun()

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("## 🚀 AI-Powered IPO Intelligence")
        st.markdown(
            "**Upload DRHP/RHP → Extract → Analyze → Decide**"
        )

    with col_right:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("AI Modules", "5+")
        with c2:
            st.metric("Pages", "300+")
        with c3:
            st.metric("Engine", "RAG")

    # Feature pills using columns
    st.markdown("---")
    pill1, pill2, pill3, pill4, pill5 = st.columns(5)
    with pill1:
        st.info("📊 Financial Analysis")
    with pill2:
        st.warning("⚠️ Risk Scoring")
    with pill3:
        st.success("📈 Listing Gain")
    with pill4:
        st.info("🤖 Ask DRHP AI")
    with pill5:
        st.success("✅ Apply/Avoid")

    st.markdown("---")

    tabs = st.tabs(["Overview", "Financials", "Risk Analysis", "Verdict", "Ask DRHP"])

    with tabs[0]:
        render_insights_page()
    with tabs[1]:
        render_financials_page()
    with tabs[2]:
        render_risk_page()
    with tabs[3]:
        render_compare_page()
    with tabs[4]:
        from ui.ask_drhp_page import render_ask_drhp_page

        render_ask_drhp_page()
