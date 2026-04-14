"""
Interview timer — auto-refreshing countdown for mock interview mode.

Uses st.fragment(run_every=1) for isolated per-second reruns
that don't interrupt the main chat panel.
"""
from __future__ import annotations

import time
from datetime import timedelta

import streamlit as st

from assistant.config import settings


def _format_time(seconds: float) -> str:
    td = timedelta(seconds=max(0, int(seconds)))
    total_seconds = int(td.total_seconds())
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


@st.fragment(run_every=1)
def render_timer() -> None:
    """
    Renders an interview countdown timer that refreshes every second.

    Isolated via st.fragment so it doesn't trigger full page reruns.
    """
    duration_sec = settings.interview_timer_minutes * 60

    timer_active: bool = st.session_state.get("timer_active", False)
    timer_start: float | None = st.session_state.get("timer_start")

    col_btn, col_time = st.columns([1, 1])

    with col_btn:
        if not timer_active:
            if st.button("▶️ Старт таймера", use_container_width=True, key="timer_start_btn"):
                st.session_state.timer_active = True
                st.session_state.timer_start = time.time()
                st.rerun()
        else:
            if st.button("⏹️ Сброс", use_container_width=True, key="timer_stop_btn"):
                st.session_state.timer_active = False
                st.session_state.timer_start = None
                st.rerun()

    with col_time:
        if timer_active and timer_start is not None:
            elapsed = time.time() - timer_start
            remaining = duration_sec - elapsed

            if remaining <= 0:
                st.error("⏰ Время вышло!")
                st.session_state.timer_active = False
                st.session_state.timer_start = None
                # Inject a system message to trigger final interview summary
                if "messages" in st.session_state:
                    timeout_msg = "⏰ Время интервью истекло. Подведи итоги: оцени кандидата по рубрике."
                    st.session_state.messages.append({
                        "role": "user",
                        "content": timeout_msg,
                    })
            else:
                color = "normal" if remaining > 120 else "inverse"
                st.metric(
                    label=f"⏱️ {settings.interview_timer_minutes} мин",
                    value=_format_time(remaining),
                    delta=None,
                    label_visibility="visible",
                )
        else:
            st.metric(
                label=f"⏱️ {settings.interview_timer_minutes} мин",
                value=f"{settings.interview_timer_minutes:02d}:00",
                label_visibility="visible",
            )
