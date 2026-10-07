"""RAG engine for Ask DRHP.

Implements a pure scikit-learn TF-IDF in-memory vector store (no PyTorch, no
onnxruntime, no Chroma) and OpenRouter-backed answers using ONLY retrieved
context.
"""

from __future__ import annotations

from typing import Any

import config
import numpy as np
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from utils.helpers import call_llm


class TfidfVectorStore:
    """In-memory TF-IDF vector store with LangChain-compatible interface."""

    def __init__(self, chunks: list[str]) -> None:
        self.chunks = chunks
        self._vectorizer = TfidfVectorizer(
            max_features=2048,
            ngram_range=(1, 2),
            stop_words="english",
        )
        self._matrix = self._vectorizer.fit_transform(chunks)

    def similarity_search(self, query: str, k: int = 4) -> list[Document]:
        query_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self._matrix)[0]
        top_idx = np.argsort(sims)[::-1][:k]
        return [
            Document(page_content=self.chunks[i])
            for i in top_idx
            if sims[i] > 0.0
        ]


def _chunk_text(raw_text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " "],
    )
    return splitter.split_text(raw_text)


def build_vector_store(sections_dict: dict[str, str]) -> TfidfVectorStore:
    """Build a TF-IDF vector store from extracted DRHP sections."""
    full_text = " ".join([v for v in sections_dict.values() if isinstance(v, str) and v.strip()])
    chunks = _chunk_text(full_text) if full_text.strip() else [""]
    return TfidfVectorStore(chunks)


@st.cache_resource(show_spinner="Building Q&A knowledge base...")
def get_vectorstore(raw_text: str) -> TfidfVectorStore | None:
    """Build or return a cached TF-IDF vector store from raw DRHP text."""
    if not raw_text or not raw_text.strip():
        return None
    chunks = _chunk_text(raw_text)
    return TfidfVectorStore(chunks)


def ask_drhp(question: str, vectorstore) -> str:
    try:
        docs = vectorstore.similarity_search(question, k=5)
    except Exception as e:
        return f"Search error: {str(e)}"

    if not docs:
        return "This information is not available in the uploaded document."

    # Keep context under 1200 chars to save tokens
    context = ""
    for doc in docs:
        if len(context) + len(doc.page_content) < 1200:
            context += doc.page_content + "\n---\n"

    prompt = f"""You are an expert IPO analyst.
Answer using ONLY the context below.
Be specific — include exact names, addresses,
numbers, dates from the context.
If not in context say "Not found in document."
Never say "details are set out below" — give the actual detail.

Context:
{context}

Question: {question}
Direct Answer:"""

    try:
        from utils.helpers import call_llm
        answer = call_llm(
            prompt=prompt,
            system_prompt="Answer questions about IPO documents precisely.",
            max_tokens=100
        )
        from utils.helpers import clean_llm_response
        return clean_llm_response(answer)
    except Exception as e:
        return f"Error: {str(e)}"

