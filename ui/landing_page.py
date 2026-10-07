import streamlit as st

LOGO_URL = "https://img.icons8.com/color/48/combo-chart--v1.png"
LOGO_WIDTH = 56


def render_landing_page():
    # My Portfolio button at true top-right using columns
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("💼 My Portfolio", type="primary", key="btn_portfolio", use_container_width=False):
            st.session_state['current_module'] = 'portfolio'
            st.session_state['show_landing'] = False
            st.rerun()

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    html = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

.landing-wrapper {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 20px 20px;
    font-family: 'Inter', sans-serif;
}}

.brand-header {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 18px;
    margin-bottom: 10px;
}}

.brand-title {{
    font-size: 52px;
    font-weight: 900;
    letter-spacing: -1.5px;
    line-height: 1;
    color: #111827;
}}
.brand-title span {{
    color: #00B386;
}}

.brand-tagline {{
    text-align: center;
    font-size: 16px;
    color: #6B7280;
    font-weight: 400;
    margin-bottom: 40px;
    letter-spacing: 0.3px;
}}

.stats-row {{
    display: flex;
    gap: 16px;
    margin-bottom: 40px;
}}
.stat-card {{
    flex: 1;
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 20px 16px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.stat-value {{
    font-size: 24px;
    font-weight: 800;
    color: #00B386;
    margin-bottom: 4px;
}}
.stat-label {{
    font-size: 11px;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 600;
}}

.section-title {{
    font-size: 22px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 16px;
}}

.modules-row {{
    display: flex;
    gap: 20px;
    margin-bottom: 36px;
}}
.module-card {{
    flex: 1;
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    display: flex;
    flex-direction: column;
    min-height: 320px;
}}
.module-card-head {{
    margin-bottom: 14px;
}}
.module-card-title {{
    font-size: 17px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 12px;
}}
.module-features {{
    flex: 1;
    margin-bottom: 18px;
    padding-left: 18px;
}}
.module-features li {{
    font-size: 13px;
    color: #4B5563;
    line-height: 1.6;
    margin-bottom: 2px;
}}
.module-badge {{
    display: inline-block;
    background: #F3F4F6;
    color: #9CA3AF;
    font-size: 10px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 12px;
}}
.module-badge.ready {{
    background: #ECFDF5;
    color: #00B386;
}}

.landing-footer {{
    text-align: center;
    font-size: 12px;
    color: #9CA3AF;
    padding-top: 10px;
}}
.landing-footer strong {{
    color: #6B7280;
}}

#btn_portfolio > button {{
    background-color: #FFFFFF;
    color: #00B386;
    border: 2px solid #00B386;
    border-radius: 10px;
    padding: 8px 20px;
    font-weight: 700;
    font-size: 14px;
    font-family: 'Inter', sans-serif;
    transition: all 0.2s;
    box-shadow: 0 2px 6px rgba(0,179,134,0.15);
}}
#btn_portfolio > button:hover {{
    background-color: #00B386;
    color: #FFFFFF;
    box-shadow: 0 4px 12px rgba(0,179,134,0.3);
}}
</style>

<div class="landing-wrapper">
    <div class="brand-header">
        <img src="{LOGO_URL}" width="{LOGO_WIDTH}" />
        <div class="brand-title">Invest<span>IQ</span></div>
    </div>
    <div class="brand-tagline">AI Powered Investment Intelligence Platform</div>

    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-value">300+</div>
            <div class="stat-label">Pages Analyzed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">5+</div>
            <div class="stat-label">AI Modules</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">RAG</div>
            <div class="stat-label">Powered QnA</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">Live</div>
            <div class="stat-label">Market Data</div>
        </div>
    </div>

    <div class="section-title">Modules</div>
    <div class="modules-row">
        <div class="module-card">
            <div class="module-card-head">
                <span class="module-badge ready">Ready</span>
                <div class="module-card-title">📄 IPO Intelligence</div>
            </div>
            <ul class="module-features">
                <li>AI DRHP/RHP analysis</li>
                <li>Risk scoring</li>
                <li>Financial analysis</li>
                <li>Listing gain prediction</li>
            </ul>
        </div>
        <div class="module-card">
            <div class="module-card-head">
                <span class="module-badge ready">Ready</span>
                <div class="module-card-title">📈 Stock Analyzer</div>
            </div>
            <ul class="module-features">
                <li>Live NSE/BSE analysis</li>
                <li>Technical indicators</li>
                <li>AI Buy/Sell signals</li>
            </ul>
        </div>
        <div class="module-card">
            <div class="module-card-head">
                <span class="module-badge ready">Ready</span>
                <div class="module-card-title">💰 MF Advisor</div>
            </div>
            <ul class="module-features">
                <li>AI mutual fund recommendations</li>
                <li>Goal based investing</li>
                <li>Portfolio allocation</li>
            </ul>
        </div>
    </div>
</div>
"""

    st.html(html)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button(
            "Open IPO Intelligence",
            type="primary",
            use_container_width=True,
            key="btn_ipo"
        ):
            st.session_state['current_module'] = 'ipo'
            st.session_state['show_landing'] = False
            st.rerun()
    with b2:
        if st.button(
            "Open Stock Analyzer",
            type="secondary",
            use_container_width=True,
            key="btn_stock"
        ):
            st.session_state['current_module'] = 'stock'
            st.session_state['show_landing'] = False
            st.rerun()
    with b3:
        if st.button(
            "Open MF Advisor",
            type="primary",
            use_container_width=True,
            key="btn_mf"
        ):
            st.session_state['current_module'] = 'mf'
            st.session_state['show_landing'] = False
            st.rerun()

    footer_html = """
<div class="landing-footer">
    <strong>InvestIQ</strong> • AI Powered Investment Intelligence Platform<br/>
    Not Financial Advice
</div>
"""
    st.html(footer_html)
