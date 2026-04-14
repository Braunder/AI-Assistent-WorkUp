"""
Sidebar — mode selector, progress tracker, session history, export buttons.
"""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from assistant.config import settings
from assistant.ui.state import get_assistant, run_async, save_chat_draft
from assistant.tools.export import (
    export_to_markdown,
    export_to_pdf,
    import_chat_from_json,
    import_chat_from_markdown,
)


_MODE_LABELS = {
    "study": "📖 Study — пошаговое обучение",
    "diagnostic": "🔬 Diagnostic — быстрая оценка пробелов",
    "interview": "🎤 Interview — mock собеседование",
}
_MODE_KEYS = list(_MODE_LABELS.keys())


def _render_mode_selector(assistant) -> None:
    st.subheader("⚙️ Режим обучения")
    current_idx = _MODE_KEYS.index(assistant._coach_mode) if assistant._coach_mode in _MODE_KEYS else 0
    selected_label = st.radio(
        "Выбери режим:",
        options=list(_MODE_LABELS.values()),
        index=current_idx,
        key="mode_radio",
        label_visibility="collapsed",
    )
    selected_mode = _MODE_KEYS[list(_MODE_LABELS.values()).index(selected_label)]
    if selected_mode != assistant._coach_mode:
        assistant._coach_mode = selected_mode
        st.success(f"Режим: **{selected_mode}**")

    # Interview timer toggle
    if selected_mode == "interview":
        from assistant.ui.timer import render_timer
        render_timer()


def _render_progress(assistant) -> None:
    st.subheader("📊 Прогресс")
    progress_items = assistant.get_progress_items()
    weak_topics = assistant.get_weak_topics()

    col1, col2 = st.columns(2)
    col1.metric("✅ Тем изучено", len(progress_items))
    col2.metric("⚠️ Слабых мест", len(weak_topics))

    if progress_items:
        with st.expander("Детали прогресса", expanded=False):
            for item in progress_items[-10:]:  # last 10
                st.markdown(f"- {item}")

    if weak_topics:
        with st.expander("Слабые места", expanded=False):
            for item in weak_topics[-10:]:
                st.warning(item)


def _render_history(assistant) -> None:
    st.subheader("🕐 История сессий")
    sessions = assistant.get_session_history()
    if not sessions:
        st.caption("Нет сохранённых сессий. Они появятся после авто-сохранения.")
        return

    for i, summary in enumerate(reversed(sessions[-5:]), start=1):
        with st.expander(f"Сессия {i}", expanded=False):
            st.markdown(summary)

    # Manual save button
    if st.button("💾 Сохранить сессию сейчас", use_container_width=True):
        with st.spinner("Сохраняю..."):
            result = run_async(assistant.save_session())
        st.success(result)
        st.rerun()


def _render_export(assistant) -> None:
    st.subheader("📤 Экспорт")
    notes_path = settings.notes_file_path
    try:
        notes_text = notes_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        notes_text = ""

    progress_items = assistant.get_progress_items()
    weak_topics = assistant.get_weak_topics()
    chat_messages = st.session_state.get("messages", [])
    md_content = export_to_markdown(
        notes_text,
        progress_items,
        weak_topics,
        chat_messages=chat_messages,
    )

    col_md, col_pdf = st.columns(2)
    with col_md:
        st.download_button(
            label="📄 Markdown",
            data=md_content.encode("utf-8"),
            file_name=f"ml_assistant_export_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_pdf:
        try:
            pdf_bytes = export_to_pdf(md_content)
            st.download_button(
                label="📑 PDF",
                data=pdf_bytes,
                file_name=f"ml_assistant_export_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except ImportError:
            st.caption("PDF: установи fpdf2")


def _render_import() -> None:
    st.subheader("📥 Импорт диалога")
    uploaded = st.file_uploader(
        "Загрузи экспорт диалога (.md или .json)",
        type=["md", "markdown", "json"],
        key="chat_import_uploader",
    )
    if uploaded is None:
        return

    try:
        raw_text = uploaded.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        st.error("Файл должен быть в UTF-8.")
        return

    suffix = uploaded.name.lower().rsplit(".", 1)[-1] if "." in uploaded.name else ""
    try:
        if suffix == "json":
            imported_messages = import_chat_from_json(raw_text)
        else:
            imported_messages = import_chat_from_markdown(raw_text)
    except ValueError as exc:
        st.error(str(exc))
        return

    if not imported_messages:
        st.warning("Не удалось найти сообщения в файле.")
        return

    st.caption(f"Найдено сообщений: {len(imported_messages)}")
    if st.button("🔁 Импортировать и продолжить", use_container_width=True, type="primary"):
        st.session_state.messages = imported_messages
        st.session_state.rag_sources = []
        st.session_state.last_confidence = None
        st.session_state.verify_result = None
        st.session_state.last_assistant_text = (
            imported_messages[-1]["content"] if imported_messages[-1]["role"] == "assistant" else ""
        )
        save_chat_draft(imported_messages)
        st.success("Диалог импортирован. Можно продолжать чат.")
        st.rerun()


def render_sidebar() -> None:
    """Entry point: renders the full sidebar."""
    assistant = get_assistant()
    with st.sidebar:
        st.title("🤖 ML Interview")
        st.caption("Ассистент для подготовки к собеседованию")
        st.divider()

        _render_mode_selector(assistant)
        st.divider()
        _render_progress(assistant)
        st.divider()
        _render_history(assistant)
        st.divider()
        _render_export(assistant)
        st.divider()
        _render_import()
