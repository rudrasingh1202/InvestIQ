"""InvestIQ configuration.

This module centralizes constants and environment-variable access.
Logic is intentionally minimal for now (scaffolding only).
"""

from __future__ import annotations

import os
from dotenv import load_dotenv



def getenv_str(name: str, default: str | None = None) -> str | None:
    """Get an environment variable as string."""
    val = os.getenv(name)
    return default if (val is None or val == "") else val


from dotenv import load_dotenv

load_dotenv()

# API keys / LLM
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL", 
    "https://openrouter.ai/api/v1"
)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")




# RAG settings
RAG_TOP_K: int = int(getenv_str("RAG_TOP_K", "5") or "5")

# Data paths
PROJECT_ROOT: str = os.path.dirname(os.path.abspath(__file__))
DATA_DIR: str = os.path.join(PROJECT_ROOT, "data")
SAMPLE_DRHP_DIR: str = os.path.join(DATA_DIR, "sample_drhps")

