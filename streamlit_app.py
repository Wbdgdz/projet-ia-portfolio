from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import streamlit as st
from agents import Runner

from chat_store import load_chat_state, save_chat_state
from profile_sections import list_profile_sections_impl
from profile_agent import build_agent
from rag_tool import bootstrap_env


PROJECT_ROOT = Path(__file__).resolve().parent
bootstrap_env(PROJECT_ROOT)


def _setup_page() -> None:
    st.set_page_config(page_title="Chat Portfolio (RAG)")
    st.title("Chat Portfolio (RAG)")


def _get_query_params() -> dict[str, list[str]]:
    try:
        return {k: list(v) for k, v in st.query_params.items()}  # type: ignore[attr-defined]
    except Exception:
        return st.experimental_get_query_params()  # type: ignore[attr-defined]


def _set_query_params(**kwargs: str) -> None:
    try:
        st.query_params.update(kwargs)  # type: ignore[attr-defined]
    except Exception:
        st.experimental_set_query_params(**kwargs)  # type: ignore[attr-defined]


def _reset_conversation() -> None:
    new_cid = uuid4().hex
    st.session_state.conversation_id = new_cid
    st.session_state.messages = []
    st.session_state.previous_response_id = None
    _set_query_params(cid=new_cid)
    save_chat_state(new_cid, messages=[], previous_response_id=None)
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()  # type: ignore[attr-defined]


def _render_sidebar() -> None:
    with st.sidebar:
        st.header("Options")
        if st.button("Réinitialiser la conversation"):
            _reset_conversation()

        st.divider()
        st.subheader("Sections disponibles")
        st.markdown(list_profile_sections_impl())


def _init_session_state() -> None:
    if "conversation_id" not in st.session_state:
        qp = _get_query_params()
        cid = (qp.get("cid") or [""])[0].strip()
        if not cid:
            cid = uuid4().hex
            _set_query_params(cid=cid)
        st.session_state.conversation_id = cid

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "previous_response_id" not in st.session_state:
        st.session_state.previous_response_id = None


def _load_persisted_history() -> None:
    if "loaded_persisted_history" in st.session_state:
        return

    st.session_state.loaded_persisted_history = True
    state = load_chat_state(st.session_state.conversation_id)
    if state and isinstance(state.get("messages"), list):
        st.session_state.messages = [
            m
            for m in state.get("messages", [])
            if isinstance(m, dict) and m.get("role") in {"user", "assistant"}
        ]
        st.session_state.previous_response_id = state.get("previous_response_id")


def _render_messages() -> None:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def _run_agent(agent, user_text: str) -> str:
    try:
        result = Runner.run_sync(
            agent,
            user_text,
            previous_response_id=st.session_state.previous_response_id,
        )
        st.session_state.previous_response_id = result.last_response_id
        return result.final_output
    except Exception as e:
        return (
            "Erreur lors de l'exécution de l'agent.\n\n"
            f"Détail: {type(e).__name__}: {e}\n\n"
            "Vérifie que OPENAI_API_KEY / UPSTASH_VECTOR_REST_URL / UPSTASH_VECTOR_REST_TOKEN sont bien renseignées (dans .env ou Streamlit secrets), "
            "et que l'index a été alimenté."
        )


def _handle_user_input(agent) -> None:
    user_text = st.chat_input("Pose une question sur mon profil…")
    if not user_text:
        return

    st.session_state.messages.append({"role": "user", "content": user_text})
    save_chat_state(
        st.session_state.conversation_id,
        messages=st.session_state.messages,
        previous_response_id=st.session_state.previous_response_id,
    )
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        answer = _run_agent(agent, user_text)
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    save_chat_state(
        st.session_state.conversation_id,
        messages=st.session_state.messages,
        previous_response_id=st.session_state.previous_response_id,
    )


def main() -> None:
    _setup_page()
    _render_sidebar()
    _init_session_state()
    _load_persisted_history()

    agent = build_agent()
    _render_messages()
    _handle_user_input(agent)


main()
