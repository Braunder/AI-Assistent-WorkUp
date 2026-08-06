"""
Chat panel — left/main column of the Streamlit UI.

Renders conversation history, streams new assistant responses,
displays confidence badges, and shows a Verify button per message.
"""
from __future__ import annotations

import hashlib

import streamlit as st

from assistant.ui.state import get_assistant, get_tts_engine, run_async, save_chat_draft, sync_stream


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


def _tts_key_for_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def _synthesize_tts_audio(text: str) -> bytes | None:
    if not text or not st.session_state.get("web_tts_enabled", False):
        return None

    tts_engine = get_tts_engine()
    spoken_text = tts_engine.prepare_text_for_tts(text)
    if not spoken_text:
        return None

    try:
        return run_async(tts_engine.synthesize_wav(spoken_text))
    except Exception:
        return None


def render_chat_history() -> None:
    """Render all stored messages from session_state."""
    audio_cache = st.session_state.get("web_tts_audio_cache", {})
    autoplay_key = st.session_state.get("web_tts_autoplay_key")

    for idx, msg in enumerate(st.session_state.messages):
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

                if st.session_state.get("web_tts_enabled", False):
                    cache_key = _tts_key_for_text(msg["content"])
                    col_tts, col_tts_status = st.columns([1, 3])
                    with col_tts:
                        if st.button("🔊 Озвучить", key=f"tts_play_{idx}_{cache_key[:8]}"):
                            audio_bytes = audio_cache.get(cache_key)
                            if audio_bytes is None:
                                audio_bytes = _synthesize_tts_audio(msg["content"])
                                if audio_bytes:
                                    audio_cache[cache_key] = audio_bytes
                                    st.session_state.web_tts_audio_cache = audio_cache
                            if audio_bytes:
                                st.audio(audio_bytes, format="audio/wav", autoplay=True)
                            else:
                                st.caption("Нечего озвучивать (ответ в основном код/символы) или TTS недоступен.")

                    with col_tts_status:
                        if cache_key in audio_cache:
                            st.caption("Аудио готово")

                    if autoplay_key and autoplay_key == cache_key and cache_key in audio_cache:
                        st.audio(audio_cache[cache_key], format="audio/wav", autoplay=True)
                        st.session_state.web_tts_autoplay_key = None


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

    # Generate web TTS audio for the last answer (if enabled), then autoplay on rerun.
    if st.session_state.get("web_tts_enabled", False):
        cache_key = _tts_key_for_text(full_response)
        audio_cache = st.session_state.get("web_tts_audio_cache", {})
        if cache_key not in audio_cache:
            audio_bytes = _synthesize_tts_audio(full_response)
            if audio_bytes:
                audio_cache[cache_key] = audio_bytes
                st.session_state.web_tts_audio_cache = audio_cache
        if st.session_state.get("web_tts_autoplay", True) and cache_key in st.session_state.get("web_tts_audio_cache", {}):
            st.session_state.web_tts_autoplay_key = cache_key

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
