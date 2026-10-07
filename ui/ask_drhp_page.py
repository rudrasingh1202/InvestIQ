"""Ask DRHP chat UI.

Goal: when user clicks Analyze and vectorstore is built, Ask DRHP must answer.
If not ready, show a clear instruction.
"""

from __future__ import annotations

import streamlit as st

from modules.rag_engine import ask_drhp, get_vectorstore


def render_ask_drhp_page() -> None:
    st.subheader("Ask DRHP")
    st.caption("Ask any question about the uploaded DRHP document.")

    st.session_state.setdefault("chat_history", [])

    # Render history
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_question = st.chat_input("Type your question about the DRHP...")

    if not user_question:
        return

    st.session_state["chat_history"].append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.write(user_question)

    raw_text = st.session_state.get("raw_text", "")
    vectorstore = get_vectorstore(raw_text)

    if vectorstore is None:
        assistant = "Upload a DRHP/RHP PDF and click Analyze first so I can search the document."
        with st.chat_message("assistant"):
            st.write(assistant)
        st.session_state["chat_history"].append({"role": "assistant", "content": assistant})
        return

    with st.chat_message("assistant"):
        with st.spinner("Searching DRHP..."):
            answer = ask_drhp(user_question, vectorstore)
            st.write(answer)

    st.session_state["chat_history"].append({"role": "assistant", "content": answer})

