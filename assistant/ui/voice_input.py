"""
Voice input widget for the Streamlit UI.

Uses st.audio_input() (Streamlit >= 1.31) to capture microphone audio,
converts the uploaded bytes to a numpy array, and transcribes via the
existing faster-whisper STT pipeline.

NOTE: On HTTP localhost, browsers require explicit microphone permission.
If the microphone button is blocked, use the CLI push-to-talk mode (main.py).
"""
from __future__ import annotations

import hashlib
import io

import streamlit as st


def render_voice_button() -> str | None:
    """
    Render a compact voice input widget.

    Returns:
        Transcribed text string if audio was recorded and transcribed,
        None otherwise.
    """
    with st.expander("🎤 Голосовой ввод (нажми для записи)", expanded=False):
        st.caption(
            "Запиши голосовое сообщение. Браузер запросит доступ к микрофону.\n"
            "Если заблокировано — используй **main.py** (CLI push-to-talk)."
        )
        nonce = st.session_state.get("voice_audio_nonce", 0)
        audio_value = st.audio_input(
            label="Запись",
            key=f"voice_audio_input_{nonce}",
            label_visibility="collapsed",
        )

        if audio_value is None:
            return None

        audio_bytes = audio_value.read()
        if not audio_bytes:
            return None

        signature = hashlib.sha1(audio_bytes).hexdigest()
        last_signature = st.session_state.get("voice_last_signature")
        if signature == last_signature:
            # Same recording seen again after rerun; skip duplicate processing.
            return None
        st.session_state.voice_last_signature = signature

        with st.spinner("Расшифровываю речь..."):
            try:
                text = _transcribe_audio_bytes(audio_bytes)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Ошибка транскрипции: {exc}")
                return None

        if text:
            st.success(f"Распознано: *{text}*")
            return text

    return None


def _transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """Convert raw audio bytes from st.audio_input to transcribed text."""
    import numpy as np
    import scipy.io.wavfile as wav  # type: ignore[import-untyped]

    from assistant.voice.stt import transcribe

    # st.audio_input returns WAV bytes
    sample_rate, audio_array = wav.read(io.BytesIO(audio_bytes))

    # Convert to float32 mono if needed
    if audio_array.ndim > 1:
        audio_array = audio_array.mean(axis=1)

    if audio_array.dtype != np.float32:
        audio_array = audio_array.astype(np.float32)
        if audio_array.max() > 1.0:
            audio_array /= 32768.0  # normalise int16 PCM to [-1, 1]

    return transcribe(audio_array, sample_rate)
