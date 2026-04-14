"""
Right panel — tabbed panel with RAG sources, code editor, and verify tab.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import hashlib
import streamlit as st

from assistant.config import settings
from assistant.ui.state import get_assistant, run_async


def _render_rag_tab() -> None:
    sources = st.session_state.get("rag_sources", [])
    if not sources:
        st.info("Источники появятся после первого сообщения.")
        return

    session_sources = [s for s in sources if s.get("type") != "knowledge"]
    kb_sources = [s for s in sources if s.get("type") == "knowledge"]

    if session_sources:
        st.markdown("**📚 Из прошлых сессий**")
        for src in session_sources:
            score = src.get("score", 0.0)
            score_bar = min(1.0, max(0.0, float(score)))
            with st.container(border=True):
                st.progress(score_bar, text=f"Релевантность: {score:.2f}")
                st.caption(src.get("text", "")[:300])

    if kb_sources:
        st.markdown("**🧭 Из базы знаний**")
        for src in kb_sources:
            score = src.get("score", 0.0)
            score_bar = min(1.0, max(0.0, float(score)))
            with st.container(border=True):
                st.progress(score_bar, text=f"Релевантность: {score:.2f}")
                src_label = src.get("source", "knowledge base")
                st.caption(f"**{src_label}**")
                st.caption(src.get("text", "")[:300])


def _render_code_tab() -> None:
    practice_path = settings.practice_file_path

    def _hash_text(text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def _normalise_newlines(text: str) -> str:
        # Streamlit/Ace can return CRLF on Windows; write LF to prevent
        # \r\r\n expansion in text mode and line-count doubling.
        return text.replace("\r\n", "\n").replace("\r", "\n")

    try:
        disk_content = practice_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        disk_content = "# practice.py — пока пуст\n"

    disk_hash = _hash_text(disk_content)

    # First load from disk
    if st.session_state.get("code_editor_content") is None:
        st.session_state.code_editor_content = disk_content
        st.session_state.code_editor_saved_hash = disk_hash

    current_buffer = st.session_state.code_editor_content
    saved_hash = st.session_state.get("code_editor_saved_hash")
    is_dirty = _hash_text(_normalise_newlines(current_buffer)) != saved_hash

    # If file changed externally and editor is clean, auto-sync from disk.
    if disk_hash != saved_hash and not is_dirty:
        st.session_state.code_editor_content = disk_content
        st.session_state.code_editor_saved_hash = disk_hash
        st.session_state.code_editor_nonce = st.session_state.get("code_editor_nonce", 0) + 1

    # If file changed externally while editor is dirty, warn user.
    if disk_hash != saved_hash and is_dirty:
        st.warning("Файл practice.py изменился на диске (возможно, моделью). Нажми 'Обновить', чтобы подтянуть изменения.")

    st.caption(f"📄 `{practice_path.name}` — редактируй и сохраняй:")

    edited: str
    editor_key = f"code_ace_editor_{st.session_state.get('code_editor_nonce', 0)}"
    try:
        from streamlit_ace import st_ace  # type: ignore[import-not-found]

        edited = st_ace(
            value=st.session_state.code_editor_content,
            language="python",
            theme="monokai",
            key=editor_key,
            height=460,
            font_size=14,
            tab_size=4,
            wrap=True,
            auto_update=True,
            show_gutter=True,
            show_print_margin=False,
            min_lines=24,
            max_lines=60,
        )
        if edited is None:
            edited = st.session_state.code_editor_content
    except Exception:
        st.info("Для удобного Tab-редактора установи пакет `streamlit-ace`.")
        edited = st.text_area(
            label="practice.py",
            value=st.session_state.code_editor_content,
            height=460,
            key="code_textarea",
            label_visibility="collapsed",
        )

    # Keep the latest buffer in session state for action buttons below.
    st.session_state.code_editor_content = edited

    col_save, col_reload, col_check, col_run = st.columns(4)
    with col_save:
        if st.button("💾 Сохранить", use_container_width=True, type="primary"):
            try:
                normalised = _normalise_newlines(edited)
                practice_path.write_text(normalised, encoding="utf-8", newline="\n")
                st.session_state.code_editor_content = normalised
                st.session_state.code_editor_saved_hash = _hash_text(normalised)
                st.session_state.code_saved = True
                st.success("Сохранено!")
            except OSError as exc:
                st.error(f"Ошибка записи: {exc}")

    with col_reload:
        if st.button("🔄 Обновить", use_container_width=True):
            try:
                latest = practice_path.read_text(encoding="utf-8")
                st.session_state.code_editor_content = latest
                st.session_state.code_editor_saved_hash = _hash_text(latest)
                st.session_state.code_editor_nonce = st.session_state.get("code_editor_nonce", 0) + 1
                st.rerun()
            except FileNotFoundError:
                st.warning("Файл не найден.")

    with col_check:
        if st.button("✅ Проверить", use_container_width=True):
            try:
                compile(edited, str(practice_path), "exec")
                st.success("Синтаксис OK")
            except SyntaxError as exc:
                st.error(
                    f"Синтаксическая ошибка: строка {exc.lineno}, col {exc.offset}: {exc.msg}"
                )

    with col_run:
        if st.button("▶️ Запустить", use_container_width=True):
            # Run editor buffer as a temporary script so user can test
            # without forcing file save first.
            tmp_path = ""
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix="_practice_run.py",
                    encoding="utf-8",
                    delete=False,
                ) as tmp:
                    tmp.write(edited)
                    tmp_path = tmp.name

                run = subprocess.run(
                    [sys.executable, tmp_path],
                    capture_output=True,
                    text=True,
                    cwd=str(settings.workspace_root),
                    timeout=30,
                )
                st.caption(f"Код завершился с exit code: {run.returncode}")
                if run.stdout:
                    st.code(run.stdout, language="text")
                if run.stderr:
                    st.code(run.stderr, language="text")
                if not run.stdout and not run.stderr:
                    st.info("Выполнено без вывода.")
            except subprocess.TimeoutExpired:
                st.error("Выполнение прервано: превышен лимит 30 секунд.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Ошибка запуска: {exc}")
            finally:
                if tmp_path:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass


def _render_verify_tab() -> None:
    assistant = get_assistant()
    last_text = st.session_state.get("last_assistant_text", "")

    if not last_text:
        st.info("Здесь появится результат проверки факта из последнего ответа.")
        return

    st.caption("**Проверяем последний ответ ассистента через веб-поиск + LLM critique:**")

    with st.expander("Текст для проверки", expanded=False):
        # Show only first 600 chars to avoid clutter
        st.markdown(last_text[:600] + ("..." if len(last_text) > 600 else ""))

    if st.button("🔍 Verify — запустить проверку", type="primary", use_container_width=True):
        with st.spinner("Ищу в интернете и проверяю факты..."):
            try:
                result = run_async(assistant.verify_claim(last_text))
                st.session_state.verify_result = result
            except Exception as exc:  # noqa: BLE001
                st.session_state.verify_result = f"❌ Ошибка проверки: {exc}"
        st.rerun()

    verify_result = st.session_state.get("verify_result")
    if verify_result:
        st.divider()
        st.markdown("**Результат fact-check:**")
        if "НЕТОЧНЫЙ" in verify_result.upper():
            st.error(verify_result)
        elif "ТОЧНЫЙ" in verify_result.upper():
            st.success(verify_result)
        else:
            st.warning(verify_result)


def render_right_panel() -> None:
    """Entry point: renders the right tabbed panel."""
    tab_rag, tab_code, tab_verify = st.tabs(["📚 RAG Sources", "💻 Code", "🔍 Verify"])

    with tab_rag:
        _render_rag_tab()

    with tab_code:
        _render_code_tab()

    with tab_verify:
        _render_verify_tab()
