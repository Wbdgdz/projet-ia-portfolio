from __future__ import annotations

from pathlib import Path

import streamlit as st
from agents import Runner

from profile_agent import build_agent
from rag_tool import bootstrap_env


PROJECT_ROOT = Path(__file__).resolve().parent
bootstrap_env(PROJECT_ROOT)


st.set_page_config(page_title="Chat Portfolio (RAG)")
st.title("Chat Portfolio (RAG)")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "previous_response_id" not in st.session_state:
    st.session_state.previous_response_id = None

agent = build_agent()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_text = st.chat_input("Pose une question sur mon profil…")
if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        try:
            result = Runner.run_sync(
                agent,
                user_text,
                previous_response_id=st.session_state.previous_response_id,
            )
            answer = result.final_output
            st.session_state.previous_response_id = result.last_response_id
        except Exception as e:
            answer = (
                "Erreur lors de l'exécution de l'agent.\n\n"
                f"Détail: {type(e).__name__}: {e}\n\n"
                "Vérifie que OPENAI_API_KEY / UPSTASH_VECTOR_REST_URL / UPSTASH_VECTOR_REST_TOKEN sont bien renseignées (dans .env ou Streamlit secrets), "
                "et que l'index a été alimenté."
            )

        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
