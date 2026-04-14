"""
Streamlit session state management and async-to-sync stream bridge.

All st.session_state keys are initialised here once per page load.
The singleton MLAssistant is cached via @st.cache_resource so it
survives Streamlit reruns without re-connecting to LM Studio.
"""
from __future__ import annotations

import asyncio
import json
import queue
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import streamlit as st

from assistant.core.assistant import MLAssistant
from assistant.config import settings


_CHAT_DRAFT_PATH = settings.workspace_root / ".streamlit_chat_draft.json"


@st.cache_resource
def get_assistant() -> MLAssistant:
    """Create (or return cached) MLAssistant singleton."""
    return MLAssistant()


def initialize_session_state() -> None:
    """Ensure all required session_state keys exist with default values."""
    restored_messages = load_chat_draft()
    defaults: dict[str, Any] = {
        # Chat history: list of {role, content, confidence, sources}
        "messages": restored_messages,
        # RAG sources from the last assistant response
        "rag_sources": [],
        # Parsed confidence from the last assistant response
        "last_confidence": None,
        # Verify-tab state
        "verify_result": None,
        "verify_in_progress": False,
        # The last assistant message text (for verify)
        "last_assistant_text": "",
        # Interview timer
        "timer_start": None,
        "timer_active": False,
        # practice.py editor state
        "code_editor_content": None,
        "code_saved": False,
        "code_editor_nonce": 0,
        "code_editor_saved_hash": None,
        # voice input dedupe / reset
        "voice_audio_nonce": 0,
        "voice_last_signature": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_chat_draft() -> list[dict[str, Any]]:
    """Load persisted chat draft from local workspace file."""
    try:
        raw = _CHAT_DRAFT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except OSError:
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    validated: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if not isinstance(role, str) or not isinstance(content, str):
            continue
        row: dict[str, Any] = {"role": role, "content": content}
        confidence = item.get("confidence")
        if isinstance(confidence, dict):
            row["confidence"] = confidence
        validated.append(row)
    return validated


def save_chat_draft(messages: list[dict[str, Any]]) -> None:
    """Persist chat draft to disk so browser refresh does not lose conversation."""
    serializable: list[dict[str, Any]] = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = msg.get("content")
        if not isinstance(role, str) or not isinstance(content, str):
            continue
        row: dict[str, Any] = {"role": role, "content": content}
        confidence = msg.get("confidence")
        if isinstance(confidence, dict):
            row["confidence"] = confidence
        serializable.append(row)

    try:
        _CHAT_DRAFT_PATH.write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
    except OSError:
        # Non-fatal: UI should still work without draft persistence.
        return


def sync_stream(assistant: MLAssistant, user_input: str) -> Iterator[str]:
    """
    Run assistant.stream_chat() (async generator) in a background thread
    and yield tokens synchronously so Streamlit's st.write_stream() can consume them.

    Pattern: Queue + Thread — avoids nest_asyncio which is unreliable in Streamlit.
    """
    token_queue: queue.Queue[str | None] = queue.Queue()

    def _worker() -> None:
        async def _consume() -> None:
            try:
                async for token in assistant.stream_chat(user_input):
                    token_queue.put(token)
            except Exception as exc:  # noqa: BLE001
                token_queue.put(f"\n\n❌ Ошибка генерации: {exc}")
            finally:
                token_queue.put(None)  # sentinel — stream ended

        asyncio.run(_consume())

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

    while True:
        token = token_queue.get()
        if token is None:
            break
        yield token


def run_async(coro: Any) -> Any:
    """Run a coroutine synchronously from Streamlit's sync context."""
    return asyncio.run(coro)
