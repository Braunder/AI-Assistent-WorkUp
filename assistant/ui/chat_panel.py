"""
Chat panel — left/main column of the Streamlit UI.

Renders conversation history, streams new assistant responses,
displays confidence badges, and shows a Verify button per message.
"""
from __future__ import annotations

import streamlit as st

from assistant.ui.state import get_assistant, save_chat_draft, sync_stream


def _confidence_badge(confidence: dict | None) -> str:
    """Return a coloured emoji badge string for the given confidence dict."""
    if confidence is None:
        return ""
    score: int = confidence.get("score", 0)
    reason: str = confidence.get("reason", "")
    if score >= 4:
        emoji = "🟢"
    elif score == 3:
        emoji = "🟡"
    else:
        emoji = "🔴"
    return f"{emoji} **Уверенность: {score}/5** — {reason}"


def render_chat_history() -> None:
    """Render all stored messages from session_state."""
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                conf = msg.get("confidence")
                if conf:
                    badge = _confidence_badge(conf)
                    if conf.get("score", 5) <= 2:
                        st.warning(badge + "  \n⚠️ Рекомендуем нажать **Verify** для проверки факта.")
                    else:
                        st.caption(badge)


def render_input_area(history_container: st.delta_generator.DeltaGenerator) -> None:
    """Chat input + voice button row. Processes new user messages."""
    assistant = get_assistant()

    # Voice input — rendered above the chat input
    from assistant.ui.voice_input import render_voice_button
    voice_text = render_voice_button()

    # Determine the prompt: voice transcription takes priority over typed input
    prompt: str | None = voice_text or st.chat_input(
        "Введи сообщение или используй 🎤...",
        key="main_chat_input",
    )

    if not prompt:
        return

    # Add user message to history and display it inside the scrollable history panel
    st.session_state.messages.append({"role": "user", "content": prompt})
    with history_container:
        with st.chat_message("user"):
            st.markdown(prompt)

        # Stream the assistant response in the same scrollable container
        with st.chat_message("assistant"):
            full_response: str = st.write_stream(sync_stream(assistant, prompt))

    # After stream finishes, snapshot confidence + sources from the assistant
    confidence = assistant.last_confidence
    rag_sources = list(assistant.last_rag_sources)

    # Update session state
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response, "confidence": confidence}
    )
    save_chat_draft(st.session_state.messages)
    st.session_state.rag_sources = rag_sources
    st.session_state.last_confidence = confidence
    st.session_state.last_assistant_text = full_response
    st.session_state.verify_result = None  # reset verify on new message
    st.session_state.code_saved = False

    # Reset audio widget after successful voice submit to avoid replay on rerun.
    if voice_text:
        st.session_state.voice_audio_nonce = st.session_state.get("voice_audio_nonce", 0) + 1

    st.rerun()


def render_chat_panel() -> None:
    """Entry point: renders the full chat column."""
    st.header("💬 ML Interview Assistant", divider="blue")

    # Fixed-height history region with its own scrollbar.
    history_container = st.container(height=620, border=True)
    with history_container:
        render_chat_history()

    render_input_area(history_container)
