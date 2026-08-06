"""
ML Interview Assistant — Streamlit Web UI

Run with:
    streamlit run app.py

Voice CLI mode (push-to-talk, no browser):
    python main.py
"""
from __future__ import annotations

import streamlit as st

from assistant.ui.state import initialize_session_state
from assistant.ui.sidebar import render_sidebar
from assistant.ui.chat_panel import render_chat_panel
from assistant.ui.right_panel import render_right_panel


st.set_page_config(
    page_title="ML Interview Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**ML Interview Assistant** — персональный AI-ментор для подготовки "
            "к собеседованию на позицию LM / MLOps / DevOps Engineer.\n\n"
            "Режимы: Study | Diagnostic | Interview\n"
            "Голосовой CLI: `python main.py`"
        ),
    },
)


def _inject_custom_css() -> None:
    """Minimal CSS tweaks for readability."""
    st.markdown(
        """
        <style>
        /* Widen chat messages slightly */
        .stChatMessage { max-width: 100% !important; }
        /* Confidence badge colour hints */
        .stCaption { opacity: 0.9; }
        /* Keep code blocks readable */
        .stTextArea textarea { font-family: 'JetBrains Mono', monospace; font-size: 13px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    _inject_custom_css()
    initialize_session_state()
    render_sidebar()

    # Two-column layout: chat (60%) | right panel (40%)
    col_chat, col_right = st.columns([3, 2], gap="medium")

    with col_chat:
        render_chat_panel()

    with col_right:
        render_right_panel()


if __name__ == "__main__":
    main()
