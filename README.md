# 🚀 InvestIQ

> AI-Powered Investment Intelligence Platform for Indian Investors

InvestIQ is an AI-driven investment research platform that simplifies complex financial analysis through intelligent automation, modern data pipelines, and LLM-powered insights.

Built for retail investors, students, and financial enthusiasts, InvestIQ helps users analyze IPOs, stocks, and (upcoming) mutual fund investments using a clean and interactive dashboard.

---

## Overview

InvestIQ combines:

- AI-powered investment analysis
- Financial data intelligence
- Large Language Models (LLMs)
- Retrieval-Augmented Generation (RAG)
- Real-time market data
- Interactive visual dashboards

The platform is designed to be modular and scalable, making it easy to add new investment modules without affecting existing functionality.

---

## Current Modules

| Module | Status |
|-------|-------|
| IPO Intelligence | Completed |
| Stock Analyzer | Completed |
| AI Buy/Sell Signal Engine | Completed |
| Peer Comparison Engine | Completed |
| Technical Indicator Analysis | Completed |
| Risk Scoring System | Completed |
| Financial Health Analysis | Completed |
| Listing Gain Prediction | Completed |
| AI Investment Verdict Generator | Completed |
| DRHP/RHP PDF Parser | Completed |
| Ask DRHP AI (RAG) | Completed |
| Mutual Fund Advisor | In Development |
| Portfolio Intelligence | Planned |
| SIP Optimizer | Planned |
| AI Wealth Planner | Planned |

---

# Key Features

### IPO Intelligence

- DRHP & RHP PDF Analysis
- Financial Health Evaluation
- IPO Risk Scoring
- Listing Gain Prediction
- Apply / Avoid Recommendation
- AI Generated IPO Summary
- AI-based DRHP Question Answering
- IPO Verdict Engine
- Company Fundamentals Analysis

---

### Stock Analyzer

- AI Buy / Sell / Hold Signals
- Financial Ratio Analysis
- Technical Indicator Analysis
- Peer Comparison Engine
- Sector Comparison Analysis
- AI Investment Verdict
- Confidence Score Generation
- Target Price Prediction
- Stop Loss Suggestions
- Investment Methodology Explanation
- Risk Assessment Engine

---

### AI Investment Engine

InvestIQ's AI engine analyzes multiple dimensions before generating recommendations.

The AI considers:

- Financial Performance
- Revenue Growth
- Profitability Trends
- Debt Analysis
- Sector Comparison
- Technical Indicators
- Market Signals
- Risk Parameters
- Peer Performance
- Fundamental Strength

---

## Tech Stack

### Frontend

- Streamlit
- Plotly
- HTML/CSS Components
- Streamlit Extras
- Custom UI Components

---

### Backend

- Python
- Pandas
- NumPy
- Requests
- BeautifulSoup
- LXML

---

### Financial Data APIs

- Yahoo Finance (yfinance)
- NSE Data Sources
- Sector Comparison Engine

---

### AI & LLM Stack

- Groq API
- OpenRouter API
- OpenAI API
- LangChain
- Gemini Models
- Ollama (Optional)
- Multi-Model Support

---

### Retrieval Augmented Generation (RAG)

- LangChain
- Document Chunking
- Semantic Retrieval
- PDF Context Pipeline
- DRHP Question Answering System

---

### PDF Processing

- PDFPlumber
- PyMuPDF
- Intelligent Section Extraction
- Financial Table Parsing
- DRHP/RHP Processing Pipeline

---

## AI Models Supported

InvestIQ is designed to support multiple AI providers.

### Supported Providers

| Provider | Support |
|--------|--------|
| Groq | Yes |
| OpenAI | Yes |
| OpenRouter | Yes |
| Gemini | Yes |
| Ollama | Yes |
| Future Models | Plug & Play |

The architecture is provider-independent, allowing seamless switching between models.

---

# Architecture

```
InvestIQ
│
├── IPO Intelligence
│
├── Stock Analyzer
│
├── AI Investment Engine
│
├── RAG Pipeline
│
├── Financial Intelligence Layer
│
├── Peer Comparison Engine
│
├── Risk Scoring Engine
│
├── Listing Gain Predictor
│
├── Technical Indicator Engine
│
└── Future Investment Modules
        │
        ├── Mutual Fund Advisor
        ├── SIP Optimizer
        ├── Portfolio Analyzer
        └── Wealth Planner
```

---

## Project Structure

```
InvestIQ/

│
├── app.py
│
├── ui/
│      ├── dashboard.py
│      ├── upload_page.py
│      ├── insights_page.py
│      ├── financials_page.py
│      ├── risk_page.py
│      ├── compare_page.py
│      └── ask_drhp_page.py
│
├── modules/
│      ├── pdf_parser.py
│      ├── section_extractor.py
│      ├── financial_analyzer.py
│      ├── risk_scorer.py
│      ├── peer_comparator.py
│      ├── listing_predictor.py
│      ├── rag_engine.py
│      └── report_generator.py
│
├── utils/
│      ├── sebi_scraper.py
│      ├── nse_data.py
│      └── helpers.py
│
├── data/
│
├── assets/
│
├── requirements.txt
│
└── README.md
```

---

# Installation

### Clone Repository

```bash
git clone <your-repository-url>
cd investiq
```

---

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Configure Environment Variables

Create a .env file.

```bash
cp .env.example .env
```

Example:

```env

# GROQ

GROQ_API_KEY=

# OPENAI

OPENAI_API_KEY=

# OPENROUTER

OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=

# MODEL

MODEL_NAME=

# OLLAMA

OLLAMA_BASE_URL=
OLLAMA_MODEL=

```

---

# Run Application

```bash
python -m streamlit run app.py
```

Application will be available at:

```
http://localhost:8501
```

---

## Investment Intelligence Workflow

### IPO Module

```
Upload PDF

↓

Extract Data

↓

Financial Analysis

↓

Risk Analysis

↓

AI Summary

↓

Listing Gain Prediction

↓

AI Verdict

↓

Apply / Avoid Recommendation
```

---

### Stock Analyzer

```
Enter Stock Symbol

↓

Fetch Market Data

↓

Technical Analysis

↓

Financial Analysis

↓

Peer Comparison

↓

AI Analysis

↓

Buy / Sell Signal

↓

Target Price & Stop Loss

↓

Investment Verdict
```

---

## Session State Design

InvestIQ uses Streamlit's session state architecture for modular and scalable development.

Current modules communicate through:

```
st.session_state
```

This design allows:

- Independent module development
- Easy feature addition
- Flexible AI integrations
- Seamless UI expansion
- Future investment modules support

---

## Future Roadmap

### Phase 1 (Completed)

- IPO Intelligence
- Stock Analyzer
- AI Buy/Sell Signals
- RAG Integration
- Peer Comparison

---

### Phase 2 (In Development)

- Mutual Fund Advisor
- AI Fund Recommendation Engine
- SIP Recommendation System
- Fund Risk Analysis
- Fund Comparison Dashboard

---

### Phase 3

- Portfolio Analyzer
- Wealth Planning
- Retirement Planning
- AI Financial Assistant
- Portfolio Optimization
- Multi Asset Allocation

---

## Why InvestIQ?

InvestIQ is designed to bridge the gap between traditional investment research and modern AI capabilities.

The platform aims to provide:

- Faster investment analysis
- Intelligent financial insights
- Beginner-friendly investment decisions
- Modular AI-powered workflows
- Scalable architecture for future financial products

---

## Built With

```
Python
Streamlit
LangChain
Groq
OpenAI
OpenRouter
Gemini
Yahoo Finance
Plotly
Pandas
NumPy
PDFPlumber
PyMuPDF
RAG
LLMs
```

---

## License

```
MIT License
```

---

## Author

### Rudra Singh

B.Tech CSE (AI & ML)

---

> InvestIQ – Transforming Investment Research with Artificial Intelligence.